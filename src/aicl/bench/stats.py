"""Evaluation statistics for detectors. Scores are oriented so higher = more machine-like."""

from __future__ import annotations

import math
import random


def auroc(neg: list[float], pos: list[float]) -> float:
    """Area under the ROC curve via the Mann-Whitney U statistic (ties count half)."""
    if not neg or not pos:
        return math.nan
    labelled = sorted([(s, 0) for s in neg] + [(s, 1) for s in pos])
    rank_sum, i = 0.0, 0
    while i < len(labelled):
        j = i
        while j < len(labelled) and labelled[j][0] == labelled[i][0]:
            j += 1
        mid_rank = (i + 1 + j) / 2
        rank_sum += mid_rank * sum(1 for k in range(i, j) if labelled[k][1] == 1)
        i = j
    u = rank_sum - len(pos) * (len(pos) + 1) / 2
    return u / (len(neg) * len(pos))


def bootstrap_auroc(
    neg: list[float], pos: list[float], resamples: int = 1000, seed: int = 0
) -> tuple[float, float] | None:
    """Percentile-bootstrap 95% CI, resampling each class independently."""
    if len(neg) < 5 or len(pos) < 5:
        return None
    rng = random.Random(seed)
    values = sorted(
        auroc(rng.choices(neg, k=len(neg)), rng.choices(pos, k=len(pos)))
        for _ in range(resamples)
    )
    return values[int(0.025 * resamples)], values[int(0.975 * resamples) - 1]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return math.nan, math.nan
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def threshold_at_fpr(neg: list[float], target_fpr: float) -> float:
    """Smallest threshold t such that at most target_fpr of `neg` satisfy score > t."""
    ordered = sorted(neg, reverse=True)
    k = min(int(math.floor(target_fpr * len(ordered))), len(ordered) - 1)
    return ordered[k]


def rate(scores: list[float], threshold: float) -> dict:
    """Share of scores flagged (score > threshold) with a Wilson 95% CI."""
    k = sum(s > threshold for s in scores)
    lo, hi = wilson(k, len(scores))
    return {"n": len(scores), "flagged": k, "rate": k / len(scores) if scores else math.nan,
            "ci95": [lo, hi]}
