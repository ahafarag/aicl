# ai-content-lab

**Open, reproducible measurement of prose style, for editors, researchers, and anyone who wants to check what AI detectors are actually measuring.**

Commercial AI detectors return one opaque percentage. `aicl` returns the measurements underneath (sentence-length variation, lexical diversity, repetition, stock-phrase density, perplexity, GLTR rank profiles, Binoculars scores), each with a written definition, a citation, and its known limits.

```console
$ aicl analyze examples/draft.md --compare examples/edited.md
Metric                    draft.md  edited.md   Change        %
------------------------  --------  ---------  -------  -------
Words                          198        207       +9    +4.5%
Sentence length, CV          0.320      0.510   +0.191   +59.6%
Paragraph length, CV         0.146      0.332   +0.186  +127.5%
MATTR (w=50)                 0.779      0.852   +0.073    +9.3%
MTLD                          69.8      112.8    +43.0   +61.7%
Distinct-2                   0.929      0.976   +0.047    +5.0%
Stock phrases / 1k words    106.06       0.00  -106.06  -100.0%
...
Sentence-length CV 95% CI (draft.md): 0.221-0.392
Sentence-length CV 95% CI (edited.md): 0.289-0.670
```

Note the overlapping confidence intervals: with 17 sentences, a 60% jump in sentence-length CV is not conclusive. `aicl` shows the uncertainty instead of hiding it.

## Install

```bash
pip install ai-content-lab            # core: pure Python, no dependencies
pip install "ai-content-lab[lm]"      # + perplexity, GLTR, Binoculars (torch, transformers)
```

From source:

```bash
git clone https://github.com/<you>/ai-content-lab && cd ai-content-lab
pip install -e ".[dev,lm]" && pytest
```

## Usage

```bash
aicl analyze essay.md                         # summary table
aicl analyze draft.md --compare final.md      # before/after with deltas
aicl analyze essay.md --json                  # everything, machine-readable
aicl analyze essay.md --lm                    # + perplexity and surprisal under gpt2
aicl analyze essay.md --lm --model gpt2-medium --tokens --json   # per-token surprisal
aicl analyze essay.md --binoculars            # + Binoculars score (uncalibrated)
cat essay.txt | aicl analyze -                # stdin
```

From Python:

```python
from aicl import analyze
r = analyze(open("essay.md").read())
r["sentence_length"]["cv"], r["lexical"]["mtld"], r["stock_phrases"]["per_1k_words"]
```

## What it measures

| Group | Measures | Needs |
|---|---|---|
| Structure | sentence / paragraph / section length: mean, SD, **CV**, percentiles, bootstrap CI | core |
| Lexical | TTR, **MATTR**, **MTLD** | core |
| Repetition | distinct-2/3, sentence-opener diversity, top repeated trigrams | core |
| Style | stock-phrase density by category, punctuation rates | core |
| Predictability | perplexity, surprisal distribution, entropy, GLTR rank buckets | `[lm]` |
| Zero-shot detector | Binoculars score (observer/performer pair of your choice) | `[lm]` |

Full definitions, formulas, and caveats: [docs/measurement_model.md](docs/measurement_model.md).

## Principles

1. **Descriptive, not a verdict.** No number here proves authorship. Detectors misclassify human writing, especially by non-native English writers ([Liang et al., 2023](https://doi.org/10.1016/j.patter.2023.100779)).
2. **Reproducible.** Same version, same input, same output. Models, windows, and seeds are reported in every result.
3. **Honest about uncertainty.** Small samples get confidence intervals and warnings, not bigger fonts.
4. **Built for better writing, not for evading detectors.** The editing workflow in [SKILL.md](SKILL.md) improves clarity and specificity and reports the measured change. It does not optimize against detector scores.

## Roadmap

- [ ] **Detector report card:** run open and commercial detectors over public benchmarks (e.g. RAID) and human-written corpora; publish false-positive rates, calibration, and robustness to light editing.
- [ ] Reference profiles: per-genre distributions so a value can be read as a percentile against human-written text of the same kind.
- [ ] HTML report with a GLTR-style per-token surprisal heatmap.
- [ ] Web demo (Hugging Face Space).
- [ ] Better sentence segmentation for non-English text.

Contributions are welcome, especially stock-phrase entries backed by a corpus comparison and new measures with a citation.

## Citation

```bibtex
@software{ai_content_lab,
  title  = {ai-content-lab: reproducible stylometric measurement for prose},
  author = {Abdelrahman},
  year   = {2026},
  url    = {https://github.com/<you>/ai-content-lab}
}
```

## License

MIT
