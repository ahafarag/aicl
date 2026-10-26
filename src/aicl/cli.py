"""Command-line interface: `aicl analyze FILE [--compare FILE]`."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from . import __version__
from .metrics import analyze
from .report import compare, summary


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _measure(text: str, args) -> dict:
    result = analyze(text)
    if args.lm or args.binoculars:
        from . import lm

        if args.lm:
            result["lm"] = lm.lm_metrics(
                text, model=args.model, device=args.device, return_tokens=args.tokens
            )
        if args.binoculars:
            result["binoculars"] = lm.binoculars(
                text, observer=args.observer, performer=args.performer, device=args.device
            )
    return result


def _json_safe(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


def _split_arg(value: str | None) -> list[str] | None:
    return [v.strip() for v in value.split(",") if v.strip()] if value else None


def _bench(args) -> int:
    from .bench import data
    from .bench.run import evaluate, write

    if args.dataset == "liang":
        records, title, sources = data.liang(), "Liang et al. (2023) essays", [data.LIANG_CITATION]
    elif args.dataset == "raid":
        records = data.raid(n=args.n, domains=_split_arg(args.domains), models=_split_arg(args.models),
                            attacks=_split_arg(args.attacks), seed=args.seed)
        title, sources = "RAID sample", [data.RAID_CITATION]
    else:
        records, title, sources = data.jsonl(args.dataset), Path(args.dataset).stem, [args.dataset]

    def progress(name: str, i: int, n: int) -> None:
        if i == n or i % 25 == 0:
            print(f"\r{name}: {i}/{n}", end="\n" if i == n else "", file=sys.stderr, flush=True)

    report = evaluate(records, _split_arg(args.detectors) or [], target_fpr=args.fpr,
                      seed=args.seed, progress=progress)
    out = args.out or f"reports/{Path(args.dataset).stem}"
    md, js = write(report, title, sources, out)
    print(f"Wrote {md} and {js}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aicl", description="Reproducible stylometric measurement for prose."
    )
    parser.add_argument("--version", action="version", version=f"aicl {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="measure a document, or compare two versions")
    a.add_argument("file", help="text or Markdown file ('-' for stdin)")
    a.add_argument("--compare", metavar="FILE", help="second version to compare against FILE")
    a.add_argument("--json", action="store_true", help="print machine-readable JSON")
    a.add_argument("--lm", action="store_true", help="add perplexity/surprisal (needs [lm] extra)")
    a.add_argument("--model", default="gpt2", help="reference model for --lm (default: gpt2)")
    a.add_argument("--tokens", action="store_true", help="include per-token surprisal in JSON")
    a.add_argument("--binoculars", action="store_true", help="add an uncalibrated Binoculars score")
    a.add_argument("--observer", default="gpt2")
    a.add_argument("--performer", default="distilgpt2")
    a.add_argument("--device", default="cpu")

    b = sub.add_parser("bench", help="evaluate AI-text detectors and write a report card")
    b.add_argument("dataset", help="'liang', 'raid', or a JSONL file with text/label/group")
    b.add_argument("--detectors", default="binoculars,perplexity,gltr-top10,stock-phrases,low-sentence-cv",
                   help="comma-separated built-in detectors ('' for third-party scores only)")
    b.add_argument("--fpr", type=float, default=0.05, help="target false-positive rate for calibration")
    b.add_argument("--seed", type=int, default=0)
    b.add_argument("--n", type=int, default=20, help="RAID: texts per stratum")
    b.add_argument("--domains", help="RAID: comma-separated domains (default: all in the Parquet export)")
    b.add_argument("--models", help="RAID: comma-separated generator models")
    b.add_argument("--attacks", default="", help="RAID: comma-separated adversarial attacks to include")
    b.add_argument("--out", help="output directory (default: reports/<dataset>)")

    args = parser.parse_args(argv)
    if args.command == "bench":
        return _bench(args)
    before = _measure(_read(args.file), args)
    if args.compare:
        after = _measure(_read(args.compare), args)
        if args.json:
            print(json.dumps(_json_safe({"before": before, "after": after}), indent=2))
        else:
            print(compare(before, after, (Path(args.file).name, Path(args.compare).name)))
    elif args.json:
        print(json.dumps(_json_safe(before), indent=2))
    else:
        print(summary(before, Path(args.file).name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
