# Statistical Recalculation & Wilson 95% Confidence Intervals

All Phase 39 percentages and two-sided 95% Wilson confidence intervals ($z = 1.959964$) were recomputed directly from raw JSONL prediction files under `reports/phase39/raw_predictions/`:

1. **G1 ADR:** $74 / 250 = 29.60\%$ [24.28%, 35.53%] | **ASR:** $176 / 250 = 70.40\%$ [64.47%, 75.72%] | **FPR:** $0 / 80 = 0.00\%$ [0.00%, 4.58%]
2. **Firewall Detection Recall:** $50 / 110 = 45.45\%$ [36.46%, 54.76%] | **Generator Leakage:** $60 / 110 = 54.55\%$ [45.24%, 63.54%] | **False Quarantine:** $0 / 50 = 0.00\%$ [0.00%, 7.13%]
3. **Multilingual Overall ADR:** $160 / 270 = 59.26\%$ [53.31%, 64.95%] | **Unseen Translit ADR:** $26 / 90 = 28.89\%$ [20.54%, 38.96%] | **FPR:** $2 / 90 = 2.22\%$ [0.61%, 7.74%]
4. **G3 Gate Accuracy:** $129 / 140 = 92.14\%$ [86.48%, 95.56%] | **Supported Acceptance:** $29 / 35 = 82.86\%$ [67.32%, 91.90%] | **Contradiction Recall:** $55 / 70 = 78.57\%$ [67.61%, 86.56%] | **Unsupported Leakage:** $0 / 20 = 0.00\%$ [0.00%, 16.11%]
