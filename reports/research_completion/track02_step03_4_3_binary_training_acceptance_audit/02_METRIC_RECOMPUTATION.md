# Track 2, Step 3.4.3 — Section 02: Metric Recomputation and Audit

## 1. Independent Metric Recomputation

The trained checkpoint was evaluated across the 200 validation records from `data/processed/sft_v2/binary/validation.jsonl` using inference-only execution. All reported metrics were recomputed and compared:

| Metric | Reported Value (Step 3.4.2) | Recomputed Value (Audit) | Discrepancy |
|--------|:---------------------------:|:------------------------:|:-----------:|
| **Validation Loss** | `0.5535` | `0.5535` | **0.0000** |
| **Accuracy** | `0.7600` (76.00%) | `0.7600` (76.00%) | **0.0000** |
| **Balanced Accuracy** | `0.7600` (76.00%) | `0.7600` (76.00%) | **0.0000** |
| **Macro F1 Score** | `0.7500` | `0.7500` | **0.0000** |
| **Class 0 (Factual) Precision** | `0.6857` (68.57%) | `0.6857` (68.57%) | **0.0000** |
| **Class 0 (Factual) Recall** | `0.9600` (96.00%) | `0.9600` (96.00%) | **0.0000** |
| **Class 0 (Factual) F1** | `0.8000` | `0.8000` | **0.0000** |
| **Class 1 (Hallu) Precision** | `0.9333` (93.33%) | `0.9333` (93.33%) | **0.0000** |
| **Class 1 (Hallu) Recall** | `0.5600` (56.00%) | `0.5600` (56.00%) | **0.0000** |
| **Class 1 (Hallu) F1** | `0.7000` | `0.7000` | **0.0000** |

---

## 2. Confusion Matrix Reproduction

The independent audit produced the exact confusion matrix:

| Actual \ Predicted | FACTUAL (Pred 0) | HALLUCINATED (Pred 1) | Total Actual |
|---------------------|:----------------:|:---------------------:|:------------:|
| **FACTUAL (Actual 0)** | **96** ($TN$) | **4** ($FP$) | **100** |
| **HALLUCINATED (Actual 1)** | **44** ($FN$) | **56** ($TP$) | **100** |
| **Total Predicted** | **140** | **60** | **200** |

- True Negatives ($TN$): **96** (96% specificity on factual content).
- True Positives ($TP$): **56** (56% sensitivity on hallucinations).
- False Positives ($FP$): **4** (only 4% false alarm rate).
- False Negatives ($FN$): **44**.

---

## 3. Training Loss Progression Verification

Supporting values from `training_results.json`:
- Initial Training Loss (Step 1): `0.5788`
- Final Training Loss (Step 1,000): `0.2144`
- Overall Average Training Loss: `0.5065`
- Step 0 Baseline Validation Loss: `0.6973`
- Step 1,000 Final Validation Loss: `0.5535`
