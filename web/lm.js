// Port of src/aicl/lm.py for transformers.js. Works in the browser and in Node.
// `tf` is the imported @huggingface/transformers module.

const LN2 = Math.log(2);

export async function loadModels(tf, { dtype = "fp32", device, progress } = {}) {
  const opts = { dtype, device, progress_callback: progress };
  const [tokenizer, observer, performer] = await Promise.all([
    tf.AutoTokenizer.from_pretrained("Xenova/gpt2"),
    tf.AutoModelForCausalLM.from_pretrained("Xenova/gpt2", opts),
    tf.AutoModelForCausalLM.from_pretrained("Xenova/distilgpt2", opts),
  ]);
  return { tf, tokenizer, observer, performer };
}

function windows(ids, size) {
  const out = [];
  for (let i = 0; i < ids.length; i += size) {
    const w = ids.slice(i, i + size);
    if (w.length > 1) out.push(w);
  }
  return out;
}

async function logits(tf, model, window) {
  const n = window.length;
  const input_ids = new tf.Tensor("int64", BigInt64Array.from(window, BigInt), [1, n]);
  const attention_mask = new tf.Tensor("int64", new BigInt64Array(n).fill(1n), [1, n]);
  const out = await model({ input_ids, attention_mask });
  const data = out.logits.data;
  const vocab = out.logits.dims[2];
  out.logits.dispose?.();
  return { data, vocab };
}

function logSumExp(data, offset, vocab) {
  let max = -Infinity;
  for (let v = 0; v < vocab; v++) if (data[offset + v] > max) max = data[offset + v];
  let sum = 0;
  for (let v = 0; v < vocab; v++) sum += Math.exp(data[offset + v] - max);
  return max + Math.log(sum);
}

/**
 * Perplexity, GLTR ranks and per-token surprisal under gpt2 (the observer), plus the
 * Binoculars score with distilgpt2 as performer, from one pass over each model.
 */
export async function score(models, text, { window = 1024 } = {}) {
  const { tf, tokenizer, observer, performer } = models;
  const ids = tokenizer.encode(text, { add_special_tokens: false });
  const size = Math.min(window, observer.config.n_positions ?? window);

  const tokens = [];
  let nllObs = 0, nllPerf = 0, xent = 0, n = 0;
  for (const w of windows(ids, size)) {
    const obs = await logits(tf, observer, w);
    const perf = await logits(tf, performer, w);
    const vocab = Math.min(obs.vocab, perf.vocab);
    for (let i = 0; i < w.length - 1; i++) {
      const target = w[i + 1];
      const oOff = i * obs.vocab, pOff = i * perf.vocab;
      const oLse = logSumExp(obs.data, oOff, obs.vocab);
      const pLse = logSumExp(perf.data, pOff, perf.vocab);
      const targetLogit = obs.data[oOff + target];
      let rank = 1, cross = 0;
      for (let v = 0; v < vocab; v++) {
        const o = obs.data[oOff + v];
        if (o > targetLogit) rank++;
        cross += Math.exp(o - oLse) * -(perf.data[pOff + v] - pLse);
      }
      const nll = oLse - targetLogit;
      nllObs += nll;
      nllPerf += pLse - perf.data[pOff + target];
      xent += cross;
      n++;
      tokens.push({ text: tokenizer.decode([target]), surprisal_bits: nll / LN2, rank });
    }
  }
  if (!n) throw new Error("Text is too short to score: need at least two tokens.");
  const top10 = tokens.filter((t) => t.rank <= 10).length / n;
  return {
    tokens_scored: n,
    perplexity: Math.exp(nllObs / n),
    top10_share: top10,
    binoculars: (nllPerf / n) / (xent / n),
    tokens,
  };
}
