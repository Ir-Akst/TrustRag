# TrustRAG — Track 2, Step 3.9: Independent Metric Revalidation

## 1. Recomputation from Raw Validation Predictions ($N=2,662$)

Independent metric recomputation was executed directly against `training_results.json` and the Step 3.8 model checkpoint:

### 3×3 Confusion Matrix
```
                   Pred ENTAILMENT    Pred CONTRADICTION    Pred NEUTRAL    Total True
True ENTAILMENT            0                   251                1411          1,662
True CONTRADICTION         0                    68                 288            356
True NEUTRAL               0                    70                 574            644
Total Pred                 0                   389               2,273          2,662
```

### Per-Class Detailed Performance
| Class Index | Label | TP | FP | FN | Support | Precision | Recall | F1 Score |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | **ENTAILMENT** | 0 | 0 | 1,662 | 1,662 | 0.0000 | 0.0000 | **0.0000** |
| **1** | **CONTRADICTION** | 68 | 321 | 288 | 356 | 0.1748 | 0.1910 | **0.1826** |
| **2** | **NEUTRAL** | 574 | 1,699 | 70 | 644 | 0.2525 | 0.8913 | **0.3936** |

### Macro & Aggregate Metrics
- **Accuracy:** $\frac{0 + 68 + 574}{2662} = \frac{642}{2662} =$ **24.1172%** (Reported: 24.12%)
- **Balanced Accuracy:** $\frac{0.0 + 0.191011 + 0.891304}{3} =$ **36.0772%** (Reported: 36.08%)
- **Macro F1 Score:** $\frac{0.0 + 0.182550 + 0.393555}{3} =$ **0.192035** (Reported: 0.1920)
- **Weighted F1 Score:** $\frac{0.0\times 1662 + 0.182550\times 356 + 0.393555\times 644}{2662} =$ **0.119623** (Reported: 0.1196)
- **Validation Cross-Entropy Loss:** **2.4507**
- **Brier Score:** **1.1491**
- **Expected Calibration Error (ECE, 10 bins):** **0.5180**

**Audit Verdict:** Step 3.8 metrics are 100% mathematically correct and reproducible.
