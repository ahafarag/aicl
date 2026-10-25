---
title: Would an AI detector flag your writing?
emoji: 🔍
colorFrom: indigo
colorTo: green
sdk: static
app_file: index.html
pinned: true
license: mit
short_description: See what AI detectors react to. Runs in your browser.
---

# Would an AI detector flag your writing?

Paste a text to see:

- **Three open detectors** (Binoculars, perplexity, GLTR), each calibrated to wrongly flag at most 5% of a pool of human essays, and whether they would flag yours.
- **Where your text sits** among real human essays (TOEFL essays by non-native writers, US 8th-grade essays) and GPT-3.5 essays, for six signals.
- **A word-level heatmap** of how predictable each token was to gpt2.

Everything runs in your browser with [transformers.js](https://github.com/huggingface/transformers.js), so your text never leaves your device. Nothing here proves who wrote a text. The page shows why detectors misjudge careful, plain human writing, especially by non-native English writers.

Code, methods and the full detector report card: https://github.com/ahafarag/aicl

Reference data: Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J. (2023). *GPT detectors are biased against non-native English writers.* Patterns, 4(7). Only aggregate statistics are bundled, plus one example essay from their MIT-licensed dataset.
