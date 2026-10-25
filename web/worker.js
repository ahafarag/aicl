// Runs the language models off the main thread.
import * as tf from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.1";
import { loadModels, score } from "./lm.js";

tf.env.allowLocalModels = false;
let models = null;

async function load() {
  const progress = (p) => {
    if (p.status === "progress" && p.total) postMessage({ type: "progress", file: p.file, loaded: p.loaded, total: p.total });
  };
  // Measured against the Python scores in headless Chrome: WebAssembly + fp16 agrees within
  // 0.34%, but WebGPU + fp16 drifts up to 10%, enough to flip verdicts. So never use WebGPU
  // with fp16; fall back to fp32 (exact, twice the download) only if fp16 fails to load.
  const attempts = [{ device: "wasm", dtype: "fp16" }, { device: "wasm", dtype: "fp32" }];
  let lastError;
  for (const a of attempts) {
    try {
      const m = await loadModels(tf, { ...a, progress });
      await score(m, "A short warm-up sentence. Another one follows.");
      postMessage({ type: "ready", ...a });
      return m;
    } catch (e) {
      lastError = e;
    }
  }
  throw lastError;
}

self.onmessage = async ({ data }) => {
  try {
    models ??= await load();
    if (data.type === "score") postMessage({ type: "result", id: data.id, result: await score(models, data.text) });
  } catch (e) {
    postMessage({ type: "error", id: data.id, message: String(e?.message ?? e) });
  }
};
