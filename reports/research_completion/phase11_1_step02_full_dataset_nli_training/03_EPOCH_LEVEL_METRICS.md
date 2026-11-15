# TrustRAG — Phase 11.1, Step 2: Full-Dataset NLI Training Audit
## 03 — Epoch-Level Metrics (Execution Blocked)

- **Audit Date:** 2026-11-14T18:25:00Z
- **Auditor:** Senior ML Training Engineer & Independent Experimental Auditor

---

### 1. Epoch-Level Progression Status

Because the run was halted during mandatory preflight gates prior to executing any backward pass or optimizer step, zero training epochs were performed.

| Epoch | Status | Optimizer Steps | Train Loss | Val Loss | Val Acc | Val Macro F1 | Val Contradiction Recall | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Step 0 Baseline** | NOT EXECUTED | 0 | N/A | N/A | N/A | N/A | N/A | Preflight Blocked |
| **Epoch 1** | NOT EXECUTED | 0 | N/A | N/A | N/A | N/A | N/A | Preflight Blocked |
| **Epoch 2** | NOT EXECUTED | 0 | N/A | N/A | N/A | N/A | N/A | Preflight Blocked |
| **Epoch 3** | NOT EXECUTED | 0 | N/A | N/A | N/A | N/A | N/A | Preflight Blocked |

---

### 2. Historical Baseline Reference

For context and comparison, the audited metrics from prior historical runs on the 2,662 validation set are preserved below:

- **Step 0 Unadapted Model Baseline (Step 3.16):**
  - Accuracy: **24.19%** (All 2,662 samples predicted as NEUTRAL)
  - Balanced Accuracy: 33.33%
  - Macro F1: 0.1299
  - Contradiction Recall: **0.00%**
- **Step 3.8 Degenerate Collapsed Run (1,000 steps, unweighted):**
  - Accuracy: **24.12%**
  - Balanced Accuracy: 36.08%
  - Macro F1: 0.1920
  - Contradiction Recall: 19.10% (68/356)
  - Entailment Recall: **0.00%** (0/1,662)
- **Step 3.16 Remediated Pilot (1,000 steps, balanced sampler):**
  - Accuracy: **38.05%**
  - Balanced Accuracy: 35.44%
  - Macro F1: 0.2975
  - Entailment Recall: 33.51% (557/1,662)
  - Contradiction Recall: **4.49%** (16/356)
  - Neutral Recall: 68.32% (440/644)

