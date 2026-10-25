# Detector report card: Liang et al. (2023) essays

Generated 2026-10-25 with aicl 0.1.0 (seed 0). 746 documents: 394 human-written, 352 machine-generated. 196 human texts were held out for calibration.

## Separability (evaluation split)

| Detector | What it scores | AUROC (95% CI) | Scored |
|---|---|---:|---:|
| binoculars | Binoculars, gpt2/distilgpt2, uncalibrated | 0.681 (0.633–0.723) | 746 |
| perplexity | Low perplexity under gpt2 | 0.729 (0.682–0.773) | 746 |
| gltr-top10 | GLTR top-10 rank share under gpt2 | 0.661 (0.612–0.709) | 746 |
| stock-phrases | Stock-phrase density (baseline) | 0.696 (0.660–0.731) | 746 |
| low-sentence-cv | Low sentence-length CV (baseline) | 0.856 (0.817–0.891) | 746 |
| Crossplag (2023) | Third-party score | 0.598 (0.547–0.645) | 746 |
| GPTZero (2023) | Third-party score | 0.722 (0.667–0.772) | 740 |
| HFOpenAI (2023) | Third-party score | 0.605 (0.554–0.654) | 746 |
| OriginalityAI (2023) | Third-party score | 0.635 (0.582–0.684) | 746 |
| Quil (2023) | Third-party score | 0.599 (0.535–0.654) | 601 |
| Sapling (2023) | Third-party score | 0.526 (0.472–0.578) | 601 |
| ZeroGPT (2023) | Third-party score | 0.553 (0.510–0.594) | 746 |

## Flag rates at a threshold calibrated to 5% false positives

Each detector's threshold was set on the held-out human texts so that at most 5% of them were flagged. Rows show the share of each evaluation group flagged as machine-generated, with Wilson 95% intervals.

| Group | Kind | binoculars | perplexity | gltr-top10 | stock-phrases | low-sentence-cv | Crossplag (2023) | GPTZero (2023) | HFOpenAI (2023) | OriginalityAI (2023) | Quil (2023) | Sapling (2023) | ZeroGPT (2023) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TOEFL essays (non-native writers) | human → false positives | 22% (12%–36%) | 17% (9%–31%) | 30% (19%–45%) | 0% (0%–8%) | 11% (5%–23%) | 17% (9%–31%) | 35% (23%–49%) | 17% (9%–31%) | 33% (21%–47%) | 17% (9%–31%) | 13% (6%–26%) | 22% (12%–36%) |
| US 8th-grade essays | human → false positives | 5% (1%–15%) | 5% (1%–15%) | 5% (1%–15%) | 0% (0%–8%) | 0% (0%–8%) | 0% (0%–8%) | 0% (0%–8%) | 0% (0%–8%) | 0% (0%–8%) | 0% (0%–8%) | 0% (0%–8%) | 0% (0%–8%) |
| US college admission essays | human → false positives | 6% (2%–19%) | 3% (1%–15%) | 3% (1%–15%) | 3% (1%–15%) | 0% (0%–10%) | 0% (0%–10%) | 3% (1%–15%) | 0% (0%–10%) | 0% (0%–10%) | 0% (0%–10%) | 3% (1%–15%) | 0% (0%–10%) |
| Stanford CS224N abstracts | human → false positives | 1% (0%–7%) | 0% (0%–5%) | 0% (0%–5%) | 14% (8%–23%) | 8% (4%–17%) | 0% (0%–5%) | 0% (0%–5%) | 1% (0%–7%) | 1% (0%–7%) | - | - | 0% (0%–5%) |
| GPT-3.5 college essays | machine → detected | 87% (71%–95%) | 100% (89%–100%) | 100% (89%–100%) | 32% (19%–50%) | 13% (5%–29%) | 42% (26%–59%) | 100% (89%–100%) | 52% (35%–68%) | 19% (9%–36%) | 0% (0%–11%) | 16% (7%–33%) | 97% (84%–99%) |
| GPT-3.5 CS224N abstracts | machine → detected | 58% (50%–66%) | 41% (33%–49%) | 32% (25%–40%) | 39% (32%–47%) | 48% (40%–56%) | 25% (19%–32%) | 6% (3%–11%) | 27% (20%–35%) | 23% (17%–30%) | 8% (5%–14%) | 14% (10%–21%) | 25% (19%–32%) |
| GPT-3.5 college essays, literary prompt | machine → detected | 0% (0%–11%) | 3% (1%–16%) | 3% (1%–16%) | 58% (41%–74%) | 10% (3%–25%) | 0% (0%–11%) | 10% (3%–25%) | 0% (0%–11%) | 0% (0%–11%) | 0% (0%–11%) | 0% (0%–11%) | 0% (0%–11%) |
| GPT-3.5 CS224N abstracts, literary prompt | machine → detected | 9% (5%–15%) | 3% (1%–7%) | 1% (0%–4%) | 52% (44%–60%) | 45% (37%–53%) | 2% (1%–6%) | 1% (0%–4%) | 2% (1%–6%) | 2% (1%–6%) | 1% (0%–5%) | 3% (1%–7%) | 0% (0%–3%) |

## Flag rates at the vendors' own 0.5 cut-off

Third-party scores as recorded by the dataset authors, all records included. These are historical snapshots: vendors have since changed their models.

| Group | Kind | Crossplag (2023) | GPTZero (2023) | HFOpenAI (2023) | OriginalityAI (2023) | Quil (2023) | Sapling (2023) | ZeroGPT (2023) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| TOEFL essays (non-native writers) | human → false positives | 52% (42%–62%) | 52% (42%–62%) | 58% (48%–68%) | 76% (66%–83%) | 75% (65%–83%) | 68% (58%–77%) | 48% (38%–58%) |
| US 8th-grade essays | human → false positives | 12% (7%–21%) | 0% (0%–4%) | 9% (5%–17%) | 1% (0%–6%) | 9% (5%–17%) | 5% (2%–11%) | 0% (0%–4%) |
| US college admission essays | human → false positives | 0% (0%–5%) | 1% (0%–8%) | 0% (0%–5%) | 4% (1%–12%) | 1% (0%–8%) | 1% (0%–8%) | 3% (1%–10%) |
| Stanford CS224N abstracts | human → false positives | 3% (1%–8%) | 1% (0%–4%) | 1% (0%–5%) | 8% (4%–13%) | - | - | 0% (0%–3%) |
| GPT-3.5 college essays | machine → detected | 58% (41%–74%) | 100% (89%–100%) | 58% (41%–74%) | 42% (26%–59%) | 58% (41%–74%) | 74% (57%–86%) | 100% (89%–100%) |
| GPT-3.5 CS224N abstracts | machine → detected | 37% (29%–45%) | 14% (9%–20%) | 41% (34%–50%) | 59% (50%–66%) | 57% (49%–65%) | 68% (60%–75%) | 31% (24%–39%) |
| GPT-3.5 college essays, literary prompt | machine → detected | 0% (0%–11%) | 13% (5%–29%) | 0% (0%–11%) | 0% (0%–11%) | 0% (0%–11%) | 0% (0%–11%) | 10% (3%–25%) |
| GPT-3.5 CS224N abstracts, literary prompt | machine → detected | 9% (5%–15%) | 1% (0%–4%) | 10% (6%–16%) | 28% (21%–35%) | 24% (18%–32%) | 18% (13%–25%) | 1% (0%–5%) |

## How to read this

- AUROC is the probability that a randomly chosen machine text scores higher than a randomly chosen human text. 0.5 is chance.
- A low overall false-positive rate can hide a high rate for one group. Compare the human rows.
- Small groups have wide intervals. Do not rank detectors whose intervals overlap.
- Protocol: docs/report_card.md. Reproduce with the command in that document.

## Sources

- Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J. (2023). GPT detectors are biased against non-native English writers. Patterns, 4(7). Data: https://github.com/Weixin-Liang/ChatGPT-Detector-Bias (MIT).
