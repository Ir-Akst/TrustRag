# TrustRAG — Track 2, Step 3.11: Test Suite & Authorization Safety Audit

## 1. Test Suite Independent Execution

The unit test suite in `tests/unit/test_track02_step03_6_nli_training_runner.py` was executed independently across both environments:

### Environment 1: Primary pytest (`.venv`, Python 3.14)
```text
tests/unit/test_track02_step03_6_nli_training_runner.py ........................ [100%]
======================== 27 passed, 1 skipped in 0.05s =========================
```
*(1 test skipped due to torch not being present in `.venv`)*

### Environment 2: PyTorch Training Runtime (`.venv-train`, Python 3.10)
```text
Running 28 tests with PyTorch runtime...
ALL 28 TESTS PASSED SUCCESSFULLY IN PYTORCH ENVIRONMENT!
```
*(All 28 tests passed including `test_prepare_nli_model_architecture`)*

---

## 2. Authorization Guard & Safety Tests Audit

- **Execution Authorization Guard:**
  `test_execute_training_unauthorized_rejection` confirms that `execute_training` strictly raises `TrainingNotAuthorizedError` when `authorized=False`.
- **Protected Checkpoint Immutability Guard:**
  `test_save_checkpoint_atomic_protected_overwrite_rejection` and `test_save_checkpoint_atomic_protected_nli_pilot1000_overwrite_rejection` confirm that attempts to overwrite `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` or `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000` immediately raise `SecurityViolationError`.
- **Split Isolation Guard:**
  `test_verify_split_isolation_id_leakage` and `test_verify_split_isolation_premise_leakage` confirm zero ID or premise contamination between train and validation splits.
