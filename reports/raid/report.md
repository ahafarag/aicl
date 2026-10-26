# Detector report card: RAID sample

Generated 2026-10-26 with aicl 0.1.0 (seed 0). 984 documents: 60 human-written, 924 machine-generated. 30 human texts were held out for calibration.

## Separability (evaluation split)

| Detector | What it scores | AUROC (95% CI) | Scored |
|---|---|---:|---:|
| binoculars | Binoculars, gpt2/distilgpt2, uncalibrated | 0.862 (0.833–0.888) | 984 |
| perplexity | Low perplexity under gpt2 | 0.828 (0.785–0.868) | 984 |
| gltr-top10 | GLTR top-10 rank share under gpt2 | 0.808 (0.760–0.851) | 984 |
| stock-phrases | Stock-phrase density (baseline) | 0.507 (0.431–0.575) | 984 |
| low-sentence-cv | Low sentence-length CV (baseline) | 0.693 (0.631–0.754) | 984 |

## Flag rates at a threshold calibrated to 5% false positives

Each detector's threshold was set on the held-out human texts so that at most 5% of them were flagged. Rows show the share of each evaluation group flagged as machine-generated, with Wilson 95% intervals.

| Group | Kind | binoculars | perplexity | gltr-top10 | stock-phrases | low-sentence-cv |
|---|---|---:|---:|---:|---:|---:|
| human: abstracts | human → false positives | 0% (0%–28%) | 0% (0%–28%) | 0% (0%–28%) | 0% (0%–28%) | 10% (2%–40%) |
| human: books | human → false positives | 10% (2%–40%) | 0% (0%–28%) | 0% (0%–28%) | 0% (0%–28%) | 0% (0%–28%) |
| human: news | human → false positives | 10% (2%–40%) | 10% (2%–40%) | 0% (0%–28%) | 0% (0%–28%) | 0% (0%–28%) |
| model: gpt2 | machine → detected | 85% (74%–92%) | 83% (72%–91%) | 73% (61%–83%) | 0% (0%–6%) | 13% (7%–24%) |
| model: gpt3 | machine → detected | 97% (89%–99%) | 83% (72%–91%) | 78% (66%–87%) | 0% (0%–6%) | 25% (16%–37%) |
| model: chatgpt | machine → detected | 95% (86%–98%) | 82% (70%–89%) | 62% (49%–73%) | 18% (11%–30%) | 50% (38%–62%) |
| model: gpt4 | machine → detected | 65% (52%–76%) | 55% (42%–67%) | 37% (26%–49%) | 2% (0%–9%) | 25% (16%–37%) |
| model: cohere | machine → detected | 68% (56%–79%) | 55% (42%–67%) | 50% (38%–62%) | 0% (0%–6%) | 17% (9%–28%) |
| model: cohere-chat | machine → detected | 83% (72%–91%) | 75% (63%–84%) | 62% (49%–73%) | 0% (0%–6%) | 37% (26%–49%) |
| model: llama-chat | machine → detected | 93% (84%–97%) | 92% (82%–96%) | 87% (76%–93%) | 0% (0%–6%) | 27% (17%–39%) |
| model: mistral | machine → detected | 63% (51%–74%) | 45% (33%–58%) | 42% (30%–54%) | 0% (0%–6%) | 12% (6%–22%) |
| model: mistral-chat | machine → detected | 88% (78%–94%) | 90% (80%–95%) | 75% (63%–84%) | 3% (1%–11%) | 37% (26%–49%) |
| model: mpt | machine → detected | 47% (35%–59%) | 37% (26%–49%) | 32% (21%–44%) | 0% (0%–6%) | 17% (9%–28%) |
| model: mpt-chat | machine → detected | 58% (46%–70%) | 57% (44%–68%) | 38% (27%–51%) | 17% (9%–28%) | 35% (24%–48%) |
| attack: paraphrase | machine → detected | 92% (83%–97%) | 44% (33%–56%) | 36% (26%–48%) | 0% (0%–6%) | 18% (11%–29%) |
| attack: synonym | machine → detected | 56% (44%–67%) | 29% (19%–41%) | 21% (13%–33%) | 0% (0%–6%) | 35% (24%–47%) |
| attack: homoglyph | machine → detected | 98% (92%–100%) | 39% (29%–51%) | 18% (11%–29%) | 0% (0%–6%) | 30% (21%–42%) |
| attack: whitespace | machine → detected | 47% (35%–59%) | 36% (26%–48%) | 47% (35%–59%) | 3% (1%–10%) | 21% (13%–33%) |

## How to read this

- AUROC is the probability that a randomly chosen machine text scores higher than a randomly chosen human text. 0.5 is chance.
- A low overall false-positive rate can hide a high rate for one group. Compare the human rows.
- Small groups have wide intervals. Do not rank detectors whose intervals overlap.
- Protocol: docs/report_card.md. Reproduce with the command in that document.

## Sources

- Dugan, L., et al. (2024). RAID: A shared benchmark for robust evaluation of machine-generated text detectors. ACL. Data: https://huggingface.co/datasets/liamdugan/raid (MIT).
