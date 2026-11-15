# TrustRAG — Track 2, Step 3.5: Comparative Evaluation Metrics by Dataset

## 1. Primary Metrics Table

| Metric | Combined Evaluation (N=1,000) | HaluEval Benchmark (N=500) | RAGTruth Benchmark (N=500) |
| :--- | :---: | :---: | :---: |
| **Total Evaluated Records** | 1,000 | 500 | 500 |
| **True FACTUAL (Class 0)** | 500 | 250 | 250 |
| **True HALLUCINATED (Class 1)**| 500 | 250 | 250 |
| **Accuracy** | **76.60%** | **98.80%** | **54.40%** |
| **95% Wilson CI** | [73.88%, 79.12%] | [97.41%, 99.45%] | [50.02%, 58.72%] |
| **95% Bootstrap CI** | [74.10%, 79.20%] | [97.80%, 99.60%] | [50.00%, 58.60%] |
| **Balanced Accuracy** | **76.60%** | **98.80%** | **54.40%** |
| **Macro F1 Score** | **0.7583** | **0.9880** | **0.4812** |
| **Macro F1 95% Bootstrap CI** | [0.7322, 0.7848] | [0.9779, 0.9960] | [0.4370, 0.5237] |

---

## 2. Per-Class Precision, Recall, and F1

### Combined (N=1,000)
- **FACTUAL (Class 0):** Precision = 69.62%, Recall = 94.40%, F1 = 0.8014 (Support: 500)
- **HALLUCINATED (Class 1):** Precision = 91.30%, Recall = 58.80%, F1 = 0.7153 (Support: 500)

### HaluEval (N=500)
- **FACTUAL (Class 0):** Precision = 98.03%, Recall = 99.60%, F1 = 0.9881 (Support: 250)
- **HALLUCINATED (Class 1):** Precision = 99.59%, Recall = 98.00%, F1 = 0.9879 (Support: 250)

### RAGTruth (N=500)
- **FACTUAL (Class 0):** Precision = 52.59%, Recall = 89.20%, F1 = 0.6617 (Support: 250)
- **HALLUCINATED (Class 1):** Precision = 64.47%, Recall = 19.60%, F1 = 0.3006 (Support: 250)

---

## 3. Discrimination and Calibration Metrics

| Metric | Combined | HaluEval | RAGTruth |
| :--- | :---: | :---: | :---: |
| **ROC-AUC** | **0.9178** | **0.9910** | **0.7197** |
| **PR-AUC (Hallucinated)** | **0.9219** | **0.9938** | **0.7020** |
| **Brier Score** | **0.1772** | **0.0574** | **0.2970** |
| **Expected Calibration Error (ECE)** | **0.1540** | **0.2008** | **0.2541** |
