# Measurement Model

This document defines every measure `aicl` reports: what it computes, what it is sensitive to, and what it cannot tell you. It replaces an earlier draft that framed these quantities as levers for evading AI detectors. That framing was neither supported by evidence nor the purpose of this project.

**Ground rule:** no measure here, alone or combined, establishes who or what wrote a text. Style varies with genre, register, length, editing, and the writer's first language. Treat every number as a description to compare under the same method, not a verdict.

## 1. Units

A document $D$ is parsed into sections $C_1,\dots,C_N$ (split at Markdown headings), paragraphs (blank-line separated; each list item is its own paragraph) and sentences $s_1,\dots,s_M$. Headings, fenced code and inline code are excluded. A *word* is a run of letters or digits, optionally joined by an apostrophe or hyphen. $|x|$ is the word count of unit $x$.

Sentence splitting is rule-based: a boundary is terminal punctuation (`.` `!` `?` `…`, with any closing quotes or brackets) followed by whitespace and an uppercase letter, digit or opening quote. Common abbreviations and single-letter initials do not end sentences. The rules are in `src/aicl/text.py` and covered by tests; use the same version of `aicl` for both texts in any comparison.

## 2. Structural variation

For any list of unit lengths $x_1,\dots,x_n$:

$$\mu = \frac{1}{n}\sum_i x_i,\qquad \sigma = \sqrt{\frac{1}{n}\sum_i (x_i-\mu)^2},\qquad \mathrm{CV} = \frac{\sigma}{\mu}$$

`aicl` reports these for sentence, paragraph and section lengths, plus min, p10, median, p90 and max.

**Why CV and not raw SD.** The SD of sentence length grows with mean sentence length. A text of long sentences will have a larger SD than a text of short ones even when both are equally uniform. CV is scale-free, so it can be compared across texts with different average sentence lengths. The earlier draft's "burstiness $=\sigma = 10.4$" is not comparable between documents for this reason.

**Uncertainty.** With few sentences, CV is noisy. `aicl` reports a 95% percentile-bootstrap interval (2,000 resamples, fixed seed) for sentence-length CV when $M \ge 10$. If the intervals of two versions overlap substantially, do not claim a change.

**Caveats.** Sentence lengths are not independent (writers alternate deliberately), so the bootstrap interval is approximate. Lists, dialogue and headings-heavy documents shift these numbers for reasons unrelated to authorship. Section-length CV depends mostly on how the author chose to divide the document.

## 3. Lexical diversity

- **TTR**: distinct words / total words. Falls with text length, so only compare equal-length texts.
- **MATTR** (Covington & McFall, 2010): mean TTR over every window of 50 consecutive words. Much less length-dependent than TTR.
- **MTLD** (McCarthy & Jarvis, 2010): the mean length of word runs that keep TTR above 0.72, averaged over a forward and a backward pass. Unreliable below about 100 words. Undefined, reported as `null`, when the text never drops below the threshold.

## 4. Repetition

- **Distinct-n** (Li et al., 2016): unique n-grams / total n-grams for $n = 2, 3$.
- **Opener diversity**: unique first-two-word pairs / sentences. Low values mean many sentences start the same way.
- **Top repeated trigrams**: the most frequent three-word sequences occurring more than once.

## 5. Stock phrases and punctuation

**Stock-phrase density** counts matches per 1,000 words against a curated list (`src/aicl/phrases.py`) of words and frames that occur often in instruction-tuned model output ("delve", "it is important to note", "plays a crucial role"). Every entry is normal English, and overlapping patterns can count one passage twice. The measure is meant for spotting filler and cliché, not as evidence of authorship.

**Punctuation rates** count em dashes, semicolons, colons, question marks, exclamation marks and opening parentheses per 1,000 words.

## 6. Language-model measures (optional, `--lm`)

Given a causal language model $P_\theta$ and a token sequence $t_1,\dots,t_T$, the surprisal of token $t_i$ is $-\log_2 P_\theta(t_i \mid t_{<i})$ bits, and

$$\mathrm{PPL}(D) = 2^{\frac{1}{T}\sum_i -\log_2 P_\theta(t_i\mid t_{<i})}$$

`aicl` also reports the distribution of surprisal (its SD is a token-level measure of how uneven predictability is), the mean predictive entropy, and **GLTR rank buckets** (Gehrmann et al., 2019): the share of tokens that were the model's top-10, top-100 or top-1000 prediction, or lower-ranked.

Long texts are scored in non-overlapping windows of up to the model's context length. The first token of each window is used as context only. Results depend on the model, its tokenizer and the window, and all three are reported. Perplexities from different models are not comparable.

## 7. Binoculars (optional, `--binoculars`)

Binoculars (Hans et al., 2024) compares a text's perplexity with the cross-perplexity between two related models, an *observer* $M_1$ and a *performer* $M_2$ that share a tokenizer:

$$B(D) = \frac{\frac{1}{T}\sum_i -\log P_{M_2}(t_i\mid t_{<i})}{\frac{1}{T}\sum_i \sum_{v} P_{M_1}(v\mid t_{<i})\,\bigl(-\log P_{M_2}(v\mid t_{<i})\bigr)}$$

Lower scores mean the text is about as predictable as a model expects text to be, which is typical of LLM output. The thresholds published in the paper apply only to its Falcon-7B / Falcon-7B-Instruct pair. `aicl` defaults to the small `gpt2` / `distilgpt2` pair, which runs on a laptop but is **uncalibrated** (`"calibrated": false`). Do not turn its score into a label without calibrating on labeled data from your own domain.

## 8. What these measures do not support

- **No threshold separates "human" from "AI".** Published work shows detectors misclassify human writing, disproportionately text by non-native English writers (Liang et al., 2023), and that light paraphrasing defeats many of them (Sadasivan et al., 2023; Krishna et al., 2023).
- **Raising a measure does not make text better.** Inserting one-word sentences raises CV, and inserting rare jargon raises perplexity. Both can make writing worse and say nothing about provenance.
- **Comparisons must hold the method fixed:** same `aicl` version, same model and window, comparable length and genre.

## References

- Covington, M. A., & McFall, J. D. (2010). Cutting the Gordian knot: The moving-average type–token ratio (MATTR). *Journal of Quantitative Linguistics*, 17(2).
- Gehrmann, S., Strobelt, H., & Rush, A. M. (2019). GLTR: Statistical detection and visualization of generated text. *ACL System Demonstrations*.
- Hans, A., et al. (2024). Spotting LLMs with Binoculars: Zero-shot detection of machine-generated text. *ICML*.
- Krishna, K., et al. (2023). Paraphrasing evades detectors of AI-generated text, but retrieval is an effective defense. *NeurIPS*.
- Li, J., et al. (2016). A diversity-promoting objective function for neural conversation models. *NAACL*.
- Liang, W., et al. (2023). GPT detectors are biased against non-native English writers. *Patterns*, 4(7).
- McCarthy, P. M., & Jarvis, S. (2010). MTLD, vocd-D, and HD-D: A validation study of sophisticated approaches to lexical diversity assessment. *Behavior Research Methods*, 42(2).
- Sadasivan, V. S., et al. (2023). Can AI-generated text be reliably detected? *arXiv:2303.11156*.
