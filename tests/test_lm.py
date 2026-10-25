"""Language-model tests. Skipped unless torch/transformers are installed.

They download gpt2 and distilgpt2 from the Hugging Face Hub on first run.
"""

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")

from aicl import lm  # noqa: E402

TEXT = "The quick brown fox jumps over the lazy dog. " * 3


def test_lm_metrics_shapes_and_window_consistency():
    r = lm.lm_metrics(TEXT, return_tokens=True)
    assert r["tokens_scored"] == len(r["tokens"])
    assert r["perplexity"] > 1
    assert sum(r["rank_buckets"].values()) == pytest.approx(1)
    # Repeated text should become highly predictable.
    assert r["rank_buckets"]["top10"] > 0.5
    small = lm.lm_metrics(TEXT, window=8)
    assert small["tokens_scored"] < r["tokens_scored"]


def test_binoculars_same_model_is_self_consistent():
    r = lm.binoculars(TEXT, observer="gpt2", performer="gpt2")
    assert r["score"] > 0
    assert r["calibrated"] is False


def test_too_short():
    with pytest.raises(ValueError):
        lm.lm_metrics("Hi")
