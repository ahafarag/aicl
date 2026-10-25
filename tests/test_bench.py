import json

import pytest

from aicl.bench import stats
from aicl.bench.run import evaluate, markdown


def test_auroc_perfect_chance_and_ties():
    assert stats.auroc([0, 1, 2], [3, 4]) == 1.0
    assert stats.auroc([3, 4], [0, 1]) == 0.0
    assert stats.auroc([1, 1], [1, 1]) == 0.5
    # one of four pairs is tied, one is reversed
    assert stats.auroc([1, 3], [1, 4]) == pytest.approx(0.625)


def test_wilson_interval():
    lo, hi = stats.wilson(5, 10)
    assert lo == pytest.approx(0.2366, abs=1e-3)
    assert hi == pytest.approx(0.7634, abs=1e-3)
    assert stats.wilson(0, 20)[0] == 0.0


def test_threshold_respects_target_fpr():
    neg = list(range(100))
    t = stats.threshold_at_fpr(neg, 0.05)
    assert sum(s > t for s in neg) <= 5
    assert sum(s > t - 1 for s in neg) > 5


def _records():
    recs = []
    for i in range(40):
        recs.append({"id": f"h{i}", "text": f"h{i}", "label": 0, "group": "native" if i < 20 else "non-native",
                     "scores": {"Vendor": 0.1 if i < 20 else 0.9}})
    for i in range(20):
        recs.append({"id": f"m{i}", "text": f"m{i}", "label": 1, "group": "llm", "scores": {"Vendor": 0.95}})
    return recs


def test_evaluate_reports_group_false_positives():
    report = evaluate(_records(), detectors=[], target_fpr=0.05)
    vendor = report["detectors"]["Vendor"]
    assert vendor["vendor"]["native"]["rate"] == 0.0
    assert vendor["vendor"]["non-native"]["rate"] == 1.0
    assert vendor["vendor"]["llm"]["rate"] == 1.0
    assert report["counts"]["calibration_humans"] == 20
    md = markdown(report, "toy", ["synthetic"])
    assert "non-native | human → false positives" in md
    json.dumps(report)
