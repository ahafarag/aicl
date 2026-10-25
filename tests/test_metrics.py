import math

import pytest

from aicl.metrics import analyze, bootstrap_cv_ci, describe, distinct_n, mattr, mtld


def test_describe_uses_population_sd():
    d = describe([2, 4, 4, 4, 5, 5, 7, 9])
    assert d["mean"] == 5
    assert d["sd"] == 2
    assert d["cv"] == pytest.approx(0.4)
    assert d["median"] == 4.5


def test_mattr_matches_ttr_for_short_text_and_detects_repetition():
    assert mattr(["a", "b", "a"], window=50) == pytest.approx(2 / 3)
    assert mattr(["a", "b"] * 100, window=10) == pytest.approx(0.2)


def test_mtld_orders_repetitive_below_diverse():
    repetitive = ["the", "cat", "sat"] * 60
    diverse = [f"w{i}" for i in range(90)] + ["the", "cat"] * 45
    assert mtld(repetitive) < mtld(diverse)


def test_mtld_of_all_unique_tokens_is_undefined():
    assert math.isnan(mtld([f"w{i}" for i in range(20)]))


def test_distinct_n():
    assert distinct_n(["a", "b", "a", "b"], 2) == pytest.approx(2 / 3)


def test_bootstrap_ci_is_deterministic_and_brackets_estimate():
    xs = [5, 8, 12, 20, 3, 15, 9, 30, 7, 11, 14, 6]
    lo, hi = bootstrap_cv_ci(xs)
    assert (lo, hi) == bootstrap_cv_ci(xs)
    assert lo < describe(xs)["cv"] < hi
    assert bootstrap_cv_ci(xs[:5]) is None


def test_analyze_end_to_end():
    text = (
        "# One\n\nIt is important to note that we delve into the topic. "
        "Furthermore, the landscape is vibrant.\n\n"
        "# Two\n\nShort. This sentence is a fair bit longer than the one before it."
    )
    r = analyze(text)
    assert r["counts"] == {"words": 29, "sentences": 4, "paragraphs": 2, "sections": 2}
    assert r["sentence_length"]["min"] == 1
    hits = r["stock_phrases"]["by_category"]
    assert hits["vocabulary"] == {"delve": 1, "vibrant": 1}
    assert "it is important to note" in hits["framing"]
    assert hits["transitions"] == {"furthermore": 1}
    assert r["section_length"]["n"] == 2
    assert any("100 words" in w for w in r["warnings"])


def test_analyze_empty_text():
    r = analyze("")
    assert r["counts"]["words"] == 0
    assert r["sentence_length"] == {"n": 0}
