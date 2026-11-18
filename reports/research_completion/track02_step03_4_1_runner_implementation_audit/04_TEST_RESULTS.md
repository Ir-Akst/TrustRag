# Track 2, Step 3.4.1 — Section 04: Non-Training Test Suite Verification

## 1. Test Suite Overview

Test file: [tests/unit/test_track02_step03_4_1_binary_training_runner.py](file:///home/aditya/rags/TrustRag-phase11/tests/unit/test_track02_step03_4_1_binary_training_runner.py)  
Execution command: `pytest -v tests/unit/test_track02_step03_4_1_binary_training_runner.py`  
Test Execution Time: **0.07 seconds**  
Result: **20 passed / 20 total (100% PASS)**  

---

## 2. Test Breakdown by Category

### A. Schema & Serialization (6 tests)
- `test_validate_dataset_record_valid`: PASSED (validates mandatory fields).
- `test_validate_dataset_record_missing_field`: PASSED (catches missing fields).
- `test_validate_dataset_record_invalid_label`: PASSED (rejects non-binary labels like 'NEUTRAL').
- `test_validate_dataset_record_rejects_test_split`: PASSED (rejects split='test').
- `test_label_mapping`: PASSED (verifies FACTUAL=0, HALLUCINATED=1).
- `test_serialize_binary_input`: PASSED (verifies Text A / Text B serialization without NLI terms).

### B. Deterministic Sampling & Leakage (5 tests)
- `test_stratified_sampling`: PASSED (verifies exact 50/50 source and 50/50 class balance).
- `test_sequential_sampling`: PASSED (verifies sequential order).
- `test_load_dataset_rejects_test_file`: PASSED (blocks test set loading).
- `test_verify_split_isolation_clean`: PASSED (permits isolated splits).
- `test_verify_split_isolation_leakage`: PASSED (catches and rejects ID overlap).

### C. Safety Watchdogs (5 tests)
- `test_watchdog_normal_operation`: PASSED (telemetry tracks within limits).
- `test_watchdog_abort_on_low_ram`: PASSED (triggers abort at 650 MB available RAM).
- `test_watchdog_abort_on_swap_growth`: PASSED (triggers abort when swap grows by 600 MB).
- `test_watchdog_abort_on_low_free_swap`: PASSED (triggers abort when free swap drops below 1,000 MB).
- `test_watchdog_abort_on_timeout`: PASSED (triggers abort when time exceeds cutoff).

### D. Metrics & Checkpointing (4 tests)
- `test_compute_binary_metrics_perfect`: PASSED (verifies 1.0 accuracy, balanced acc, macro F1, and confusion matrix).
- `test_compute_binary_metrics_imperfect`: PASSED (verifies sensitivity, specificity, and confusion matrix cells).
- `test_save_checkpoint_atomic_success`: PASSED (verifies temporary directory staging and atomic rename).
- `test_save_checkpoint_rejects_overwriting_pretrained`: PASSED (blocks overwriting base model).
