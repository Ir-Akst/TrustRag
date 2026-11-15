# TrustRAG — Track 2, Step 3.10: Unit Test Results

## 1. Test Suite Summary

- **Test Suite:** `tests/unit/test_track02_step03_6_nli_training_runner.py`
- **Total Test Cases:** 28 tests (21 baseline + 7 remediation tests).
- **Passed:** **28 / 28 (100%)**
- **Failed:** 0
- **Execution Environments:**
  1. Primary pytest runner (`/home/aditya/rags/.venv/bin/pytest`)
  2. PyTorch runtime validation (`/home/aditya/rags/.venv-train/bin/python`)

---

## 2. Granular Test Breakdown

| Category | Test Function | Purpose / Assertion | Status |
| :--- | :--- | :--- | :---: |
| **Sampling & Shuffling** | `test_deterministic_shuffling_reproducibility` | Same seed yields identical order; diff seeds yield diff order; exact quotas | **PASS** |
| **Sampling & Shuffling** | `test_shuffled_order_breaks_sequential_tail` | Confirms tail is thoroughly mixed; eliminates class grouping | **PASS** |
| **Starvation Guard** | `test_class_starvation_detection_violation` | Asserts `ClassStarvationError` triggers on 30-step absence | **PASS** |
| **Starvation Guard** | `test_class_starvation_clean_on_shuffled_sequence`| Asserts balanced sequence passes with max absence $\le 3$ | **PASS** |
| **Evidence Preservation**| `test_evidence_preserving_tokenization_hypothesis_priority`| Verifies 100% hypothesis retention when budget allows | **PASS** |
| **Evidence Preservation**| `test_evidence_preserving_tokenization_long_hypothesis_safeguard`| Guarantees minimum premise tokens on long hypotheses | **PASS** |
| **Checkpoint Protection**| `test_save_checkpoint_atomic_protected_nli_pilot1000_overwrite_rejection`| Asserts `SecurityViolationError` on Step 3.8 checkpoint overwrite | **PASS** |
| **Checkpoint Protection**| `test_save_checkpoint_atomic_protected_overwrite_rejection`| Asserts `SecurityViolationError` on binary checkpoint overwrite | **PASS** |
| **Security & Isolation**| `test_execute_training_unauthorized_rejection` | Asserts `TrainingNotAuthorizedError` when `authorized=False` | **PASS** |
| **Security & Isolation**| `test_load_nli_dataset_test_set_rejection` | Asserts `SecurityViolationError` on test file targeting | **PASS** |
| **Security & Isolation**| `test_verify_split_isolation_leakage_detection` | Asserts `SecurityViolationError` on overlapping IDs | **PASS** |
| **Architecture** | `test_prepare_nli_model_architecture` | Confirms 141.9M params, 3 classes, FP32 precision | **PASS** |
| **Watchdogs** | `test_watchdog_abort_on_ram_depletion` | Asserts `ResourceAbortError` when RAM drops below 700 MB | **PASS** |
| **Watchdogs** | `test_watchdog_abort_on_swap_growth` | Asserts `ResourceAbortError` when swap grows beyond threshold | **PASS** |
| **Watchdogs** | `test_watchdog_abort_on_timeout` | Asserts `TimeoutAbortError` on wall-clock breach | **PASS** |
