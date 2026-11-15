# TrustRAG Track 2, Step 2.1: Split and Leakage Re-Verification Report

## 1. Audit Methodology

This report independently re-verifies dataset partitioning, split isolation, benchmark test quarantine, and text deduplication for `sft_v1`.

The audit evaluated:
1. Identifier-level isolation (`source_id`, `example_id`).
2. Exact document-text hashing (SHA-256 of context strings).
3. Benchmark test set contamination.
4. Retrieval benchmark quarantine (HotpotQA, MS MARCO).

---

## 2. Source Identifier Isolation Audit

| Benchmark | Split Pair | Method | Overlap Count | Overlap % | Verdict |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **RAGTruth** | Train vs. Validation | `source_id` matching | **0** | **0.00%** | **PASS** |
| **RAGTruth** | Train vs. Test | `source_id` matching | **0** | **0.00%** | **PASS** |
| **RAGTruth** | Validation vs. Test | `source_id` matching | **0** | **0.00%** | **PASS** |
| **HaluEval** | Train vs. Validation | `source_id` matching | **0** | **0.00%** | **PASS** |
| **HaluEval** | Train vs. Test | `source_id` matching | **0** | **0.00%** | **PASS** |
| **HaluEval** | Validation vs. Test | `source_id` matching | **0** | **0.00%** | **PASS** |
| **Cross-Dataset** | RAGTruth vs HaluEval | `example_id` collision | **0** | **0.00%** | **PASS** |

**Auditor Finding on Identifiers:** At the metadata identifier level, all splits are 100% disjoint with zero collisions.

---

## 3. Adversarial Document Content Deduplication Audit

To verify whether upstream benchmarks contained identical text under different IDs, full document text matching was performed across all splits.

### 3.1 RAGTruth Document Content Overlap
- **Train vs Validation Document Overlap:** Exactly **1 document** (out of 2,515 distinct source texts).
  - *Train Example ID:* `sft_ragtruth_train_ragtruth_3707` (`source_id: 12084`)
  - *Validation Example ID:* `sft_ragtruth_validation_ragtruth_3713` (`source_id: 12085`)
  - *Content:* A CNN weather report beginning *"Tornadoes, fierce winds and severe thunderstorms with large hail..."*
  - *Root Cause:* The upstream canonical RAGTruth corpus (Niu et al., 2024) duplicated this exact news story under two consecutive source IDs (`12084` and `12085`). Because the Step 2 partition grouped by `source_id`, `12084` fell into the train slice and `12085` fell into the validation slice.
  - *Impact:* Affects exactly 1 out of 503 validation documents (0.19% of validation sources). Negligible impact on model selection.
- **RAGTruth Test Quarantine:** Exactly **0 documents** from the canonical test set appear in train or validation (100% clean test isolation).

### 3.2 HaluEval Document Content Overlap
- **Train vs Validation Document Overlap:** Exactly **13 passages** appear in both train and validation.
- **Train vs Test Document Overlap:** Exactly **9 passages** appear in both train and test.
- **Validation vs Test Document Overlap:** Exactly **4 passages** appear in both validation and test.
- *Root Cause Analysis:*  
  HaluEval QA was generated from HotpotQA multi-hop questions. In HotpotQA, multiple distinct questions are frequently anchored on the same Wikipedia introductory paragraph.  
  The upstream HaluEval authors partitioned rows by row index rather than grouping by paragraph text. Consequently, distinct questions sharing the same underlying paragraph were split across train, validation, and test.
- *Auditor Assessment:*  
  This is an inherent property of the upstream canonical HaluEval release. Because the questions, candidate responses, and hallucinated answers are completely distinct, semantic leakage is low, but researchers evaluating zero-shot passage memorization must be aware of these 9 overlapping passages.

---

## 4. Retrieval Benchmark Quarantine

The prompt instructions strictly mandated that retrieval benchmark datasets (HotpotQA and MS MARCO) must never be mixed into fine-tuning data.

- **HotpotQA Evaluation Records (7,405 records):** Exactly **0 records** present in `sft_v1`.
- **MS MARCO Evaluation Records (10,047 records):** Exactly **0 records** present in `sft_v1`.
- **Retrieval Quarantine Status:** **100% COMPLIANT.**

---

## 5. RAGTruth Validation Split Provenance Verification

- **Audit Check:** Was the RAGTruth validation split carved strictly from the training partition?
- **Raw Train Source Count:** 2,515 distinct source documents (15,090 response records).
- **Partition Execution:**
  - `sft_v1` Train: 2,012 sources (12,072 records) = $2,012 / 2,515 = 80.00\%$.
  - `sft_v1` Validation: 503 sources (3,018 records) = $503 / 2,515 = 20.00\%$.
- **Sum:** $12,072 + 3,018 = 15,090$ records ($2,012 + 503 = 2,515$ sources).
- **Test Partition:** Canonical test set contains 450 sources (2,700 records) and was completely untouched.

**Auditor Finding:** **Verified.** The RAGTruth validation split was derived 100% from the upstream training slice with zero test contamination.

