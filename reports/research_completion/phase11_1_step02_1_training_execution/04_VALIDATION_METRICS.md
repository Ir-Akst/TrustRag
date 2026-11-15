# TrustRAG — Phase 11.1, Step 2.1: Validation Metrics & Baseline Evaluation

## 1. Step 0 Pre-Training Baseline Evaluation

Prior to training, the freshly initialized DeBERTa-v3-small 3-class sequence classification model was evaluated against the complete, unmanipulated validation split (`data/processed/sft_v2/nli/validation.jsonl`, 2,662 samples). 

Both execution attempts (`task-9745` and `task-9774`) yielded identical, deterministic baseline performance.

### 1.1 Summary Aggregate Metrics

| Metric | Measured Value | Pre-Registered Target | Target Status |
| :--- | :---: | :---: | :---: |
| **Validation Loss** | 1.08834 | $\le 0.8500$ | Unmet (Untrained) |
| **Overall Accuracy** | 24.19% (644 / 2,662) | $\ge 65.00\%$ | Unmet (Untrained) |
| **Balanced Accuracy** | 33.33% | $\ge 65.00\%$ | Unmet (Untrained) |
| **Macro F1** | 0.12986 | $\ge 0.6500$ | Unmet (Untrained) |
| **Weighted F1** | 0.09425 | — | — |
| **Contradiction Recall** | 0.00% (0 / 356) | $\ge 65.00\%$ | Unmet (Untrained) |
| **Brier Score** | 0.66293 | $\le 0.3500$ | Unmet (Untrained) |
| **ECE-10 (Calibration)**| 0.15180 | $\le 0.1000$ | Unmet (Untrained) |

---

## 2. Per-Class Performance Breakdown (Step 0 Baseline)

| Class | Support | True Positives | Predicted Count | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`ENTAILMENT`** | 1,662 | 0 | 0 | 0.00% | 0.00% | 0.0000 |
| **`CONTRADICTION`** | 356 | 0 | 0 | 0.00% | 0.00% | 0.0000 |
| **`NEUTRAL`** | 644 | 644 | 2,662 | 24.19% | 100.00% | 0.3896 |
| **Macro Average** | — | — | — | 8.06% | 33.33% | **0.1299** |

---

## 3. Post-Training Validation Status

Because training was halted at Step 325 by the watchdog memory growth cutoff prior to completing Epoch 1 (which required 2,704 steps), no post-training validation pass was reached. Consequently:
- **Final Macro F1:** N/A (Run terminated mid-epoch)
- **Final Contradiction Recall:** N/A
- **Final ECE-10:** N/A
- **Checkpoint Persistence:** No post-training checkpoint saved.

All baseline targets remain unmet due to premature process termination.

