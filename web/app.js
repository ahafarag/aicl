import { analyze, WORD_RE } from "./aicl.js";
import { ACCEPT, extractText } from "./extract.js";

const REPO = "https://github.com/ahafarag/aicl";
const MIN_WORDS = 40, MAX_WORDS = 600;
const COMPARE = [["toefl", "TOEFL essays"], ["us8", "US 8th-grade"], ["gpt", "GPT-3.5"]];
const EXAMPLES = [
  ["examples/1_toefl_essay.txt", "Real TOEFL essay by a human", "Flagged by all 7 commercial detectors in 2023"],
  ["examples/2_chatbot_style.txt", "Chatbot-style draft", "AI-written"],
  ["examples/3_edited.txt", "The same draft, rewritten", "Also AI-written"],
];
const SIGNALS = [
  ["perplexity", "Perplexity", (s, lm) => lm.perplexity, (v) => v.toFixed(1),
    "How surprised a language model is by your words. Lower means more predictable. Simple, common vocabulary lowers it, which is why detectors misread many non-native writers."],
  ["top10_share", "Top-10 word share", (s, lm) => lm.top10_share, (v) => `${(100 * v).toFixed(0)}%`,
    "Share of words that were among the model's 10 most likely guesses."],
  ["binoculars", "Binoculars score", (s, lm) => lm.binoculars, (v) => v.toFixed(3),
    "Perplexity compared with what a model would expect from itself. Lower looks more machine-like."],
  ["sentence_cv", "Sentence-length variation", (s) => s.sentence_length.cv, (v) => v.toFixed(2),
    "How much sentence lengths vary (standard deviation / mean). Older AI text tends to be uniform."],
  ["stock_per_1k", "Stock phrases / 1k words", (s) => s.stock_phrases.per_1k_words, (v) => v.toFixed(1),
    "Phrases common in chatbot output ('delve', 'it is important to note'). Plenty of people use them too."],
  ["mtld", "Vocabulary diversity (MTLD)", (s) => s.lexical.mtld, (v) => v.toFixed(0),
    "How long the text runs before words start repeating. Higher means more varied vocabulary."],
];
const GLTR = [[10, "g1", "top 10"], [100, "g2", "top 100"], [1000, "g3", "top 1,000"], [Infinity, "g4", "rarer"]];

const $ = (id) => document.getElementById(id);
const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const pct = (x) => `${Math.round(100 * x)}%`;

const ref = await (await fetch("reference.json")).json();
const T = ref.thresholds_5pct_fpr;

function percentileRank(value, qs, levels) {
  if (value <= qs[0]) return 0;
  if (value >= qs.at(-1)) return 1;
  for (let i = 1; i < qs.length; i++) {
    if (value <= qs[i]) {
      const frac = qs[i] > qs[i - 1] ? (value - qs[i - 1]) / (qs[i] - qs[i - 1]) : 0.5;
      return levels[i - 1] + frac * (levels[i] - levels[i - 1]);
    }
  }
  return 1;
}
const rank = (signal, group, value) => percentileRank(value, ref.groups[group].signals[signal], ref.quantiles);

// --- model worker ---
const worker = new Worker(new URL("./worker.js", import.meta.url), { type: "module" });
const pending = new Map();
const downloads = new Map();
let nextId = 0;
worker.onmessage = ({ data }) => {
  if (data.type === "progress") {
    downloads.set(data.file, [data.loaded, data.total]);
    let loaded = 0, total = 0;
    for (const [l, t] of downloads.values()) { loaded += l; total += t; }
    setStatus(`Downloading models (once, then cached): ${(loaded / 1e6).toFixed(0)} / ${(total / 1e6).toFixed(0)} MB`, loaded / total);
  } else if (data.type === "ready") {
    setStatus("Models ready. Analysing…");
  } else if (pending.has(data.id)) {
    const { resolve, reject } = pending.get(data.id);
    pending.delete(data.id);
    data.type === "result" ? resolve(data.result) : reject(new Error(data.message));
  }
};
const scoreText = (text) => new Promise((resolve, reject) => {
  const id = nextId++;
  pending.set(id, { resolve, reject });
  worker.postMessage({ type: "score", id, text });
});

function setStatus(msg, fraction) {
  $("status").hidden = !msg;
  $("status-text").textContent = msg ?? "";
  $("bar").hidden = fraction === undefined;
  if (fraction !== undefined) $("bar").value = fraction;
}

function truncate(text) {
  const matches = [...text.matchAll(WORD_RE)];
  return matches.length <= MAX_WORDS ? [text, false] : [text.slice(0, matches[MAX_WORDS - 1].index + matches[MAX_WORDS - 1][0].length), true];
}

function heatmap(tokens) {
  const legend = GLTR.map(([, cls, label]) => `<span class="${cls}">${label}</span>`).join(" ");
  const spans = tokens.map((t) => {
    const cls = GLTR.find(([limit]) => t.rank <= limit)[1];
    return `<span class="${cls}" title="rank ${t.rank}, ${t.surprisal_bits.toFixed(1)} bits">${esc(t.text).replaceAll("\n", "<br>")}</span>`;
  }).join("");
  return `<h2>Word by word</h2><p class="legend">Colour = how highly gpt2 ranked each token before seeing it: ${legend}</p><div class="heat">${spans}</div>`;
}

function render(style, lm, nWords, truncated) {
  const verdicts = [
    ["Binoculars", lm.binoculars.toFixed(3), lm.binoculars < -T.binoculars, `below ${(-T.binoculars).toFixed(3)}`],
    ["Perplexity", lm.perplexity.toFixed(1), lm.perplexity < -T.perplexity, `below ${(-T.perplexity).toFixed(1)}`],
    ["GLTR top-10 share", `${(100 * lm.top10_share).toFixed(1)}%`, lm.top10_share > T["gltr-top10"], `above ${(100 * T["gltr-top10"]).toFixed(1)}%`],
  ];
  const flagged = verdicts.filter((v) => v[2]).length;
  const rows = [], meanings = [];
  for (const [key, label, get, fmt, meaning] of SIGNALS) {
    const v = get(style, lm);
    if (v === undefined || v === null || Number.isNaN(v)) continue;
    rows.push(`<tr><td>${label}</td><td class="num">${fmt(v)}</td>${COMPARE.map(([g]) => `<td class="num">${pct(rank(key, g, v))}</td>`).join("")}</tr>`);
    meanings.push(`<li><b>${label}:</b> ${meaning}</li>`);
  }
  const med = (g) => ref.groups[g].signals.perplexity[10].toFixed(1);
  $("result").innerHTML = `
    <h2 class="verdict ${flagged ? "warn" : "ok"}">${flagged} of 3 open detectors would flag this text</h2>
    ${truncated ? `<p class="note">Only the first ${MAX_WORDS} words were analysed.</p>` : ""}
    <p>Each detector was tuned to wrongly flag at most 5% of a mixed pool of human essays. At those settings it
    still flagged <b>17–30% of TOEFL essays by non-native writers</b>
    (<a href="${REPO}/blob/master/reports/liang/report.md">report card</a>).</p>
    <div class="scroll"><table><thead><tr><th>Detector</th><th class="num">Your score</th><th>Flags when</th><th>Flagged?</th></tr></thead>
    <tbody>${verdicts.map(([n, s, f, r]) => `<tr><td>${n}</td><td class="num">${s}</td><td>${r}</td><td>${f ? "<b>yes</b>" : "no"}</td></tr>`).join("")}</tbody></table></div>
    <h2>Where your text sits</h2>
    <p>Share of each reference group with a <b>lower</b> value than your text:</p>
    <div class="scroll"><table><thead><tr><th>Signal</th><th class="num">Your text</th>${COMPARE.map(([, l]) => `<th class="num">${l}</th>`).join("")}</tr></thead>
    <tbody>${rows.join("")}</tbody></table></div>
    <ul class="meanings">${meanings.join("")}</ul>
    ${heatmap(lm.tokens)}
    <h2>Why careful human writing gets flagged</h2>
    <p>Median perplexity in the reference essays: <b>TOEFL ${med("toefl")}</b>, US 8th-grade ${med("us8")}, GPT-3.5 ${med("gpt")}.
    Writers who use common words and standard phrasing look predictable, and predictable is what most detectors call AI.</p>
    <h2>What this is not</h2>
    <ul>
      <li><b>Not proof of authorship, in either direction.</b> No measure here can establish who wrote a text.</li>
      <li>The detectors are small open models (gpt2 / distilgpt2), not the commercial products. The reference essays are from 2023.</li>
      ${nWords < 150 ? `<li>Short text (${nWords} words): treat every number as rough.</li>` : ""}
    </ul>`;
  $("result").hidden = false;
}

async function run() {
  const raw = $("text").value.trim();
  const nWords = (raw.match(WORD_RE) || []).length;
  if (nWords < MIN_WORDS) {
    setStatus(`Please paste at least ${MIN_WORDS} words. Short texts give unreliable results.`);
    return;
  }
  const [text, truncated] = truncate(raw);
  $("go").disabled = true;
  $("result").hidden = true;
  setStatus("Loading models…");
  try {
    const lm = await scoreText(text);
    render(analyze(text), lm, Math.min(nWords, MAX_WORDS), truncated);
    setStatus(null);
    $("result").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) {
    setStatus(`Something went wrong: ${e.message}`);
  } finally {
    $("go").disabled = false;
  }
}

$("go").addEventListener("click", run);

const FILE_HELP = $("file-note").textContent;
async function loadFile(file) {
  const note = $("file-note");
  note.classList.remove("error");
  note.textContent = `Reading ${file.name}…`;
  try {
    const { text, kind } = await extractText(file);
    $("text").value = text;
    const n = (text.match(WORD_RE) || []).length;
    note.textContent = `Loaded ${n.toLocaleString()} words from ${file.name} (${kind}). Check the text above, then press Analyse.` +
      (n > MAX_WORDS ? ` Only the first ${MAX_WORDS} words will be analysed.` : "");
  } catch (e) {
    note.classList.add("error");
    note.textContent = `Couldn't read ${file.name}: ${e.message}`;
  }
}
$("file").accept = ACCEPT;
$("file").addEventListener("change", (e) => {
  if (e.target.files[0]) loadFile(e.target.files[0]);
  e.target.value = "";
});
const box = $("text");
box.addEventListener("dragover", (e) => {
  if (e.dataTransfer.types.includes("Files")) { e.preventDefault(); box.classList.add("dragging"); }
});
box.addEventListener("dragleave", () => box.classList.remove("dragging"));
box.addEventListener("drop", (e) => {
  box.classList.remove("dragging");
  if (e.dataTransfer.files[0]) { e.preventDefault(); loadFile(e.dataTransfer.files[0]); }
});
box.addEventListener("input", () => {
  if ($("file-note").textContent !== FILE_HELP) { $("file-note").textContent = FILE_HELP; $("file-note").classList.remove("error"); }
});
for (const [path, label, sub] of EXAMPLES) {
  const b = document.createElement("button");
  b.className = "example";
  b.innerHTML = `${esc(label)}<small>${esc(sub)}</small>`;
  b.addEventListener("click", async () => { $("text").value = (await (await fetch(path)).text()).trim(); });
  $("examples").append(b);
}
