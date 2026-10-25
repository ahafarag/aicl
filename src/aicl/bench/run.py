"""Run detectors over a labelled dataset and write a report card (Markdown + JSON).

Protocol (documented in docs/report_card.md):
1. Human texts in each group are split in half at random (fixed seed). One half
   from every group forms the calibration pool; everything else is evaluated.
2. For each detector, the threshold is set so that at most `target_fpr` of the
   calibration humans are flagged. This mirrors how a deployer would tune a
   detector on writing they trust.
3. On the evaluation split we report AUROC with a bootstrap CI, and the share of
   each group flagged at that threshold with a Wilson CI. For human groups this
   is the false-positive rate; for machine groups it is the detection rate.
4. Third-party scores in [0, 1] are additionally evaluated at the vendor's own
   0.5 cut-off on all records, since that is what their users saw.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import random
from collections import defaultdict
from pathlib import Path

from .. import __version__
from .detectors import DETECTORS, score_all
from .stats import auroc, bootstrap_auroc, rate, threshold_at_fpr


def _split(records: list[dict], seed: int) -> list[str]:
    rng = random.Random(seed)
    by_group: dict[str, list[int]] = defaultdict(list)
    for i, r in enumerate(records):
        if r["label"] == 0:
            by_group[r["group"]].append(i)
    splits = ["eval"] * len(records)
    for idx in by_group.values():
        rng.shuffle(idx)
        for i in idx[: len(idx) // 2]:
            splits[i] = "calib"
    return splits


def evaluate(
    records: list[dict],
    detectors: list[str],
    target_fpr: float = 0.05,
    seed: int = 0,
    vendor_threshold: float = 0.5,
    progress=None,
) -> dict:
    splits = _split(records, seed)
    vendor_names = sorted({k for r in records for k in (r.get("scores") or {})})
    groups = list(dict.fromkeys(r["group"] for r in sorted(records, key=lambda r: r["label"])))
    results = {}

    for name in detectors + vendor_names:
        if name in DETECTORS:
            scores = score_all(name, [r["text"] for r in records],
                               progress=(lambda i, n, name=name: progress(name, i, n)) if progress else None)
        else:
            scores = [(r.get("scores") or {}).get(name) for r in records]

        rows = [(r, s, sp) for r, s, sp in zip(records, scores, splits) if s is not None]
        calib_neg = [s for r, s, sp in rows if sp == "calib"]
        eval_rows = [(r, s) for r, s, sp in rows if sp == "eval"]
        neg = [s for r, s in eval_rows if r["label"] == 0]
        pos = [s for r, s in eval_rows if r["label"] == 1]
        threshold = threshold_at_fpr(calib_neg, target_fpr) if calib_neg else math.nan

        entry = {
            "description": DETECTORS[name][0] if name in DETECTORS else "Third-party score",
            "scored": len(rows),
            "skipped": len(records) - len(rows),
            "auroc": auroc(neg, pos),
            "auroc_ci95": bootstrap_auroc(neg, pos, seed=seed),
            "calibrated_threshold": threshold,
            "calibrated": {
                g: rate([s for r, s in eval_rows if r["group"] == g], threshold)
                for g in groups if any(r["group"] == g for r, _ in eval_rows)
            },
        }
        if name not in DETECTORS:
            entry["vendor_threshold"] = vendor_threshold
            entry["vendor"] = {
                g: rate([s for r, s, _ in rows if r["group"] == g], vendor_threshold)
                for g in groups if any(r["group"] == g for r, _, _ in rows)
            }
        results[name] = entry

    return {
        "aicl_version": __version__,
        "generated": dt.date.today().isoformat(),
        "seed": seed,
        "target_fpr": target_fpr,
        "counts": {
            "documents": len(records),
            "human": sum(r["label"] == 0 for r in records),
            "machine": sum(r["label"] == 1 for r in records),
            "calibration_humans": splits.count("calib"),
        },
        "groups": {g: {"label": next(r["label"] for r in records if r["group"] == g),
                       "n": sum(r["group"] == g for r in records)} for g in groups},
        "detectors": results,
    }


def _pct(x: float) -> str:
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.0f}%"


def _cell(stat: dict | None) -> str:
    if not stat or not stat["n"]:
        return "-"
    lo, hi = stat["ci95"]
    return f"{_pct(stat['rate'])} ({_pct(lo)}–{_pct(hi)})"


def _group_table(report: dict, names: list[str], key: str) -> list[str]:
    lines = ["| Group | Kind | " + " | ".join(names) + " |",
             "|---|---|" + "---:|" * len(names)]
    for g, info in report["groups"].items():
        kind = "human → false positives" if info["label"] == 0 else "machine → detected"
        cells = [_cell(report["detectors"][n].get(key, {}).get(g)) for n in names]
        lines.append(f"| {g} | {kind} | " + " | ".join(cells) + " |")
    return lines


def markdown(report: dict, title: str, sources: list[str]) -> str:
    c = report["counts"]
    dets = report["detectors"]
    names = list(dets)
    out = [
        f"# Detector report card: {title}",
        "",
        f"Generated {report['generated']} with aicl {report['aicl_version']} (seed {report['seed']}). "
        f"{c['documents']} documents: {c['human']} human-written, {c['machine']} machine-generated. "
        f"{c['calibration_humans']} human texts were held out for calibration.",
        "",
        *([f"> **Warning:** {c['calibration_humans']} calibration texts cannot resolve a "
           f"{_pct(report['target_fpr'])} false-positive target (at least "
           f"{math.ceil(1 / report['target_fpr'])} are needed). Use a larger sample.", ""]
          if c["calibration_humans"] * report["target_fpr"] < 1 else []),
        "## Separability (evaluation split)",
        "",
        "| Detector | What it scores | AUROC (95% CI) | Scored |",
        "|---|---|---:|---:|",
    ]
    for n, d in dets.items():
        ci = d["auroc_ci95"]
        auc = f"{d['auroc']:.3f}" + (f" ({ci[0]:.3f}–{ci[1]:.3f})" if ci else "")
        out.append(f"| {n} | {d['description']} | {auc} | {d['scored']} |")

    out += [
        "",
        f"## Flag rates at a threshold calibrated to {_pct(report['target_fpr'])} false positives",
        "",
        "Each detector's threshold was set on the held-out human texts so that at most "
        f"{_pct(report['target_fpr'])} of them were flagged. Rows show the share of each "
        "evaluation group flagged as machine-generated, with Wilson 95% intervals.",
        "",
        *_group_table(report, names, "calibrated"),
    ]
    vendor = [n for n in names if "vendor" in dets[n]]
    if vendor:
        out += [
            "",
            f"## Flag rates at the vendors' own {dets[vendor[0]]['vendor_threshold']} cut-off",
            "",
            "Third-party scores as recorded by the dataset authors, all records included. "
            "These are historical snapshots: vendors have since changed their models.",
            "",
            *_group_table(report, vendor, "vendor"),
        ]
    out += [
        "",
        "## How to read this",
        "",
        "- AUROC is the probability that a randomly chosen machine text scores higher than a randomly "
        "chosen human text. 0.5 is chance.",
        "- A low overall false-positive rate can hide a high rate for one group. Compare the human rows.",
        "- Small groups have wide intervals. Do not rank detectors whose intervals overlap.",
        "- Protocol: docs/report_card.md. Reproduce with the command in that document.",
        "",
        "## Sources",
        "",
        *[f"- {s}" for s in sources],
        "",
    ]
    return "\n".join(out)


def write(report: dict, title: str, sources: list[str], out_dir: str) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md, js = out / "report.md", out / "report.json"
    md.write_text(markdown(report, title, sources), encoding="utf-8")
    from ..cli import _json_safe

    js.write_text(json.dumps(_json_safe(report), indent=2), encoding="utf-8")
    return md, js
