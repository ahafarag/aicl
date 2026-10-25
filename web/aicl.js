// Port of the model-free parts of aicl (src/aicl/text.py, metrics.py, phrases.py).
// Must stay numerically identical to the Python package: web/test/parity.mjs checks it.

export const WORD_RE = /[\p{L}\p{N}]+(?:['’\-][\p{L}\p{N}]+)*/gu;

const CODE_FENCE = /^\s*(```|~~~)[\s\S]*?^\s*\1[^\n]*$/gm;
const INLINE_CODE = /`[^`\n]*`/g;
const LINK = /!?\[([^\]]*)\]\([^)]*\)/g;
const EMPHASIS = /(\*\*|__|\*|_)(?=\S)(.+?)(?<=\S)\1/g;
const HEADING = /^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$/;
const LIST_ITEM = /^\s*(?:[-*+]|\d+[.)])\s+/;
// Python: ([.!?…]+["'”’)\]]*)\s+(?=["'“‘(\[]?[^\W_a-z])
const BOUNDARY = /([.!?…]+["'”’)\]]*)\s+(?=["'“‘(\[]?(?![_a-z])[\p{L}\p{N}])/gu;

const ABBREVIATIONS = new Set([
  "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "e.g", "i.e",
  "fig", "no", "vol", "approx", "inc", "ltd", "co", "cf", "al", "jan", "feb",
  "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
]);

export const words = (text) => (text.match(WORD_RE) || []).map((w) => w.toLowerCase());
export const wordCount = (text) => (text.match(WORD_RE) || []).length;

function clean(text) {
  return text
    .replace(CODE_FENCE, "")
    .replace(INLINE_CODE, "")
    .replace(LINK, "$1")
    .replace(EMPHASIS, "$2")
    .replaceAll("\r\n", "\n");
}

export function parse(text) {
  const sections = [{ title: null, paragraphs: [] }];
  const buffer = [];
  const flush = () => {
    if (buffer.length) {
      const para = buffer.map((l) => l.trim()).join(" ");
      if (wordCount(para)) sections.at(-1).paragraphs.push(para);
      buffer.length = 0;
    }
  };
  for (const line of clean(text).split("\n")) {
    const heading = line.match(HEADING);
    if (heading) {
      flush();
      sections.push({ title: heading[1], paragraphs: [] });
    } else if (!line.trim()) {
      flush();
    } else if (LIST_ITEM.test(line)) {
      flush();
      buffer.push(line.replace(LIST_ITEM, ""));
    } else {
      buffer.push(line);
    }
  }
  flush();
  return sections.filter((s) => s.paragraphs.length);
}

export function splitSentences(paragraph) {
  const sentences = [];
  let start = 0;
  for (const m of paragraph.matchAll(BOUNDARY)) {
    const punctStart = m.index;
    if (m[1].startsWith(".")) {
      const last = paragraph.slice(start, punctStart).match(/(\S+)$/);
      const token = last ? last[1].toLowerCase().replace(/^[(\["'“‘]+/, "") : "";
      if (ABBREVIATIONS.has(token) || (token.length === 1 && /\p{L}/u.test(token))) continue;
    }
    sentences.push(paragraph.slice(start, punctStart + m[1].length).trim());
    start = m.index + m[0].length;
  }
  sentences.push(paragraph.slice(start).trim());
  return sentences.filter((s) => wordCount(s));
}

export function percentile(sorted, q) {
  if (!sorted.length) return NaN;
  const pos = (sorted.length - 1) * q;
  const lo = Math.floor(pos), hi = Math.ceil(pos);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

export function describe(xs) {
  if (!xs.length) return { n: 0 };
  const mean = xs.reduce((a, b) => a + b, 0) / xs.length;
  const sd = Math.sqrt(xs.reduce((a, x) => a + (x - mean) ** 2, 0) / xs.length);
  return { n: xs.length, mean, sd, cv: mean ? sd / mean : NaN };
}

function mtldPass(tokens, threshold) {
  let factors = 0, count = 0, types = new Set();
  for (const tok of tokens) {
    count += 1;
    types.add(tok);
    if (types.size / count <= threshold) {
      factors += 1;
      types = new Set();
      count = 0;
    }
  }
  if (count) factors += (1 - types.size / count) / (1 - threshold);
  return factors ? tokens.length / factors : NaN;
}

export function mtld(tokens, threshold = 0.72) {
  if (!tokens.length) return NaN;
  return (mtldPass(tokens, threshold) + mtldPass([...tokens].reverse(), threshold)) / 2;
}

// Same entries as src/aicl/phrases.py.
const STOCK_PHRASES = {
  vocabulary: [
    "delv(?:e|es|ed|ing)", "tapestr(?:y|ies)", "testament to", "realm(?:s)?", "multifaceted",
    "intricac(?:y|ies)", "intricate", "pivotal", "underscor(?:e|es|ed|ing)", "showcas(?:e|es|ed|ing)",
    "seamless(?:ly)?", "ever-evolving", "meticulous(?:ly)?", "bustling", "vibrant",
    "embark(?:s|ed|ing)? on", "foster(?:s|ed|ing)?", "harness(?:es|ed|ing)? the power",
    "unlock(?:s|ed|ing)? the (?:full )?potential",
    "navigat(?:e|es|ed|ing) the (?:complexities|landscape|challenges)",
    "(?:digital|evolving|ever-changing|complex) landscape", "game[- ]changer", "paradigm shift",
  ],
  framing: [
    "in today's (?:fast-paced|digital|modern|ever-changing) (?:world|age|landscape)",
    "it(?:'s| is) (?:important|worth|crucial) to (?:note|remember|mention|consider)",
    "it(?:'s| is) not (?:just|only|merely) (?:about )?\\w+[^.]{0,40}?(?:it(?:'s| is)|but)",
    "plays? a (?:crucial|pivotal|vital|key|significant) role",
    "(?:a|an) (?:rich|complex|diverse) (?:tapestry|array|mosaic)",
    "whether you(?:'re| are) an? \\w+ or an? \\w+", "at the end of the day", "when it comes to",
  ],
  transitions: [
    "furthermore", "moreover", "additionally", "in conclusion", "in summary", "ultimately",
    "overall", "that being said",
  ],
};

export function stockPhraseHits(text) {
  const lowered = text.toLowerCase().replaceAll("’", "'");
  const hits = {};
  for (const [category, patterns] of Object.entries(STOCK_PHRASES)) {
    const found = {};
    for (const p of patterns) {
      for (const m of lowered.matchAll(new RegExp(`\\b${p}\\b`, "g"))) found[m[0]] = (found[m[0]] || 0) + 1;
    }
    hits[category] = found;
  }
  return hits;
}

/** The subset of aicl.metrics.analyze() the web app needs. */
export function analyze(text) {
  const sections = parse(text);
  const paragraphs = sections.flatMap((s) => s.paragraphs);
  const sentences = paragraphs.flatMap(splitSentences);
  const body = sections.map((s) => s.paragraphs.join("\n\n")).join("\n\n");
  const tokens = words(body);
  const hits = stockPhraseHits(body);
  const phraseTotal = Object.values(hits).reduce((a, c) => a + Object.values(c).reduce((x, y) => x + y, 0), 0);
  return {
    counts: { words: tokens.length, sentences: sentences.length, paragraphs: paragraphs.length },
    sentence_length: describe(sentences.map(wordCount)),
    lexical: { mtld: mtld(tokens) },
    stock_phrases: {
      per_1k_words: tokens.length ? (1000 * phraseTotal) / tokens.length : NaN,
      by_category: hits,
    },
  };
}
