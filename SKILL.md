---
name: stylometric-humanization
description: "Humanize prose for clarity, voice, rhythm, and reader engagement while measuring stylometric properties such as sentence-length burstiness, chapter-length variance, vocabulary diversity, and perplexity proxies. Use for transparent editing, authorship analysis, AI-content evaluation, and reproducible before/after reports. Do not use to evade AI detectors, impersonate a human author, conceal AI assistance, or claim that detector scores prove provenance."
argument-hint: "[content or file path] [optional audience, voice, and measurement settings]"
user-invocable: true
---

# Stylometric Humanization and Measurement

## Purpose

Improve writing so it reads naturally and consistently for its intended audience, then measure observable text characteristics before and after editing. This skill is for readability, voice development, editorial QA, and research. It must not be used to manufacture a false human-authorship signal or to present a detector result as proof of authorship.

Measurements are computed with the `aicl` tool in this repository (`aicl analyze FILE --compare FILE2`), whose definitions are in `docs/measurement_model.md`. Three dimensions are central:

- **Macro-structural variance:** variation in chapter or section word counts.
- **Syntactic burstiness:** standard deviation of sentence token counts.
- **Predictability/perplexity:** how expected the token sequence is to a reference language model.

These dimensions are descriptive signals, not acceptance targets. There is no universal “human” range, and changing them does not establish human provenance.

## When to Use

- Rewrite AI-assisted or rough prose for clarity, specificity, rhythm, and an appropriate author voice.
- Compare a draft and edited version using reproducible stylometric measurements.
- Produce an editorial report containing metrics, qualitative changes, limitations, and provenance disclosures.
- Evaluate results from GPTZero or similar services when the user supplies the result or explicitly requests an authorized browser check.
- Investigate whether a document is stylistically monotonous without inferring authorship from style alone.

Do not:

- Optimize edits toward a requested detector percentage or a false-positive “human” classification.
- Add fabricated personal experiences, fake citations, invented technical details, or deliberate errors to appear human.
- Remove or conceal required AI-use disclosures.
- Treat GPTZero, perplexity, burstiness, or any other classifier as ground truth.

## Procedure

### 1. Establish the editing contract

Before changing text, identify:

1. The intended audience, purpose, register, and reading level.
2. Whether the user wants light editing, a substantial rewrite, or analysis only.
3. Any facts, citations, terminology, structure, or disclosures that must be preserved.
4. The provenance context: human-written, AI-assisted, or unknown.
5. The comparison unit: whole document, chapter, section, or paragraph.

If the request is specifically to “beat,” “pass,” or “score human” on a detector, explain that detector evasion and provenance misrepresentation are not supported. Offer natural-language editing plus an honest measurement report instead.

### 2. Capture a baseline

Preserve the original text and record the following. `aicl analyze original.md --json` produces all of these except the feature counts and provenance statement:

- Word count and sentence count.
- Section/chapter word counts, if headings are available.
- Mean, standard deviation, minimum, maximum, and percentile sentence lengths.
- Vocabulary diversity, preferably type-token ratio and a length-normalized measure.
- Paragraph and section length distributions.
- Counts of headings, bullets, quotations, parentheticals, questions, and first-person statements where relevant.
- The provenance statement supplied by the user.

Use the same tokenizer and unit definitions for both versions. State how numbers are counted; punctuation-only fragments and headings should not silently change the result.

### 3. Edit for real reader value

Make changes that improve communication rather than target a detector:

- Replace vague claims with accurate, source-supported specifics.
- Remove repetition, generic transitions, inflated phrasing, and unnecessary summary statements.
- Vary sentence structure when the meaning and register support it.
- Combine fragments that obscure meaning and retain short sentences when they create a deliberate rhetorical effect.
- Use concrete examples only when they are true, supplied, or clearly labeled as hypothetical.
- Preserve the author’s intended voice; do not invent biography, emotion, memories, or expertise.
- Keep technical terminology precise and define it for the audience.
- Preserve citations and flag unsupported claims for review.

Never force arbitrary chapter sizes, insert random one-word sentences, add jargon solely to raise perplexity, or introduce associative digressions solely to change a classifier result.

### 4. Measure the edited version

Recompute the baseline metrics with the identical method. For section word counts \(L_i\), calculate:

$$
\mu_L = \frac{1}{N}\sum_i L_i,\qquad
\sigma_L = \sqrt{\frac{1}{N}\sum_i (L_i-\mu_L)^2}
$$

For sentence token counts \(l_j\), calculate burstiness:

$$
\mu_s = \frac{1}{M}\sum_j l_j,\qquad
\sigma_s = \sqrt{\frac{1}{M}\sum_j (l_j-\mu_s)^2}
$$

Because \(\sigma_s\) grows with mean sentence length, compare versions using the coefficient of variation \(\sigma_s/\mu_s\), and use the bootstrap interval `aicl` reports to judge whether a change exceeds sampling noise.

For a reference language model, report perplexity only when the model, tokenizer, corpus, and calculation are known:

$$
PP(D)=\exp\left(-\frac{1}{T}\sum_{t=1}^{T}\log P(w_t\mid w_{<t})\right)
$$

If no reproducible language-model measurement is available, report a clearly labeled **perplexity proxy** based on observable repetition or n-gram frequency, not a fabricated perplexity value.

### 5. Report change and interpretation

Present a before/after table with absolute and percentage change where meaningful:

| Metric | Before | After | Change | Interpretation |
|---|---:|---:|---:|---|
| Word count |  |  |  | Scope change |
| Sentence-length CV (95% CI) |  |  |  | Rhythm/structure |
| Section-length SD |  |  |  | Macro organization |
| Vocabulary measure |  |  |  | Lexical variety |
| Perplexity or proxy |  |  |  | Predictability under the stated method |

Add a qualitative review covering factual fidelity, voice, readability, accessibility, citation integrity, and any substantive changes. Distinguish:

- **Observed metrics:** calculated from the text.
- **External detector outputs:** supplied by the user or obtained through an authorized service.
- **Interpretation:** editorial or statistical judgment, not proof of provenance.

When an external detector percentage is provided, quote it as a service-specific result with its date, service name, settings, and text version. Do not aggregate percentages from different services into a “true” human score.

## Output Format

Return:

1. The revised content or a precise patch, unless analysis-only was requested.
2. A concise methods note defining tokenization, section boundaries, and formulas.
3. A before/after metrics table.
4. A qualitative editorial summary and factual/citation flags.
5. A provenance and detector-limitations note.

Use cautious language such as “the measured sentence-length variation increased” rather than “the text is now human” or “the detector was defeated.”

## Quality Checks

- Confirm that the revised text preserves required facts, citations, headings, and constraints.
- Confirm that every reported metric is computed using the stated method.
- Do not report a percentage without identifying what it measures and what it does not establish.
- Ensure edits improve reader value independently of any detector.
- If an external site is used, obtain user authorization, avoid uploading sensitive text, and record the service and date.
