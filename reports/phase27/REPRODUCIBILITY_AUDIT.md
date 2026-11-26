# Phase 27 — Reproducibility Audit

---

## 1. Audit Checklist & Verification

| Requirement | Audit Finding | Status |
| :--- | :--- | :--- |
| **Deterministic Random Seeds** | Evaluation scripts fix `random.seed(42)` and `numpy.random.seed(42)` for sample generation and partitioning. | PASSED |
| **Hardware Agnosticism** | Evaluated on CPU architecture without requiring specialized GPU hardware for G1/G2 baseline reproduction. | PASSED |
| **Frozen Checkpoint Immutability** | All 8 checkpoint files match their original release commit SHA-256 checksums. | PASSED |
| **Raw Prediction Preservation** | Complete raw prediction records for 1,000 Phase 26 samples are archived in `reports/phase26/raw_predictions/phase26_raw_predictions.jsonl`. | PASSED |
| **Single-Command Execution** | Standalone benchmark scripts can be executed via clean CLI invocations. | PASSED |
| **Environment Documentation** | Python 3.10 virtual environment dependencies are specified in `research/reproducibility/README.md`. | PASSED |

---

## 2. Verification Protocol

Independent researchers can reproduce the headline findings by following the 4-step protocol in `research/reproducibility/README.md`:
1. Verify checkpoint hashes.
2. Run `python tools/evaluation/run_phase26_generalization_benchmark.py`.
3. Compute metrics using the standalone evaluation script.
4. Confirm 71.80% ADR and 0.00% FPR within Wilson 95% confidence intervals.
