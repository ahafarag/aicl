"""Language-model measures: perplexity, surprisal profile, rank buckets, Binoculars.

Optional: requires `pip install "ai-content-lab[lm]"` (torch + transformers).
Every number here depends on the reference model, its tokenizer and the
window size, so all three are reported alongside the results.
"""

from __future__ import annotations

import math
from functools import lru_cache

from .metrics import describe

LN2 = math.log(2)


def _require():
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            'Language-model metrics need torch and transformers: pip install "ai-content-lab[lm]"'
        ) from exc


@lru_cache(maxsize=4)
def _load(name: str, device: str):
    _require()
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(name)
    model = AutoModelForCausalLM.from_pretrained(name).to(device).eval()
    return tokenizer, model


def _windows(ids: list[int], size: int) -> list[list[int]]:
    """Non-overlapping windows; the first token of each window is context only."""
    return [ids[i : i + size] for i in range(0, len(ids), size) if len(ids[i : i + size]) > 1]


def _window_logits(model, window: list[int], device: str):
    import torch

    with torch.no_grad():
        ids = torch.tensor([window], device=device)
        return model(ids).logits[0, :-1].float(), ids[0, 1:]


def lm_metrics(
    text: str,
    model: str = "gpt2",
    window: int = 1024,
    device: str = "cpu",
    return_tokens: bool = False,
) -> dict:
    """Perplexity and per-token surprisal of `text` under a causal LM.

    Rank buckets follow GLTR (Gehrmann et al., 2019): the share of tokens that
    were the model's top-10, top-100, top-1000 or lower-ranked prediction.
    """
    import torch

    tokenizer, lm = _load(model, device)
    ids = tokenizer(text, add_special_tokens=False).input_ids
    window = min(window, getattr(lm.config, "n_positions", None) or getattr(lm.config, "max_position_embeddings", window))

    surprisal, ranks, entropy, pieces = [], [], [], []
    for w in _windows(ids, window):
        logits, targets = _window_logits(lm, w, device)
        logp = torch.log_softmax(logits, dim=-1)
        target_logp = logp.gather(1, targets[:, None]).squeeze(1)
        target_logit = logits.gather(1, targets[:, None])
        surprisal += (-target_logp / LN2).tolist()
        ranks += ((logits > target_logit).sum(dim=1) + 1).tolist()
        entropy += (-(logp.exp() * logp).sum(dim=-1) / LN2).tolist()
        if return_tokens:
            pieces += [tokenizer.decode([t]) for t in targets.tolist()]

    if not surprisal:
        raise ValueError("Text is too short to score: need at least two tokens.")

    n = len(ranks)
    result = {
        "model": model,
        "window": window,
        "tokens_scored": n,
        "perplexity": 2 ** (sum(surprisal) / n),
        "surprisal_bits": describe(surprisal),
        "entropy_bits_mean": sum(entropy) / n,
        "rank_buckets": {
            "top10": sum(r <= 10 for r in ranks) / n,
            "top100": sum(10 < r <= 100 for r in ranks) / n,
            "top1000": sum(100 < r <= 1000 for r in ranks) / n,
            "rest": sum(r > 1000 for r in ranks) / n,
        },
    }
    if return_tokens:
        result["tokens"] = [
            {"text": p, "surprisal_bits": s, "rank": r}
            for p, s, r in zip(pieces, surprisal, ranks)
        ]
    return result


def binoculars(
    text: str,
    observer: str = "gpt2",
    performer: str = "distilgpt2",
    window: int = 1024,
    device: str = "cpu",
) -> dict:
    """Binoculars score (Hans et al., 2024): log-perplexity / cross-perplexity.

    log PPL uses the performer's predictions; cross-perplexity is the
    cross-entropy of the observer's next-token distribution against the
    performer's, as in the reference implementation. Lower scores indicate
    text that is unsurprising relative to what a model would expect, which is
    typical of LLM output. Decision thresholds from the paper apply only to
    its Falcon-7B pair; any other pair must be calibrated on labeled data.
    """
    import torch

    obs_tok, obs_model = _load(observer, device)
    perf_tok, perf_model = _load(performer, device)
    if obs_tok.get_vocab() != perf_tok.get_vocab():
        raise ValueError("Binoculars needs an observer and performer that share a tokenizer.")

    ids = obs_tok(text, add_special_tokens=False).input_ids
    nll_sum, xent_sum, n = 0.0, 0.0, 0
    for w in _windows(ids, window):
        obs_logits, targets = _window_logits(obs_model, w, device)
        perf_logits, _ = _window_logits(perf_model, w, device)
        perf_logp = torch.log_softmax(perf_logits, dim=-1)
        nll_sum += -perf_logp.gather(1, targets[:, None]).sum().item()
        xent_sum += -(torch.softmax(obs_logits, dim=-1) * perf_logp).sum().item()
        n += len(targets)

    if not n:
        raise ValueError("Text is too short to score: need at least two tokens.")
    log_ppl, log_xppl = nll_sum / n, xent_sum / n
    return {
        "observer": observer,
        "performer": performer,
        "tokens_scored": n,
        "log_ppl": log_ppl,
        "log_x_ppl": log_xppl,
        "score": log_ppl / log_xppl,
        "calibrated": False,
    }
