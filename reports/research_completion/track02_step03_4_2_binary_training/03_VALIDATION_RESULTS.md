# Track 2, Step 3.4.2 — Section 03: Validation Results & Evaluation

## 1. Validation Performance Comparison

Evaluated on the exact 200-sample balanced validation subset (100 FACTUAL, 100 HALLUCINATED):

| Metric | Step 0 (Untrained Baseline) | Step 1,000 (Trained Model) | Net Change |
|--------|:---------------------------:|:--------------------------:|:----------:|
| **CrossEntropy Loss** | `0.6973` | `0.5535` | **-0.1438** |
| **Accuracy** | `50.00%` | `76.00%` | **+26.00%** |
| **Balanced Accuracy** | `50.00%` | `76.00%` | **+26.00%** |
| **Macro Precision** | `25.00%` | `80.95%` | **+55.95%** |
| **Macro Recall** | `50.00%` | `76.00%` | **+26.00%** |
| **Macro F1** | `0.3333` | `0.7500` | **+0.4167** |

---

## 2. Confusion Matrix Analysis (Step 1,000)

```
                       Actual Class
                    FACTUAL    HALLUCINATED
Predicted FACTUAL      96           44         (Total Predicted Factual = 140)
Predicted HALLU         4           56         (Total Predicted Hallu   = 60)
                     ------       ------
Actual Total          100          100         (Total = 200)
```

- **True Negatives ($TN$ - Factual correctly identified):** **96 / 100** (96.0% specificity).
- **True Positives ($TP$ - Hallucination correctly caught):** **56 / 100** (56.0% sensitivity).
- **False Positives ($FP$ - Factual falsely flagged as hallucination):** **Only 4 / 100** (4.0% false alarm rate).
- **False Negatives ($FN$ - Hallucination missed):** **44 / 100**.

---

## 3. Per-Class Performance Breakdown

### Class 0: `FACTUAL` (100 samples)
- **Precision:** $rac{96}{96 + 44} = \mathbf{68.57\%}$
- **Recall:** $rac{96}{100} = \mathbf{96.00\%}$
- **F1 Score:** $\mathbf{0.8000}$

### Class 1: `HALLUCINATED` (100 samples)
- **Precision:** $rac{56}{56 + 4} = \mathbf{93.33\%}$
- **Recall:** $rac{56}{100} = \mathbf{56.00\%}$
- **F1 Score:** $\mathbf{0.7000}$

### Engineering Interpretation:
The model developed a **high-precision hallucination filter**. When the fine-tuned model predicts that a response is `HALLUCINATED`, it is correct **93.33% of the time**. It preserves 96.0% of factual statements while filtering out more than half of all hallucinations after just 1 epoch of 1,000 examples.
