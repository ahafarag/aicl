"""Detectors under evaluation. Every scorer returns higher = more machine-like.

Open detectors are computed locally. Scores recorded by third parties (e.g. the
2023 commercial detector outputs in Liang et al.) arrive on the records
themselves and are picked up automatically.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import Callable

from ..metrics import analyze
from .data import CACHE


@lru_cache(maxsize=None)
def _lm(text: str, model: str) -> dict:
    from ..lm import lm_metrics

    return lm_metrics(text, model=model)


def _binoculars(text: str) -> float:
    from ..lm import binoculars

    return -binoculars(text)["score"]


DETECTORS: dict[str, tuple[str, Callable[[str], float]]] = {
    "binoculars": ("Binoculars, gpt2/distilgpt2, uncalibrated", _binoculars),
    "perplexity": ("Low perplexity under gpt2", lambda t: -_lm(t, "gpt2")["perplexity"]),
    "gltr-top10": ("GLTR top-10 rank share under gpt2", lambda t: _lm(t, "gpt2")["rank_buckets"]["top10"]),
    "stock-phrases": ("Stock-phrase density (baseline)", lambda t: analyze(t)["stock_phrases"]["per_1k_words"]),
    "low-sentence-cv": ("Low sentence-length CV (baseline)",
                        lambda t: -(analyze(t)["sentence_length"].get("cv") or 0.0)),
}


class ScoreCache:
    """Per-detector JSONL cache keyed by text hash, so long runs can resume."""

    def __init__(self, detector: str):
        self.path = CACHE / "scores" / f"{detector}.jsonl"
        self.scores: dict[str, float] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                self.scores[row["h"]] = row["s"]

    @staticmethod
    def key(text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> float | None:
        return self.scores.get(self.key(text))

    def put(self, text: str, score: float) -> None:
        h = self.key(text)
        self.scores[h] = score
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"h": h, "s": score}) + "\n")


def score_all(name: str, texts: list[str], progress: Callable[[int, int], None] | None = None) -> list[float | None]:
    """Score texts with a built-in detector; None where the text cannot be scored."""
    _, fn = DETECTORS[name]
    cache = ScoreCache(name)
    out: list[float | None] = []
    for i, text in enumerate(texts):
        score = cache.get(text)
        if score is None:
            try:
                score = float(fn(text))
            except ValueError:
                score = None
            if score is not None:
                cache.put(text, score)
        out.append(score)
        if progress:
            progress(i + 1, len(texts))
    return out
