# TrustRAG — Track 1, Step 2.3: Independent Corrected Baseline Acceptance Audit
# 01 — Comprehensive Prediction Census & ID Accounting

**Audit Target:** `reports/research_completion/track02_step02_2_corrected_baselines/`  
**Evaluation Harness:** `tools/evaluation/run_track02_benchmarks.py`  
**Input Ground Truth Datasets:**
- `data/processed/ragtruth/test.jsonl` (2,700 records)
- `data/processed/halueval/test.jsonl` (3,000 records)
- `data/raw/hotpotqa/hotpotqa_val_distractor.parquet` (7,405 queries)
- `data/raw/ms_marco/ms_marco_val_v1.1.parquet` (10,047 queries)

---

## 1. Per-Example Prediction Census

An exhaustive census of all eight prediction files was conducted directly from storage on disk.

| Dataset | Evaluation Mode | Prediction File Name | Input Records | Prediction Records | Unique Record IDs | Duplicate IDs | Missing IDs | Extra IDs | ID Match Rate |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **RAGTruth** | `no_verification` | `predictions_ragtruth_no_verification.jsonl` | 2,700 | 2,700 | 2,700 | 0 | 0 | 0 | 100.00% |
| **RAGTruth** | `default_g3` | `predictions_ragtruth_default.jsonl` | 2,700 | 2,700 | 2,700 | 0 | 0 | 0 | 100.00% |
| **RAGTruth** | `strict_g3` | `predictions_ragtruth_strict.jsonl` | 2,700 | 2,700 | 2,700 | 0 | 0 | 0 | 100.00% |
| **HaluEval** | `no_verification` | `predictions_halueval_no_verification.jsonl` | 3,000 | 3,000 | 3,000 | 0 | 0 | 0 | 100.00% |
| **HaluEval** | `default_g3` | `predictions_halueval_default.jsonl` | 3,000 | 3,000 | 3,000 | 0 | 0 | 0 | 100.00% |
| **HaluEval** | `strict_g3` | `predictions_halueval_strict.jsonl` | 3,000 | 3,000 | 3,000 | 0 | 0 | 0 | 100.00% |
| **HotpotQA** | `tf_idf_retriever` | `predictions_hotpotqa_retrieval.jsonl` | 7,405 | 7,405 | 7,405 | 0 | 0 | 0 | 100.00% |
| **MS MARCO** | `tf_idf_retriever` | `predictions_msmarco_retrieval.jsonl` | 10,047 | 9,706 | 9,706 | 0 | 0 | 0 | 100.00%* |
| **Total** | — | — | **34,552** | **34,211** | **34,211** | **0** | **0** | **0** | **100.00%** |

*\*Note on MS MARCO:* In the official MS MARCO v1.1 validation set, 341 queries contain no annotated positive passage in `is_selected` (all 0s). As specified and verified in Step 2.1 and Step 2.2, these unannotated queries cannot be evaluated for ranking metrics and were cleanly segregated into `skipped_queries`. All 9,706 evaluable queries were processed with 100.00% ID fidelity and 0 duplicates.

---

## 2. Ground Truth Distribution Verification

The ground-truth labels recorded in each prediction record were audited against the source datasets.

### 2.1 RAGTruth Test Split
- **Source Dataset Path:** `data/processed/ragtruth/test.jsonl`
- **Total Source Records:** 2,700
- **Ground Truth Breakdown:**
  - `FACTUAL`: 1,757 records (65.07%)
  - `HALLUCINATED`: 943 records (34.93%)
- **Prediction Files Distribution:**
  - `predictions_ragtruth_no_verification.jsonl`: 1,757 FACTUAL, 943 HALLUCINATED (100% match)
  - `predictions_ragtruth_default.jsonl`: 1,757 FACTUAL, 943 HALLUCINATED (100% match)
  - `predictions_ragtruth_strict.jsonl`: 1,757 FACTUAL, 943 HALLUCINATED (100% match)

### 2.2 HaluEval Test Split
- **Source Dataset Path:** `data/processed/halueval/test.jsonl`
- **Total Source Records:** 3,000
- **Ground Truth Breakdown:**
  - `FACTUAL`: 1,500 records (50.00%)
  - `HALLUCINATED`: 1,500 records (50.00%)
- **Prediction Files Distribution:**
  - `predictions_halueval_no_verification.jsonl`: 1,500 FACTUAL, 1,500 HALLUCINATED (100% match)
  - `predictions_halueval_default.jsonl`: 1,500 FACTUAL, 1,500 HALLUCINATED (100% match)
  - `predictions_halueval_strict.jsonl`: 1,500 FACTUAL, 1,500 HALLUCINATED (100% match)

---

## 3. Five-Outcome Taxonomy Census

Every single verdict in the verification prediction files was audited to confirm that it belongs strictly to the defined five-outcome partition:
`{SUPPORTED, CONTRADICTED, PARTIALLY_SUPPORTED, INSUFFICIENT_EVIDENCE, UNCERTAIN}`.

### 3.1 RAGTruth Five-Outcome Distribution

| Evaluation Mode | SUPPORTED | CONTRADICTED | PARTIALLY_SUPPORTED | INSUFFICIENT_EVIDENCE | UNCERTAIN | Total Sum | Valid (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `no_verification` | 2,700 | 0 | 0 | 0 | 0 | 2,700 | 100.00% |
| `default_g3` (0.65) | 9 | 1,885 | 436 | 280 | 90 | 2,700 | 100.00% |
| `strict_g3` (0.80) | 3 | 1,914 | 343 | 379 | 61 | 2,700 | 100.00% |

### 3.2 HaluEval Five-Outcome Distribution

| Evaluation Mode | SUPPORTED | CONTRADICTED | PARTIALLY_SUPPORTED | INSUFFICIENT_EVIDENCE | UNCERTAIN | Total Sum | Valid (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `no_verification` | 3,000 | 0 | 0 | 0 | 0 | 3,000 | 100.00% |
| `default_g3` (0.65) | 1,153 | 235 | 19 | 1,571 | 22 | 3,000 | 100.00% |
| `strict_g3` (0.80) | 1,050 | 235 | 20 | 1,675 | 20 | 3,000 | 100.00% |

### 3.3 Census Verification Findings
1. **Zero Dropped Records:** The sum of counts across all five outcomes equals the exact number of input records (2,700 and 3,000 respectively). The 436-record (RAGTruth) and 19-record (HaluEval) accounting gap identified in Step 2.1 is completely cured.
2. **Zero Null or Invalid Verdicts:** All 17,100 verification prediction lines contain valid non-null strings adhering strictly to the `G3Verdict` enumeration.
3. **Census Acceptance Status:** **PASSED (100.00%)**.

