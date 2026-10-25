"""Build src/aicl/data/reference_liang.json: per-group quantiles of each signal.

Only aggregate quantiles are stored, never the texts. Reuses the benchmark's
score cache, so run `aicl bench liang` first to avoid rescoring.

    python scripts/build_reference.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from aicl import __version__
from aicl.bench import data
from aicl.bench.detectors import score_all
from aicl.metrics import analyze, percentile

GROUPS = {
    "TOEFL essays (non-native writers)": "toefl",
    "US 8th-grade essays": "us8",
    "US college admission essays": "college",
    "Stanford CS224N abstracts": "cs224n",
    "GPT-3.5 college essays": "gpt",
    "GPT-3.5 CS224N abstracts": "gpt",
    "GPT-3.5 college essays, literary prompt": "gpt_literary",
    "GPT-3.5 CS224N abstracts, literary prompt": "gpt_literary",
}
LABELS = {
    "toefl": "Human: TOEFL essays (non-native writers)",
    "us8": "Human: US 8th-grade essays",
    "college": "Human: US college admission essays",
    "cs224n": "Human: Stanford CS224N abstracts",
    "gpt": "GPT-3.5 essays and abstracts",
    "gpt_literary": "GPT-3.5, 'literary language' prompt",
}
QUANTILES = [i / 20 for i in range(21)]


def main() -> None:
    records = data.liang()
    texts = [r["text"] for r in records]
    # Cached benchmark scores are oriented "higher = more machine-like"; undo that here.
    signals = {
        "perplexity": [-s if s is not None else None for s in score_all("perplexity", texts)],
        "top10_share": score_all("gltr-top10", texts),
        "binoculars": [-s if s is not None else None for s in score_all("binoculars", texts)],
    }
    style = [analyze(t) for t in texts]
    signals["sentence_cv"] = [a["sentence_length"].get("cv") for a in style]
    signals["stock_per_1k"] = [a["stock_phrases"]["per_1k_words"] for a in style]
    signals["mtld"] = [a["lexical"]["mtld"] for a in style]

    out = {"aicl_version": __version__, "source": data.LIANG_CITATION, "quantiles": QUANTILES,
           "groups": {}}
    for key, label in LABELS.items():
        idx = [i for i, r in enumerate(records) if GROUPS[r["group"]] == key]
        entry = {"label": label, "n": len(idx), "signals": {}}
        for name, values in signals.items():
            vals = sorted(v for i in idx if (v := values[i]) is not None and not math.isnan(v))
            entry["signals"][name] = [percentile(vals, q) for q in QUANTILES]
        out["groups"][key] = entry

    report = json.loads(Path("reports/liang/report.json").read_text(encoding="utf-8"))
    out["thresholds_5pct_fpr"] = {
        name: report["detectors"][name]["calibrated_threshold"]
        for name in ("binoculars", "perplexity", "gltr-top10")
    }
    path = Path("src/aicl/data/reference_liang.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
