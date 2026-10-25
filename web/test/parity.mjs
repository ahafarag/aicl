// Checks the JS port against Python reference values in fixtures.json.
//   node web/test/parity.mjs            style measures only (fast)
//   node web/test/parity.mjs --lm q8    also language-model scores at the given dtype

import { readFileSync } from "node:fs";
import { analyze } from "../aicl.js";

// Python writes NaN for undefined values; JSON has no NaN, so map it to null.
const fixtures = JSON.parse(readFileSync(new URL("./fixtures.json", import.meta.url), "utf8").replace(/\bNaN\b/g, "null"));
const lmIdx = process.argv.indexOf("--lm");
const dtype = lmIdx > 0 ? process.argv[lmIdx + 1] : null;

let failures = 0;
const close = (a, b, tol) =>
  (a === null || Number.isNaN(a)) ? (b === null || Number.isNaN(b)) : Math.abs(a - b) <= tol * Math.max(1, Math.abs(b));

for (const [i, f] of fixtures.entries()) {
  const a = analyze(f.text);
  const got = { words: a.counts.words, sentences: a.counts.sentences, paragraphs: a.counts.paragraphs,
    sentence_cv: a.sentence_length.cv ?? null, stock_per_1k: a.stock_phrases.per_1k_words, mtld: a.lexical.mtld };
  for (const [k, v] of Object.entries(got)) {
    if (!close(v, f[k], 1e-9)) {
      failures++;
      console.log(`#${i} ${k}: js=${v} py=${f[k]}  ${JSON.stringify(f.text.slice(0, 60))}`);
    }
  }
}
console.log(`style: ${fixtures.length} texts, ${failures} mismatches`);

if (dtype) {
  const tf = await import("@huggingface/transformers");
  const { loadModels, score } = await import("../lm.js");
  const models = await loadModels(tf, { dtype });
  const rel = { perplexity: [], top10_share: [], binoculars: [] };
  for (const f of fixtures.filter((f) => f.perplexity !== undefined)) {
    const s = await score(models, f.text);
    for (const k of Object.keys(rel)) rel[k].push(Math.abs(s[k] - f[k]) / Math.abs(f[k]));
  }
  for (const [k, xs] of Object.entries(rel)) {
    xs.sort((a, b) => a - b);
    console.log(`${dtype} ${k}: median rel. error ${(100 * xs[xs.length >> 1]).toFixed(3)}%, max ${(100 * xs.at(-1)).toFixed(3)}%`);
  }
}
process.exit(failures ? 1 : 0);
