"""Model-free stylometric measures. Pure standard library.

Definitions, references and caveats for each measure are in
docs/measurement_model.md. None of these numbers is a test of authorship.
"""

from __future__ import annotations

import math
import random
import re
from collections import Counter

from . import __version__
from .phrases import STOCK_PHRASES
from .text import body_text, parse, split_sentences, word_count, words


def percentile(sorted_xs: list[float], q: float) -> float:
    """Linear-interpolated percentile of an already sorted list, q in [0, 1]."""
    if not sorted_xs:
        return math.nan
    pos = (len(sorted_xs) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (pos - lo)


def _mean_sd(xs: list[float]) -> tuple[float, float]:
    mean = sum(xs) / len(xs)
    return mean, math.sqrt(sum((x - mean) ** 2 for x in xs) / len(xs))


def describe(xs: list[float]) -> dict:
    """Distribution summary. SD is the population SD; CV = SD / mean."""
    if not xs:
        return {"n": 0}
    s = sorted(xs)
    mean, sd = _mean_sd(xs)
    return {
        "n": len(xs),
        "mean": mean,
        "sd": sd,
        "cv": sd / mean if mean else math.nan,
        "min": s[0],
        "p10": percentile(s, 0.10),
        "median": percentile(s, 0.50),
        "p90": percentile(s, 0.90),
        "max": s[-1],
    }


def bootstrap_cv_ci(
    xs: list[float], resamples: int = 2000, alpha: float = 0.05, seed: int = 0
) -> tuple[float, float] | None:
    """Percentile-bootstrap confidence interval for the coefficient of variation."""
    if len(xs) < 10:
        return None
    rng = random.Random(seed)
    cvs = []
    for _ in range(resamples):
        sample = rng.choices(xs, k=len(xs))
        mean, sd = _mean_sd(sample)
        cvs.append(sd / mean if mean else math.nan)
    cvs.sort()
    return percentile(cvs, alpha / 2), percentile(cvs, 1 - alpha / 2)


def mattr(tokens: list[str], window: int = 50) -> float:
    """Moving-average type-token ratio (Covington & McFall, 2010)."""
    if not tokens:
        return math.nan
    if len(tokens) <= window:
        return len(set(tokens)) / len(tokens)
    counts = Counter(tokens[:window])
    total = len(counts)
    for i in range(window, len(tokens)):
        out, inc = tokens[i - window], tokens[i]
        counts[out] -= 1
        if counts[out] == 0:
            del counts[out]
        counts[inc] += 1
        total += len(counts)
    return total / window / (len(tokens) - window + 1)


def _mtld_pass(tokens: list[str], threshold: float) -> float:
    factors = 0.0
    types: set[str] = set()
    count = 0
    for tok in tokens:
        count += 1
        types.add(tok)
        if len(types) / count <= threshold:
            factors += 1
            types, count = set(), 0
    if count:
        factors += (1 - len(types) / count) / (1 - threshold)
    return len(tokens) / factors if factors else math.nan


def mtld(tokens: list[str], threshold: float = 0.72) -> float:
    """Measure of textual lexical diversity (McCarthy & Jarvis, 2010).

    Mean of a forward and a backward pass. Unstable below ~100 tokens.
    """
    if not tokens:
        return math.nan
    return (_mtld_pass(tokens, threshold) + _mtld_pass(tokens[::-1], threshold)) / 2


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    return list(zip(*(tokens[i:] for i in range(n))))


def distinct_n(tokens: list[str], n: int) -> float:
    """Unique n-grams / total n-grams. Lower means more repetition."""
    grams = ngrams(tokens, n)
    return len(set(grams)) / len(grams) if grams else math.nan


def stock_phrase_hits(text: str) -> dict[str, Counter]:
    lowered = text.lower().replace("’", "'")
    hits = {}
    for category, patterns in STOCK_PHRASES.items():
        found: Counter = Counter()
        for pattern in patterns:
            for m in re.finditer(rf"\b{pattern}\b", lowered):
                found[m.group(0)] += 1
        hits[category] = found
    return hits


_PUNCTUATION = {
    "em_dash": re.compile(r"—|\s--\s"),
    "semicolon": re.compile(r";"),
    "colon": re.compile(r":(?!//)"),
    "question": re.compile(r"\?"),
    "exclamation": re.compile(r"!"),
    "parenthesis": re.compile(r"\("),
}


def analyze(text: str) -> dict:
    """Compute all model-free measures for one document."""
    sections = parse(text)
    paragraphs = [p for s in sections for p in s.paragraphs]
    sentences = [sent for p in paragraphs for sent in split_sentences(p)]
    body = body_text(sections)
    tokens = words(body)
    n_words = len(tokens)
    per_k = (lambda c: 1000 * c / n_words) if n_words else (lambda c: math.nan)

    sentence_lengths = [word_count(s) for s in sentences]
    openers = [tuple(words(s)[:2]) for s in sentences]
    phrase_hits = stock_phrase_hits(body)
    phrase_total = sum(sum(c.values()) for c in phrase_hits.values())

    repeated_trigrams = [
        {"ngram": " ".join(g), "count": c}
        for g, c in Counter(ngrams(tokens, 3)).most_common(10)
        if c > 1
    ]

    result = {
        "aicl_version": __version__,
        "counts": {
            "words": n_words,
            "sentences": len(sentences),
            "paragraphs": len(paragraphs),
            "sections": len(sections),
        },
        "sentence_length": describe(sentence_lengths),
        "sentence_length_cv_ci95": bootstrap_cv_ci(sentence_lengths),
        "paragraph_length": describe([word_count(p) for p in paragraphs]),
        "section_length": (
            describe([word_count(s.text) for s in sections]) if len(sections) > 1 else None
        ),
        "lexical": {
            "ttr": len(set(tokens)) / n_words if n_words else math.nan,
            "mattr_50": mattr(tokens),
            "mtld": mtld(tokens),
        },
        "repetition": {
            "distinct_2": distinct_n(tokens, 2),
            "distinct_3": distinct_n(tokens, 3),
            "opener_diversity": len(set(openers)) / len(openers) if openers else math.nan,
            "top_repeated_trigrams": repeated_trigrams,
        },
        "stock_phrases": {
            "per_1k_words": per_k(phrase_total),
            "by_category": {k: dict(v.most_common()) for k, v in phrase_hits.items()},
        },
        "punctuation_per_1k_words": {
            name: per_k(len(rx.findall(body))) for name, rx in _PUNCTUATION.items()
        },
        "warnings": _warnings(n_words, len(sentences)),
    }
    return result


def _warnings(n_words: int, n_sentences: int) -> list[str]:
    out = []
    if n_words < 100:
        out.append("Fewer than 100 words: lexical diversity (MTLD) is unreliable.")
    if n_sentences < 10:
        out.append("Fewer than 10 sentences: sentence-length spread is unreliable; no CI reported.")
    return out


__all__ = ["analyze", "describe", "mattr", "mtld", "distinct_n"]
