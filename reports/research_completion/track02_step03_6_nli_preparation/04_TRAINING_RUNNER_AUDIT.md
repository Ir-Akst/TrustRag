# TrustRAG — Track 2, Step 3.6: Training Runner Implementation & Test Audit

## 1. Runner Architecture & Features

The dedicated NLI runner `tools/training/train_nli_classifier.py` incorporates comprehensive safety controls:
1. **Deterministic 3-Class Balanced Sampling (`stratified_class_balanced`):**
   - Selects equal samples per class (e.g. 333 ENTAILMENT, 333 CONTRADICTION, 334 NEUTRAL for a 1,000-sample pilot).
2. **Real-Time Watchdog (`WatchdogMonitor`):**
   - Aborts if available host RAM drops below 700 MB.
   - Aborts if swap grows by > 500 MB from baseline.
   - Aborts if free swap drops below 1,000 MB.
   - Aborts if execution exceeds 1,800 seconds (30-minute timeout).
3. **Split Isolation Guard:**
   - Enforces zero example_id overlap and zero premise document SHA-256 hash overlap.
4. **Protected Path & Checkpoint Guard:**
   - Blocks any attempt to overwrite pretrained models or the accepted binary checkpoint.
   - Uses atomic directory replacement (`.tmp_*` -> final rename).
5. **Execution Authorization Gate:**
   - Explicit check: `config.authorized == True`. Without this flag, `execute_training()` raises `TrainingNotAuthorizedError`.

---

## 2. Test Suite Audit Results

Test Suite: `tests/unit/test_track02_step03_6_nli_training_runner.py`  
Total Test Cases: **21**  
Passing Tests: **21 / 21 (100% PASS)**  
Execution Time: **0.03s**

| # | Test Function Name | Functional Scope | Status |
| :-: | :--- | :--- | :---: |
| 1 | `test_validate_nli_record_valid` | Validates fully conformant record | **PASS** |
| 2 | `test_validate_nli_record_missing_fields` | Rejects missing mandatory schema fields | **PASS** |
| 3 | `test_validate_nli_record_invalid_label` | Rejects unmapped or misspelled label | **PASS** |
| 4 | `test_validate_nli_record_test_split_prohibited` | Blocks records tagged with split='test' | **PASS** |
| 5 | `test_validate_nli_record_empty_premise` | Rejects whitespace-only premise | **PASS** |
| 6 | `test_validate_nli_record_empty_hypothesis` | Rejects whitespace-only hypothesis | **PASS** |
| 7 | `test_serialize_nli_input` | Confirms whitespace strip and clean tuple output | **PASS** |
| 8 | `test_load_nli_dataset_class_balanced` | Verifies exact 1/3 balance across 3 classes | **PASS** |
| 9 | `test_load_nli_dataset_test_file_prohibited` | Blocks access to files containing 'test' | **PASS** |
| 10 | `test_verify_split_isolation_clean` | Confirms passing of disjoint train/val sets | **PASS** |
| 11 | `test_verify_split_isolation_id_leakage` | Catches duplicate example_id across splits | **PASS** |
| 12 | `test_verify_split_isolation_premise_leakage` | Catches duplicate premise text across splits | **PASS** |
| 13 | `test_compute_nli_metrics_perfect` | Verifies accuracy, balanced acc, F1, Brier, ECE | **PASS** |
| 14 | `test_compute_nli_metrics_imperfect` | Verifies 3x3 confusion matrix calculation | **PASS** |
| 15 | `test_watchdog_normal` | Confirms normal pass under healthy telemetry | **PASS** |
| 16 | `test_watchdog_abort_on_low_ram` | Verifies abort when RAM < 700 MB | **PASS** |
| 17 | `test_watchdog_abort_on_swap_growth` | Verifies abort on swap growth > 500 MB | **PASS** |
| 18 | `test_watchdog_abort_on_timeout` | Verifies abort when wall-clock exceeds cutoff | **PASS** |
| 19 | `test_save_checkpoint_atomic_protected_overwrite_rejection` | Blocks overwrite of binary checkpoint | **PASS** |
| 20 | `test_execute_training_unauthorized_rejection` | Blocks training when authorized=False | **PASS** |
| 21 | `test_prepare_nli_model_architecture` | Verifies 3-class head [3, 768] and FP32 | **PASS** |
