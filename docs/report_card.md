# Detector Report Card: Protocol

`aicl bench` evaluates AI-text detectors on labelled data and reports how often each one flags human writing, broken down by who wrote it. The aim is to measure what matters to someone on the receiving end of a detector: a student, a job applicant, an author.

## Reproduce

```bash
pip install -e ".[lm]"
aicl bench liang --out reports/liang
aicl bench raid --n 20 --attacks paraphrase,synonym,homoglyph --out reports/raid
aicl bench my_data.jsonl            # {"text": ..., "label": 0|1, "group": ...} per line
```

Data downloads on first use to `~/.cache/aicl` (override with `AICL_CACHE`), and so do detector scores, so an interrupted run resumes where it stopped. The seed (default 0) fixes every random choice.

## Datasets

| Name | Contents | Source |
|---|---|---|
| `liang` | 91 TOEFL essays by non-native English writers; 88 US 8th-grade essays; 70 US college admission essays; 145 Stanford CS224N abstracts; 352 GPT-3.5 texts (half generated with a "use literary language" prompt). Also includes the scores seven commercial detectors gave each text in 2023. | Liang et al. (2023), MIT |
| `raid` | Stratified sample of RAID's train split: human texts per domain, unattacked generations per model, and attacked generations per attack. | Dugan et al. (2024), MIT |
| JSONL | Your own labelled data. | - |

The 2023 commercial scores are a **historical snapshot**. Vendors have since changed their models, so these numbers describe what users saw at the time, not the products today. To evaluate a current service, score the texts with it, where its terms allow, and supply the scores in a JSONL `scores` field.

## Procedure

1. **Split.** Human texts in each group are shuffled and halved. One half from every group forms the *calibration pool*. All machine texts and the other half of the human texts form the *evaluation split*.
2. **Calibrate.** For each detector, choose the threshold $t$ so that at most the target share (default 5%) of calibration humans score above $t$. This is how a careful deployer would tune a detector on writing they trust.
3. **Separability.** On the evaluation split, report AUROC (Mann–Whitney, ties count half) with a 1,000-resample percentile bootstrap 95% CI, resampling each class independently.
4. **Flag rates.** For each evaluation group, report the share with score $> t$, with a Wilson 95% interval. For human groups this is the false-positive rate, for machine groups the detection rate.
5. **Vendor cut-off.** Third-party scores in $[0,1]$ are also evaluated at 0.5 over all records. This is the decision their users saw. Liang et al. used the same rule, and applying it to their data reproduces the paper's average 61.2% false-positive rate on TOEFL essays.

## Built-in detectors

All scores are oriented so that higher means more machine-like.

| Name | Score | Notes |
|---|---|---|
| `binoculars` | negative Binoculars score, gpt2 observer / distilgpt2 performer | zero-shot; small, uncalibrated model pair |
| `perplexity` | negative perplexity under gpt2 | the classic zero-shot baseline |
| `gltr-top10` | share of tokens in gpt2's top-10 predictions | GLTR (Gehrmann et al., 2019) |
| `stock-phrases` | stock-phrase density per 1,000 words | a naive style heuristic, included as a baseline |
| `low-sentence-cv` | negative sentence-length CV | the "burstiness" folk heuristic, included as a baseline |

The two heuristic baselines are there to test popular claims, for example that AI text has uniform sentence lengths, against data.

## Limitations

- Group sizes are small (31–145 texts). The intervals are wide, and the reports print them for that reason.
- The calibration pool mixes human groups in proportion to their size. A detector calibrated on one population can behave differently on another, and that difference is what the per-group rows show.
- Essays in `liang` are short (often under 200 words). Detectors generally do worse on short texts.
- GPT-3.5 texts from 2023 are easier to detect than output from current models. RAID covers more generators.
- Group differences in flag rates are associated with the groups, not necessarily caused by writer background. TOEFL essays also differ in topic, length and prompt.
