# TrustRAG Track 2 — Step 3.15
## 07 — Test Results

**Audit timestamp:** 2026-11-14T14:15:20Z

---

## 1. Test Execution Summary

Tests executed using:
- Python: `/home/aditya/rags/.venv/bin/python3` (3.14.9)
- pytest: 9.2.0
- `PYTHONPATH=/home/aditya/rags/TrustRag-phase11`

**Result: 46 PASSED / 1 SKIPPED / 0 FAILED** ✅

---

## 2. Test Suite 1: `test_track02_step03_6_nli_training_runner.py` (36 tests)

| # | Test | Result |
|---|---|---|
| 1 | `test_validate_nli_record_valid` | PASSED |
| 2 | `test_validate_nli_record_missing_fields` | PASSED |
| 3 | `test_validate_nli_record_invalid_label` | PASSED |
| 4 | `test_validate_nli_record_test_split_prohibited` | PASSED |
| 5 | `test_validate_nli_record_empty_premise` | PASSED |
| 6 | `test_validate_nli_record_empty_hypothesis` | PASSED |
| 7 | `test_serialize_nli_input` | PASSED |
| 8 | `test_load_nli_dataset_class_balanced` | PASSED |
| 9 | `test_load_nli_dataset_test_file_prohibited` | PASSED |
| 10 | `test_verify_split_isolation_clean` | PASSED |
| 11 | `test_verify_split_isolation_id_leakage` | PASSED |
| 12 | `test_verify_split_isolation_premise_leakage` | PASSED |
| 13 | `test_compute_nli_metrics_perfect` | PASSED |
| 14 | `test_compute_nli_metrics_imperfect` | PASSED |
| 15 | `test_watchdog_normal` | PASSED |
| 16 | `test_watchdog_abort_on_low_ram` | PASSED |
| 17 | `test_watchdog_abort_on_swap_growth` | PASSED |
| 18 | `test_watchdog_abort_on_timeout` | PASSED |
| 19 | `test_save_checkpoint_atomic_protected_overwrite_rejection` | PASSED |
| 20 | `test_execute_training_unauthorized_rejection` | PASSED |
| 21 | `test_prepare_nli_model_architecture` | **SKIPPED** (requires model load) |
| 22 | `test_deterministic_shuffling_reproducibility` | PASSED |
| 23 | `test_shuffled_order_breaks_sequential_tail` | PASSED |
| 24 | `test_class_starvation_detection_violation` | PASSED |
| 25 | `test_class_starvation_clean_on_shuffled_sequence` | PASSED |
| 26 | `test_evidence_preserving_tokenization_hypothesis_priority` | PASSED |
| 27 | `test_evidence_preserving_tokenization_long_hypothesis_safeguard` | PASSED |
| 28 | `test_save_checkpoint_atomic_protected_nli_pilot1000_overwrite_rejection` | PASSED |
| 29 | `test_evidence_span_retention_auditor_perfect_alignment` | PASSED |
| 30 | `test_evidence_span_retention_auditor_truncated_lost_and_partial` | PASSED |
| 31 | `test_evidence_span_retention_auditor_invalid_and_empty_spans` | PASSED |
| 32 | `test_multi_chunk_processor_single_chunk_fit` | PASSED |
| 33 | `test_multi_chunk_processor_sliding_window_overlap` | PASSED |
| 34 | `test_chunk_aggregator_contradiction_priority` | PASSED |
| 35 | `test_chunk_aggregator_insufficient_evidence_guard` | PASSED |
| 36 | `test_chunk_aggregator_average_probabilities` | PASSED |

---

## 3. Test Suite 2: `test_track02_step03_14_supervision_readiness.py` (11 tests)

| # | Test | Result |
|---|---|---|
| 1 | `test_evidence_to_chunk_assignment_and_containment` | PASSED |
| 2 | `test_evidence_free_chunk_detection` | PASSED |
| 3 | `test_contradiction_label_inheritance_prevention` | PASSED |
| 4 | `test_neutral_label_assignment_safety` | PASSED |
| 5 | `test_oversized_hypothesis_budgeting` | PASSED |
| 6 | `test_split_isolation_document_and_id_disjoint` | PASSED |
| 7 | `test_chunk_identity_and_traceability` | PASSED |
| 8 | `test_aggregation_compatibility_contradiction_priority` | PASSED |
| 9 | `test_dataset_reproducibility` | PASSED |
| 10 | `test_training_authorization_guard_unauthorized_rejection` | PASSED |
| 11 | `test_protected_checkpoints_safeguard` | PASSED |

---

## 4. Skip Analysis

**`test_prepare_nli_model_architecture` (SKIPPED):**
This test requires loading the DeBERTa-v3-small weights (~440 MB pytorch_model.bin)
and is skipped in the test environment to maintain fast unit test execution.
The model loading code is independently verified in source code review (Section 04).

---

## 5. Critical Safety Test Coverage

| Safety Property | Test(s) | Status |
|---|---|---|
| Authorization fence | `test_execute_training_unauthorized_rejection`, `test_training_authorization_guard_unauthorized_rejection` | ✅ PASS |
| Protected overwrite guard | `test_save_checkpoint_atomic_protected_overwrite_rejection`, `test_save_checkpoint_atomic_protected_nli_pilot1000_overwrite_rejection` | ✅ PASS |
| Test-set access prohibition | `test_validate_nli_record_test_split_prohibited`, `test_load_nli_dataset_test_file_prohibited` | ✅ PASS |
| Split isolation | `test_verify_split_isolation_id_leakage`, `test_verify_split_isolation_premise_leakage`, `test_split_isolation_document_and_id_disjoint` | ✅ PASS |
| Class starvation guard | `test_class_starvation_detection_violation`, `test_class_starvation_clean_on_shuffled_sequence` | ✅ PASS |
| Deterministic shuffling | `test_deterministic_shuffling_reproducibility`, `test_shuffled_order_breaks_sequential_tail`, `test_dataset_reproducibility` | ✅ PASS |
| Watchdog RAM/swap/timeout | `test_watchdog_abort_on_low_ram`, `test_watchdog_abort_on_swap_growth`, `test_watchdog_abort_on_timeout` | ✅ PASS |
| Chunk label inheritance prevention | `test_contradiction_label_inheritance_prevention`, `test_evidence_free_chunk_detection` | ✅ PASS |

**All safety-critical tests pass. No test failures.**

---
*Generated by Step 3.15 Independent Preflight Audit — 2026-11-14T14:15:20Z*
