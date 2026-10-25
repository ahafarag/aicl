"""Human-readable reports: single-document summary and before/after comparison."""

from __future__ import annotations

import math

# (label, path into the analyze() result, format)
ROWS = [
    ("Words", ("counts", "words"), "d"),
    ("Sentences", ("counts", "sentences"), "d"),
    ("Paragraphs", ("counts", "paragraphs"), "d"),
    ("Sections", ("counts", "sections"), "d"),
    ("Sentence length, mean", ("sentence_length", "mean"), ".1f"),
    ("Sentence length, SD", ("sentence_length", "sd"), ".1f"),
    ("Sentence length, CV", ("sentence_length", "cv"), ".3f"),
    ("Sentence length, p10-p90", None, ""),
    ("Paragraph length, CV", ("paragraph_length", "cv"), ".3f"),
    ("Section length, CV", ("section_length", "cv"), ".3f"),
    ("TTR", ("lexical", "ttr"), ".3f"),
    ("MATTR (w=50)", ("lexical", "mattr_50"), ".3f"),
    ("MTLD", ("lexical", "mtld"), ".1f"),
    ("Distinct-2", ("repetition", "distinct_2"), ".3f"),
    ("Distinct-3", ("repetition", "distinct_3"), ".3f"),
    ("Opener diversity", ("repetition", "opener_diversity"), ".3f"),
    ("Stock phrases / 1k words", ("stock_phrases", "per_1k_words"), ".2f"),
    ("Em dashes / 1k words", ("punctuation_per_1k_words", "em_dash"), ".2f"),
    ("Perplexity", ("lm", "perplexity"), ".2f"),
    ("Surprisal SD (bits)", ("lm", "surprisal_bits", "sd"), ".2f"),
    ("Top-10 rank share", ("lm", "rank_buckets", "top10"), ".3f"),
    ("Binoculars score", ("binoculars", "score"), ".4f"),
]


def _get(result: dict, path: tuple) -> float | None:
    value = result
    for key in path:
        if not isinstance(value, dict) or value.get(key) is None:
            return None
        value = value[key]
    return value


def _fmt(value, spec: str) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    return format(value, spec)


def _spread(result: dict) -> str:
    sl = result.get("sentence_length") or {}
    if not sl.get("n"):
        return "-"
    return f"{sl['p10']:.0f}-{sl['p90']:.0f}"


def _table(header: list[str], rows: list[list[str]]) -> str:
    widths = [max(len(r[i]) for r in [header] + rows) for i in range(len(header))]
    line = lambda r: "  ".join(  # noqa: E731
        c.ljust(widths[i]) if i == 0 else c.rjust(widths[i]) for i, c in enumerate(r)
    )
    return "\n".join([line(header), line(["-" * w for w in widths])] + [line(r) for r in rows])


def _visible_rows(*results: dict):
    for label, path, spec in ROWS:
        if path is None:
            yield label, [_spread(r) for r in results], None, None
            continue
        values = [_get(r, path) for r in results]
        if all(v is None for v in values):
            continue
        yield label, [_fmt(v, spec) for v in values], values, spec


def summary(result: dict, name: str = "document") -> str:
    rows = [[label, cells[0]] for label, cells, _, _ in _visible_rows(result)]
    out = [_table(["Metric", name], rows)]
    ci = result.get("sentence_length_cv_ci95")
    if ci:
        out.append(f"\nSentence-length CV 95% bootstrap CI: {ci[0]:.3f}-{ci[1]:.3f}")
    out += _details(result)
    return "\n".join(out)


def compare(before: dict, after: dict, names: tuple[str, str] = ("before", "after")) -> str:
    rows = []
    for label, cells, values, spec in _visible_rows(before, after):
        change = pct = "-"
        if values and None not in values and not any(map(math.isnan, values)):
            delta = values[1] - values[0]
            change = ("+" if delta >= 0 else "") + format(delta, spec)
            if values[0]:
                pct = f"{100 * delta / abs(values[0]):+.1f}%"
        rows.append([label, *cells, change, pct])
    out = [_table(["Metric", names[0], names[1], "Change", "%"], rows)]
    for name, r in zip(names, (before, after)):
        ci = r.get("sentence_length_cv_ci95")
        if ci:
            out.append(f"Sentence-length CV 95% CI ({name}): {ci[0]:.3f}-{ci[1]:.3f}")
    return "\n".join(out)


def _details(result: dict) -> list[str]:
    out = []
    phrases = {
        p: c for cat in result["stock_phrases"]["by_category"].values() for p, c in cat.items()
    }
    if phrases:
        top = sorted(phrases.items(), key=lambda kv: -kv[1])[:10]
        out.append("\nStock phrases found: " + ", ".join(f"{p} ({c})" for p, c in top))
    trigrams = result["repetition"]["top_repeated_trigrams"][:5]
    if trigrams:
        out.append("Most repeated trigrams: " + ", ".join(f"{t['ngram']} ({t['count']})" for t in trigrams))
    for w in result.get("warnings", []):
        out.append(f"Warning: {w}")
    out.append(
        "\nThese are descriptive measurements, not a test of authorship. "
        "See docs/measurement_model.md."
    )
    return out
