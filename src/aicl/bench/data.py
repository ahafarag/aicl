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

import hashlib
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

RAID_ROWS = "https://datasets-server.huggingface.co/filter"
RAID_CITATION = (
    "Dugan, L., et al. (2024). RAID: A shared benchmark for robust evaluation of "
    "machine-generated text detectors. ACL. Data: https://huggingface.co/datasets/liamdugan/raid (MIT)."
)
RAID_MODELS = ["gpt2", "gpt3", "chatgpt", "gpt4", "cohere", "cohere-chat", "llama-chat",
               "mistral", "mistral-chat", "mpt", "mpt-chat"]
RAID_DOMAINS = ["abstracts", "books", "news", "poetry", "recipes", "reddit", "reviews", "wiki"]


def _raid_stratum(where: str, n: int, rng: random.Random, chunk: int = 5) -> list[dict]:
    q = lambda offset, length: RAID_ROWS + "?" + urllib.parse.urlencode({  # noqa: E731
        "dataset": "liamdugan/raid", "config": "raid", "split": "train",
        "where": where, "offset": offset, "length": length})
    key = hashlib.sha1(where.encode()).hexdigest()[:16]
    total = _fetch_json(q(0, 1), f"raid/count-{key}.json")["num_rows_total"]
    rows: dict[str, dict] = {}
    for _ in range(max(1, n // chunk) * 3):
        if len(rows) >= n or total == 0:
            break
        offset = rng.randrange(max(1, total - chunk))
        page = _fetch_json(q(offset, chunk), f"raid/rows-{key}-{offset}-{chunk}.json")
        for r in page["rows"]:
            rows.setdefault(r["row"]["id"], r["row"])
    return list(rows.values())[:n]


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
    domains = domains or ["abstracts", "news", "reddit", "reviews"]
    models = models or RAID_MODELS
    attacks = attacks or []
    records = []

    def add(rows: list[dict], label: int, group: str) -> None:
        for r in rows:
            text = (r.get("generation") or "").strip()
            if text:
                records.append({"id": r["id"], "text": text, "label": label, "group": group,
                                "meta": {k: r.get(k) for k in ("model", "domain", "attack", "decoding")}})

    for domain in domains:
        add(_raid_stratum(f"\"model\"='human' AND \"attack\"='none' AND \"domain\"='{domain}'", n, rng),
            0, f"human: {domain}")
        for model in models:
            where = f"\"model\"='{model}' AND \"attack\"='none' AND \"domain\"='{domain}'"
            add(_raid_stratum(where, n, rng), 1, f"model: {model}")
        # The filter API has no reliable negation, so attacked texts are drawn
        # evenly across generator models and pooled per attack.
        per_model = max(1, -(-n // len(models)))
        for attack in attacks:
            for model in models:
                where = f"\"model\"='{model}' AND \"attack\"='{attack}' AND \"domain\"='{domain}'"
                add(_raid_stratum(where, per_model, rng), 1, f"attack: {attack}")
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
