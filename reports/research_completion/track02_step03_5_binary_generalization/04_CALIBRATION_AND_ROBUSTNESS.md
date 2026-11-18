# TrustRAG — Track 2, Step 3.5: Probability Calibration & Robustness Analysis

## 1. Probability Calibration

- **Combined Brier Score:** **0.1772** (Reference: random guessing at 0.5 is 0.2500)
- **Combined ECE (10 Equal Bins):** **0.1540**
- **HaluEval Calibration:** Brier = 0.0574, ECE = 0.2008 (Highly calibrated)
- **RAGTruth Calibration:** Brier = 0.2970, ECE = 0.2541 (Under-confident on hallucinations)

---

## 2. Confidence Distribution Analysis

| Subset | Sample Count | Mean Confidence | Median Confidence | P95 Confidence |
| :--- | :---: | :---: | :---: | :---: |
| **All Predictions** | 1000 | 78.11% | 80.77% | 85.32% |
| **Correct Predictions** | 766 | 78.59% | 81.02% | — |
| **Incorrect Predictions** | 234 | 76.56% | 80.47% | — |

---

## 3. Robustness Against Domain and Distribution Shift

1. **Format Shift:** Concise contrastive QA (HaluEval) achieves 98.80% accuracy, while multi-sentence RAG output (RAGTruth) achieves 54.40%.
2. **Fixed Decision Boundary:** The default 0.5 decision boundary (argmax) was maintained strictly without retrospective post-hoc tuning.
3. **Context Length Bottleneck:** The 128-token context truncation bottleneck is the primary driver of false negatives on long-form generation tasks.
