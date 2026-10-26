"""Benchmark datasets, normalised to a common record format.

A record is a dict with:
  id      unique string
  text    the document
  label   0 = human-written, 1 = machine-generated
  group   the subgroup reported separately (e.g. "TOEFL essays", "gpt4")
  scores  optional {detector name: score in [0, 1]} recorded by a third party

Data is downloaded on first use into $AICL_CACHE (default ~/.cache/aicl) and
never redistributed with this package.
"""

from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CACHE = Path(os.environ.get("AICL_CACHE", Path.home() / ".cache" / "aicl"))


def _backoff(attempt: int) -> None:
    time.sleep(min(60, 3 * 2 ** attempt))


def _fetch_json(url: str, cache_name: str | None = None, retries: int = 10):
    """GET JSON with caching. The Hugging Face datasets server intermittently
    rejects valid queries (422, 502, "index is loading"), so everything except a
    404 is retried with capped exponential backoff, about six minutes in total."""
    path = CACHE / cache_name if cache_name else None
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if attempt == retries - 1:
                raise
            _backoff(attempt)
            continue
        except OSError:
            if attempt == retries - 1:
                raise
            _backoff(attempt)
            continue
        if isinstance(data, dict) and "error" in data:
            if attempt == retries - 1:
                raise RuntimeError(f"{url}: {data['error']}")
            _backoff(attempt)
            continue
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data), encoding="utf-8")
        return data


# --- Liang et al. (2023), "GPT detectors are biased against non-native English writers" ---

LIANG_BASE = (
    "https://raw.githubusercontent.com/Weixin-Liang/ChatGPT-Detector-Bias/main/Data_and_Results"
)
LIANG_DETECTORS = ["Crossplag", "GPTZero", "HFOpenAI", "OriginalityAI", "Quil", "Sapling", "ZeroGPT"]
LIANG_SETS = {
    # folder: (group label, label)
    "Human_Data/TOEFL_real_91": ("TOEFL essays (non-native writers)", 0),
    "Human_Data/HewlettStudentEssay_real_88": ("US 8th-grade essays", 0),
    "Human_Data/CollegeEssay_real_70": ("US college admission essays", 0),
    "Human_Data/CS224N_real_145": ("Stanford CS224N abstracts", 0),
    "GPT_Data/CollegeEssay_gpt3_31": ("GPT-3.5 college essays", 1),
    "GPT_Data/CS224N_gpt3_145": ("GPT-3.5 CS224N abstracts", 1),
    "GPT_Data/CollegeEssay_gpt3PromptEng_31": ("GPT-3.5 college essays, literary prompt", 1),
    "GPT_Data/CS224N_gpt3PromptEng_145": ("GPT-3.5 CS224N abstracts, literary prompt", 1),
}
LIANG_CITATION = (
    "Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J. (2023). GPT detectors are biased "
    "against non-native English writers. Patterns, 4(7). Data: "
    "https://github.com/Weixin-Liang/ChatGPT-Detector-Bias (MIT)."
)


def liang() -> list[dict]:
    """Human and GPT essays from Liang et al. (2023), with the commercial detector
    scores the authors recorded in 2023 (a historical snapshot; vendors have
    since updated their models)."""
    records = []
    for folder, (group, label) in LIANG_SETS.items():
        cache = f"liang/{folder}"
        docs = _fetch_json(f"{LIANG_BASE}/{folder}/data.json", f"{cache}/data.json")
        vendor: dict[str, dict[str, float]] = {}
        for det in LIANG_DETECTORS:
            rows = _fetch_json(f"{LIANG_BASE}/{folder}/{det}.json", f"{cache}/{det}.json") or []
            vendor[det] = {r["document"]: r["score"] for r in rows if r.get("score") is not None}
        for i, d in enumerate(docs):
            text = d["document"]
            scores = {f"{det} (2023)": vendor[det][text] for det in LIANG_DETECTORS if text in vendor[det]}
            records.append({"id": f"{folder}/{i}", "text": text, "label": label, "group": group,
                            "scores": scores})
    return records


# --- RAID (Dugan et al., 2024) ---

RAID_PARQUET = "datasets/liamdugan/raid@refs%2Fconvert%2Fparquet/raid/partial-train"
RAID_CITATION = (
    "Dugan, L., et al. (2024). RAID: A shared benchmark for robust evaluation of "
    "machine-generated text detectors. ACL. Data: https://huggingface.co/datasets/liamdugan/raid (MIT)."
)
RAID_MODELS = ["gpt2", "gpt3", "chatgpt", "gpt4", "cohere", "cohere-chat", "llama-chat",
               "mistral", "mistral-chat", "mpt", "mpt-chat"]
RAID_DOMAINS = ["abstracts", "books", "news", "poetry", "recipes", "reddit", "reviews", "wiki"]


def _raid_files():
    try:
        import pyarrow.parquet as pq
        from huggingface_hub import HfFileSystem
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError('RAID needs pyarrow and huggingface_hub: pip install "ai-content-lab[bench]"') from exc
    fs = HfFileSystem()
    return fs, pq, sorted(fs.glob(f"{RAID_PARQUET}/*.parquet"))


def _raid_index() -> dict[tuple[str, str, str], list[tuple[int, int, int]]]:
    """Map (model, attack, domain) -> [(file, row group, row within group)].

    Built once from the three label columns of RAID's Parquet export (about
    3 minutes) and cached; the generation texts are not downloaded here.
    """
    path = CACHE / "raid" / "index.json"
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {tuple(k.split("|")): [tuple(x) for x in v] for k, v in raw.items()}
    fs, pq, files = _raid_files()
    index: dict[tuple[str, str, str], list[tuple[int, int, int]]] = {}
    for fi, name in enumerate(files):
        pf = pq.ParquetFile(fs.open(name, "rb"))
        for rg in range(pf.metadata.num_row_groups):
            t = pf.read_row_group(rg, columns=["model", "attack", "domain"]).to_pydict()
            for i, key in enumerate(zip(t["model"], t["attack"], t["domain"])):
                index.setdefault(key, []).append((fi, rg, i))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"|".join(k): v for k, v in index.items()}), encoding="utf-8")
    return index


def _raid_pick(rows: list[tuple[int, int, int]], n: int, rng: random.Random, chunk: int = 5):
    """Pick n rows in runs of up to `chunk` from randomly chosen row groups, so a
    stratum costs about n / chunk row-group downloads instead of n."""
    by_group: dict[tuple[int, int], list[int]] = {}
    for fi, rg, i in rows:
        by_group.setdefault((fi, rg), []).append(i)
    groups = list(by_group)
    rng.shuffle(groups)
    picked = []
    for g in groups:
        if len(picked) >= n:
            break
        members = by_group[g]
        start = rng.randrange(max(1, len(members) - chunk + 1))
        picked += [(*g, i) for i in members[start : start + min(chunk, n - len(picked))]]
    return picked


def _raid_fetch(picks: list[tuple[int, int, int]]) -> dict[tuple[int, int, int], dict]:
    """Download the chosen rows, reading each needed row group once (cached on disk)."""
    cache = CACHE / "raid" / "rows"
    out, todo = {}, {}
    for fi, rg, i in picks:
        f = cache / f"{fi}-{rg}-{i}.json"
        if f.exists():
            out[(fi, rg, i)] = json.loads(f.read_text(encoding="utf-8"))
        else:
            todo.setdefault((fi, rg), []).append(i)
    if todo:
        fs, pq, files = _raid_files()
        cache.mkdir(parents=True, exist_ok=True)
        handles: dict[int, object] = {}
        cols = ["id", "model", "domain", "attack", "decoding", "generation"]
        for (fi, rg), rows in sorted(todo.items()):
            if fi not in handles:
                handles[fi] = pq.ParquetFile(fs.open(files[fi], "rb"))
            t = handles[fi].read_row_group(rg, columns=cols).to_pydict()
            for i in rows:
                row = {c: t[c][i] for c in cols}
                (cache / f"{fi}-{rg}-{i}.json").write_text(json.dumps(row), encoding="utf-8")
                out[(fi, rg, i)] = row
    return out


def raid_domains() -> list[str]:
    """Domains present in the Parquet export (which covers only part of RAID's train split)."""
    return sorted({d for (_, _, d) in _raid_index()})


def raid(
    n: int = 20,
    domains: list[str] | None = None,
    models: list[str] | None = None,
    attacks: list[str] | None = None,
    seed: int = 0,
) -> list[dict]:
    """Stratified sample of RAID's train split: n human texts per domain, n
    unattacked generations per model x domain, and n generations per attack
    (pooled over models) x domain. Attacked texts are reported per attack, so
    robustness can be read directly from the report."""
    rng = random.Random(seed)
    index = _raid_index()
    available = {d for (_, _, d) in index}
    domains = domains or sorted(available)
    missing = [d for d in domains if d not in available]
    if missing:
        raise ValueError(f"RAID Parquet export has no domain(s) {missing}; available: {sorted(available)}")
    models = models or RAID_MODELS
    attacks = attacks or []

    # (label, group, picks) per stratum; attacked texts are drawn evenly across
    # generator models and pooled per attack.
    strata = []
    per_model = max(1, -(-n // len(models)))
    for domain in domains:
        strata.append((0, f"human: {domain}", _raid_pick(index.get(("human", "none", domain), []), n, rng)))
        for model in models:
            strata.append((1, f"model: {model}", _raid_pick(index.get((model, "none", domain), []), n, rng)))
        for attack in attacks:
            for model in models:
                strata.append((1, f"attack: {attack}",
                               _raid_pick(index.get((model, attack, domain), []), per_model, rng)))

    rows = _raid_fetch([p for _, _, picks in strata for p in picks])
    records = []
    for label, group, picks in strata:
        for p in picks:
            r = rows[p]
            text = (r.get("generation") or "").strip()
            if text:
                records.append({"id": r["id"], "text": text, "label": label, "group": group,
                                "meta": {k: r.get(k) for k in ("model", "domain", "attack", "decoding")}})
    return records


def jsonl(path: str) -> list[dict]:
    """Your own data: one JSON object per line with text, label (0/1) and optional group."""
    records = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if line.strip():
                r = json.loads(line)
                records.append({"id": str(r.get("id", i)), "text": r["text"], "label": int(r["label"]),
                                "group": r.get("group", "human" if int(r["label"]) == 0 else "machine"),
                                "scores": r.get("scores", {})})
    return records
