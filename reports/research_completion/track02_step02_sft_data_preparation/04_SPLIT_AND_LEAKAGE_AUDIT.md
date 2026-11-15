# TrustRAG Track 2, Step 2: Split and Leakage Audit Report

## 1. Audit Overview

This audit independently verifies split integrity, absence of data leakage, and strict benchmark quarantine across the `sft_v1` Supervised Fine-Tuning dataset.

---

## 2. Root Cause Analysis: RAGTruth 0-Byte Validation Split

During the Track 2 Step 1 readiness audit, a zero-byte file was observed at `data/processed/ragtruth/validation.jsonl`.

### Investigation & Upstream Truth
1. **Upstream Source Inspection:** Inspection of the official RAGTruth repository release (Niu et al., ACL 2024; `response.jsonl` and `source_info.jsonl`) confirms that the authors partitioned RAGTruth exclusively into two subsets:
   - `train`: 15,090 generation responses derived from 2,515 source documents.
   - `test`: 2,700 generation responses derived from 450 source documents.
   - `validation`: **Not provided by upstream authors.**
2. **Track 1 Placeholder:** The data acquisition adapter in Track 1 created an empty `validation.jsonl` touch-file to fulfill directory layout expectations.
3. **Resolution:**
   - Instead of evaluating on unpartitioned data or creating arbitrary record splits, we performed an **80/20 source-document-grouped partition** strictly from `train.jsonl` (2,012 train source IDs, 503 validation source IDs).
   - This preserved the canonical test split (450 source documents, 2,700 responses) in complete isolation.

---

## 3. Source Document Leakage Census

Document leakage occurs when records in validation or test share source contexts with the training set, allowing models to memorize document facts rather than learning generalizable verification logic.

### 3.1 RAGTruth Split Isolation Audit
- Total canonical source IDs: 2,965 (2,515 train sources + 450 test sources).
- `sft_v1` train sources: 2,012
- `sft_v1` validation sources: 503
- Canonical test sources: 450

| Verification Check | Set A | Set B | Overlap Count | Overlap Percentage | Verdict |
| :--- | :--- | :--- | :---: | :---: | :---: |
| Train vs. Validation | `sft_v1` Train Sources | `sft_v1` Val Sources | **0** | **0.00%** | **PASS** |
| Train vs. Test | `sft_v1` Train Sources | Test Sources | **0** | **0.00%** | **PASS** |
| Validation vs. Test | `sft_v1` Val Sources | Test Sources | **0** | **0.00%** | **PASS** |

### 3.2 HaluEval Split Isolation Audit
- Total canonical QA source IDs: 10,000 (7,000 train + 1,500 val + 1,500 test).
- `sft_v1` train sources: 7,000
- `sft_v1` validation sources: 1,500
- Canonical test sources: 1,500

| Verification Check | Set A | Set B | Overlap Count | Overlap Percentage | Verdict |
| :--- | :--- | :--- | :---: | :---: | :---: |
| Train vs. Validation | `sft_v1` Train Sources | `sft_v1` Val Sources | **0** | **0.00%** | **PASS** |
| Train vs. Test | `sft_v1` Train Sources | Test Sources | **0** | **0.00%** | **PASS** |
| Validation vs. Test | `sft_v1` Val Sources | Test Sources | **0** | **0.00%** | **PASS** |

---

## 4. Record ID Collision Audit

- Total `sft_v1` train records: 26,072 unique `example_id`s.
- Total `sft_v1` validation records: 6,018 unique `example_id`s.
- Train vs Validation ID intersection: **0 (0.00%)**.
- Duplicate IDs within splits: **0 (0.00%)**.

---

## 5. Benchmark Quarantine Verification

To ensure that downstream retrieval and benchmark evaluation results remain uncorrupted by training contamination:

1. **RAGTruth Test Set (2,700 records):** Zero records or source documents appear in `sft_v1`.
2. **HaluEval Test Set (3,000 records):** Zero records or source documents appear in `sft_v1`.
3. **HotpotQA (7,405 records):** Quarantined as retrieval-only evaluation set. Exactly **0** HotpotQA records appear in `sft_v1`.
4. **MS MARCO (10,047 records):** Quarantined as retrieval-only evaluation set. Exactly **0** MS MARCO records appear in `sft_v1`.

---

## 6. Audit Conclusion

The `sft_v1` dataset achieves **absolute zero-leakage isolation (0.00% across all sets)** and maintains complete quarantine over all benchmark test and retrieval evaluation sets.

