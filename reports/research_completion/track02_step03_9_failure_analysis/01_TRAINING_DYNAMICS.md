# TrustRAG — Track 2, Step 3.9: Training Dynamics Reconstruction

## 1. Execution Log Verification

- **Total Authorized Steps:** 1,000 optimizer steps (1 sample per step, batch size 1).
- **Optimizer:** PyTorch `torch.optim.AdamW(lr=2e-5, weight_decay=0.01, betas=(0.9, 0.999), eps=1e-8)`.
- **Learning Rate Schedule:** Linear warmup over 100 steps ($0 \to 2\times 10^{-5}$), followed by linear decay over remaining 900 steps ($2\times 10^{-5} \to 0$).
- **Gradient Clipping:** `torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)`.
- **Execution Wall-Clock Time:** 2,414.2 seconds (~40.2 minutes) for Step 0 eval + 1,000 steps + Step 1,000 eval.

---

## 2. Step-by-Step Training Telemetry & Loss Trajectory

| Step Range | Mean Rolling Loss | Step LR | Observed RSS | Available RAM |
| :---: | :---: | :---: | :---: | :---: |
| **Step 1** | 1.1087 | 0.00e+00 | 2,172.0 MB | 6,205.9 MB |
| **Step 50** | 1.1364 | 9.80e-06 | 2,401.8 MB | 3,745.2 MB |
| **Step 100 (Peak LR)** | 1.0892 | 1.98e-05 | 2,402.1 MB | 4,582.2 MB |
| **Step 150** | 1.1020 | 1.89e-05 | 2,318.5 MB | 4,327.6 MB |
| **Step 200** | 1.1805 | 1.78e-05 | 2,408.9 MB | 4,198.6 MB |
| **Step 250** | 0.9993 | 1.67e-05 | 2,392.4 MB | 4,238.8 MB |
| **Step 300** | 1.1161 | 1.56e-05 | 2,381.9 MB | 4,242.3 MB |
| **Step 350** | 1.7085 | 1.45e-05 | 2,406.6 MB | 4,650.9 MB |
| **Step 400** | 1.4246 | 1.34e-05 | 2,414.9 MB | 4,730.1 MB |
| **Step 450** | 1.0806 | 1.22e-05 | 2,425.4 MB | 4,673.9 MB |
| **Step 500** | 1.7154 | 1.11e-05 | 2,415.6 MB | 4,682.2 MB |
| **Step 550** | 1.5057 | 1.00e-05 | 2,375.9 MB | 4,685.9 MB |
| **Step 600** | 1.5036 | 8.91e-06 | 2,390.1 MB | 4,702.4 MB |
| **Step 650** | 1.0961 | 7.80e-06 | 2,367.6 MB | 4,705.0 MB |
| **Step 700** | 1.5495 | 6.69e-06 | 2,394.6 MB | 4,502.4 MB |
| **Step 750** | 2.0389 | 5.58e-06 | 2,395.0 MB | 4,385.3 MB |
| **Step 800** | 1.5662 | 4.47e-06 | 2,407.8 MB | 4,319.5 MB |
| **Step 850** | 0.8828 | 3.36e-06 | 2,409.3 MB | 4,319.6 MB |
| **Step 900** | 0.7761 | 2.24e-06 | 2,406.6 MB | 4,280.2 MB |
| **Step 950** | 0.6955 | 1.13e-06 | 2,399.9 MB | 4,417.3 MB |
| **Step 1000** | 1.5756 | 2.22e-08 | 2,406.6 MB | 4,532.6 MB |

---

## 3. Class Distribution Across Optimization Timeline

Forensic reconstruction of the sampled batch list (`train_records`) across 100-step blocks reveals the critical imbalance progression:

```
Steps   0- 99: ENTAILMENT=47, CONTRADICTION=34, NEUTRAL=19
Steps 100-199: ENTAILMENT=42, CONTRADICTION=27, NEUTRAL=31
Steps 200-299: ENTAILMENT=55, CONTRADICTION=18, NEUTRAL=27
Steps 300-399: ENTAILMENT=38, CONTRADICTION=28, NEUTRAL=34
Steps 400-499: ENTAILMENT=51, CONTRADICTION=22, NEUTRAL=27
Steps 500-599: ENTAILMENT=47, CONTRADICTION=25, NEUTRAL=28
Steps 600-699: ENTAILMENT=51, CONTRADICTION=25, NEUTRAL=24
------------------------------------------------------------
Steps 700-705: ENTAILMENT= 3, CONTRADICTION= 2, NEUTRAL= 1   <-- ENTAILMENT TARGET (334) REACHED
Steps 706-799: ENTAILMENT= 0, CONTRADICTION=37, NEUTRAL=57
Steps 800-899: ENTAILMENT= 0, CONTRADICTION=50, NEUTRAL=50
Steps 900-999: ENTAILMENT= 0, CONTRADICTION=65, NEUTRAL=35
```

**Observation:** For the last 295 optimization steps, the model was updated exclusively on CONTRADICTION and NEUTRAL. No gradient pull in favor of ENTAILMENT was applied after step 705.
