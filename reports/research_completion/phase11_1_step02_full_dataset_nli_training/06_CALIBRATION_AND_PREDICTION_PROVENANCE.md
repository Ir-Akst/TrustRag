# TrustRAG — Phase 11.1, Step 2: Full-Dataset NLI Training Audit
## 06 — Calibration & Prediction Provenance

- **Audit Date:** 2026-11-14T18:25:00Z
- **Auditor:** Senior ML Training Engineer & Reproducibility Engineer

---

### 1. Mandatory Prediction Artifact Status

The authorization mandated generating a per-sample prediction file:
- File Name: `predictions_val.jsonl`
- Required Fields per Record: `example_id`, `true_label`, `pred_label`, `logits`, `probs [p0, p1, p2]`, `model_id`, `label_mapping`.
- **Status:** **NOT GENERATED** (No model training or inference executed).

---

### 2. Calibration Metrics Status

| Calibration Metric | Pre-Registered Standard | Achieved Status | Verification Method |
| :--- | :--- | :--- | :--- |
| **ECE-10 (10-Bin Calibration Error)** | $\le 0.100$ | **N/A** | Blocked preflight |
| **Brier Score (Multi-Class)** | Lower is better | **N/A** | Blocked preflight |
| **Reliability Diagram** | Monotonic diagonal | **N/A** | Blocked preflight |
| **Selective Risk-Coverage Curve** | Monotonic decreasing | **N/A** | Blocked preflight |

---

### 3. Harness Gap Identified for Future Implementation

The existing `tools/training/train_nli_classifier.py` currently accumulates predictions in memory and discards sample-level probability vectors at line 521. In the upcoming Step 2.1 harness update, `evaluate()` must be explicitly modified to serialize `predictions_val.jsonl` directly to disk during the final validation pass.

