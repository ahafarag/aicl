"""Place a text's signals within reference distributions of human and GPT writing.

The reference file holds per-group quantiles computed by
scripts/build_reference.py from Liang et al. (2023); no texts are stored.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=1)
def load() -> dict:
    return json.loads(resources.files("aicl.data").joinpath("reference_liang.json").read_text("utf-8"))


def percentile_rank(value: float, quantiles: list[float], levels: list[float]) -> float:
    """Approximate share of a group scoring below `value`, interpolating between stored quantiles."""
    if value <= quantiles[0]:
        return 0.0
    if value >= quantiles[-1]:
        return 1.0
    for i in range(1, len(quantiles)):
        lo, hi = quantiles[i - 1], quantiles[i]
        if value <= hi:
            frac = (value - lo) / (hi - lo) if hi > lo else 0.5
            return levels[i - 1] + frac * (levels[i] - levels[i - 1])
    return 1.0


def ranks(signal: str, value: float) -> dict[str, float]:
    """Percentile rank of `value` for `signal` within every reference group."""
    ref = load()
    return {key: percentile_rank(value, g["signals"][signal], ref["quantiles"])
            for key, g in ref["groups"].items()}
