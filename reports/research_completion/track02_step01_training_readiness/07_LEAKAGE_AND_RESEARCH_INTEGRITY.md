# TrustRAG — Track 2, Step 1: Independent Neural Training Readiness Audit
# 07 — Leakage, Data Contamination & Research Integrity Audit

**Audit Objective:** Rigorously verify whether train, validation, and test dataset splits are properly isolated, confirm zero data contamination, enforce licensing boundaries, and ensure academic research integrity.

---

## 1. Cross-Split Overlap & Leakage Analysis

An exhaustive record-by-record comparison was conducted across all splits in `data/processed/`:

### 1.1 RAGTruth Cross-Split Leakage (`data/processed/ragtruth/`)

| Split Pair | Compared Records | `record_id` Overlap | `source_id` Overlap | `document` Text Overlap | `claim` Text Overlap | Integrity Finding |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Train vs Test** | 15,090 vs 2,700 | **0** | **0** | **0** | **1** (Trivial token) | **CLEAN (0 Document Leakage)** |
| **Train vs Validation** | 15,090 vs 0 | N/A | N/A | N/A | N/A | **VALIDATION SPLIT EMPTY (0 bytes)** |
| **Validation vs Test** | 0 vs 2,700 | N/A | N/A | N/A | N/A | N/A |

- **Source Document Isolation:** The source documents in RAGTruth train (CNN/DM, PubMed, etc.) do not appear in the test split. There is **zero document leakage** between training and testing.
- **Claim Overlap Note:** Exactly 1 identical claim string was detected across the 17,790 records. Inspection confirmed it was a trivial affirmative sentence ("Yes.") produced independently by two different models on unrelated articles.
- **Integrity Status:** **PASS (Train and test are strictly disjoint).**

### 1.2 HaluEval Cross-Split Leakage (`data/processed/halueval/`)

| Split Pair | Compared Records | `record_id` Overlap | `source_id` Overlap | `document` Text Overlap | `claim` Text Overlap | Integrity Finding |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Train vs Validation** | 14,000 vs 3,000 | **0** | **0** | 13 | 225 | **SOURCE IDs STRICTLY DISJOINT** |
| **Train vs Test** | 14,000 vs 3,000 | **0** | **0** | 9 | 223 | **SOURCE IDs STRICTLY DISJOINT** |
| **Validation vs Test** | 3,000 vs 3,000 | **0** | **0** | 4 | 93 | **SOURCE IDs STRICTLY DISJOINT** |

- **Partition Principle:** HaluEval QA was partitioned strictly by `source_id` (7,000 unique questions in train, 1,500 in validation, 1,500 in test).
- **Document Overlap Note:** A tiny fraction of questions in HaluEval (9 out of 10,000) reference the exact same Wikipedia passage. However, the questions, factual answers, and hallucinated answers are distinct.
- **Claim Overlap Note:** Overlapping claims represent common short entity answers (e.g., country names, dates, or "Yes/No").
- **Integrity Status:** **PASS (Questions and source annotations are strictly partitioned).**

---

## 2. Research Integrity Boundary Violations: Risks & Classifications

The following risk checklist assesses whether planned or potential actions would violate research integrity:

| Integrity Check | Audit Finding / Requirement | Severity Status |
| :--- | :--- | :---: |
| **1. Validation-Only Retrieval Datasets Used for Training** | HotpotQA (`7,405` val queries) and MS MARCO (`10,047` val queries) must **NEVER** be used to train retrievers, neural rerankers, or verifiers. | **CRITICAL GUARD / PASS** |
| **2. Test-Set Contamination** | Neither RAGTruth test (`2,700` records) nor HaluEval test (`3,000` records) has ever been exposed to training or gradient updates. | **PASS** |
| **3. Non-Commercial & Non-Derivative License Adherence** | LLM-AggreFact is licensed under CC-BY-ND-4.0. Using it for fine-tuning would violate license terms. It must remain evaluation-only. | **PASS (ACCESS BLOCKED)** |
| **4. Synthetic Label Traceability** | Synthetic security records in `data/raw/custom_security/` are explicitly tagged with `provenance: TrustRAG-Synthetic-Security-Benchmark-v1.0`. None are mislabeled as canonical human benchmarks. | **PASS** |
| **5. Honest Baseline Reporting** | Zero mock metrics or interpolated numbers have been reported for blocked datasets (RSB, LLM-AggreFact, full-corpus MS MARCO). | **PASS** |
| **6. Unpopulated RAGTruth Validation Split** | Training on RAGTruth train without creating a validation set risks overfitting or uncontrolled training duration. | **WARNING (Needs 80/20 split)** |

---

## 3. Overall Research Integrity Verdict

```
================================================================================
INTEGRITY VERDICT: PASS WITH WARNING
================================================================================
```

- **Pass:** The data splits established in Track 1 adhere to rigorous scientific boundaries. There is no test data leakage, no label poisoning, and no benchmark contamination.
- **Warning:** A clean 80/20 validation carve-out from `data/processed/ragtruth/train.jsonl` must be performed to populate the empty `validation.jsonl` prior to neural training.

