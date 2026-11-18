# TrustRAG — Track 2, Step 3.8: Validation Results on Original Imbalanced Partition

## 1. 3×3 Confusion Matrix

### Step 0 Baseline (Pre-Training)
```
                  Pred ENTAILMENT    Pred CONTRADICTION    Pred NEUTRAL
True ENTAILMENT            0                     0                1662
True CONTRADICTION         0                     0                 356
True NEUTRAL               0                     0                 644
```

### Step 1,000 Final (Post-Training)
```
                  Pred ENTAILMENT    Pred CONTRADICTION    Pred NEUTRAL
True ENTAILMENT            0                   251                1411
True CONTRADICTION         0                    68                 288
True NEUTRAL               0                    70                 574
```

---

## 2. Comprehensive Metric Summary (N=2,662)

| Metric | Step 0 Baseline | Step 1,000 Final | Majority Class Baseline |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 24.19% | **24.12%** | 62.43% |
| **Balanced Accuracy** | 33.33% | **36.08%** | 33.33% |
| **Macro F1** | 0.1299 | **0.1920** | 0.2562 |
| **Weighted F1** | 0.0943 | **0.1196** | 0.4800 |
| **Brier Score** | 0.6639 | **1.1491** | — |
| **ECE (10 bins)** | 0.1524 | **0.5180** | — |
