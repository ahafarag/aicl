"""Write web/test/fixtures.json: Python reference values for the JS parity test.

    python web/test/make_fixtures.py
"""

import json
import random
from pathlib import Path

from aicl.bench import data
from aicl.lm import binoculars, lm_metrics
from aicl.metrics import analyze

TRICKY = [
    "Dr. Smith met J. R. Jones at 5 p.m. on Monday. They talked, e.g. about rain. Fine!",
    'She asked, "Is it late?" He shrugged. "No." Then she left… Quickly.',
    "# Title\n\nIntro with **bold** and a [link](http://x.y) and `code`.\n\n- item one\n- item two\n\n"
    "```\nignored()\n```\n\nIt is important to note that we delve into a rich tapestry. Furthermore, ok.",
    "Don't over-think it — the state-of-the-art isn't 100% there; it’s close. Is it? Yes!",
]


def main() -> None:
    rng = random.Random(0)
    records = data.liang()
    by_group = {}
    for r in records:
        by_group.setdefault(r["group"], []).append(r["text"])
    texts = [t for g in sorted(by_group) for t in rng.sample(by_group[g], 5)]
    texts += [p.read_text(encoding="utf-8") for p in sorted(Path("web/examples").glob("*.txt"))]

    fixtures = []
    for t in TRICKY + texts:
        a = analyze(t)
        row = {"text": t, "words": a["counts"]["words"], "sentences": a["counts"]["sentences"],
               "paragraphs": a["counts"]["paragraphs"], "sentence_cv": a["sentence_length"].get("cv"),
               "stock_per_1k": a["stock_phrases"]["per_1k_words"], "mtld": a["lexical"]["mtld"]}
        if t not in TRICKY:
            lm = lm_metrics(t)
            row.update(perplexity=lm["perplexity"], top10_share=lm["rank_buckets"]["top10"],
                       binoculars=binoculars(t)["score"])
        fixtures.append(row)
    out = Path("web/test/fixtures.json")
    out.write_text(json.dumps(fixtures, indent=1, allow_nan=True), encoding="utf-8")
    print(f"Wrote {len(fixtures)} fixtures to {out}")


if __name__ == "__main__":
    main()
