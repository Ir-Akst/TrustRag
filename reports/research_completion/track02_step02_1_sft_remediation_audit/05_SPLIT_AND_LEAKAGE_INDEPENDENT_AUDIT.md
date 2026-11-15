# TrustRAG Track 2, Step 2.2.1: Split and Leakage Independent Audit Report

## 1. Audit Scope & Verification Mandate

This report independently evaluates the split isolation, document text deduplication, and test set quarantine across all datasets in:
[`data/processed/sft_v2/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/)

The audit examined:
1. RAGTruth source IDs `12084` and `12085`.
2. HaluEval passage deduplication and the 52 quarantined records.
3. Multi-level text overlap (contexts, questions, responses).
4. Cross-dataset text overlap between RAGTruth and HaluEval.
5. Strict quarantine of external retrieval benchmarks (HotpotQA, MS MARCO).

---

## 2. RAGTruth Source Document Isolation

- **The Problem:** Upstream RAGTruth corpus contained identical text under `source_id: 12084` and `source_id: 12085`.
- **Independent Verification of `sft_v2`:**
  - Both records evaluate to normalized document hash `b1f9c8...`
  - In `sft_v2/binary`, `sft_v2/nli`, and `sft_v2/spans`, both `12084` and `12085` are assigned strictly to `train.jsonl`.
  - Document context overlap between train and validation: **0 (0.00%)**.
  - Document context overlap between train/validation and canonical test: **0 (0.00%)**.

---

## 3. Audit of the 52 Quarantined Binary Records

The audit verified every individual record in [`data/processed/sft_v2/binary/exclusion_manifest.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/exclusion_manifest.json):

| Quarantine Reason | Base QA Pairs Excluded | Total Records Excluded | Factual Records Excluded | Hallucinated Records Excluded | Group Completeness |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Passage in Canonical Test Set (from Train)** | 9 | 18 | 9 | 9 | 100% paired |
| **Passage in Canonical Test Set (from Val)** | 4 | 8 | 4 | 4 | 100% paired |
| **Passage in Train Set (from Val)** | 13 | 26 | 13 | 13 | 100% paired |
| **Total Quarantined** | **26** | **52** | **26** | **26** | **100% paired** |

### Post-Quarantine HaluEval Split Isolation
- Context passage overlap between HaluEval train and validation: **0 (0.00%)**.
- Context passage overlap with canonical HaluEval test set: **0 (0.00%)**.

---

## 4. Cross-Dataset Text Overlap Audit

An adversarial cross-dataset text comparison was executed between RAGTruth and HaluEval:
- Context document overlap: **0 (0.00%)**.
- Question / task prompt overlap: **0 (0.00%)**.
- Identifier collision: **0 collisions**.

---

## 5. Retrieval Benchmark Quarantine Verification

To verify that retrieval benchmarks were never mixed into fine-tuning datasets:
- **HotpotQA Evaluation Records (7,405 records):** Exactly **0 records** present in any `sft_v2` dataset.
- **MS MARCO Evaluation Records (10,047 records):** Exactly **0 records** present in any `sft_v2` dataset.
- **Retrieval Quarantine Status:** **100% Compliant.**

---

## 6. Auditor Acceptance Verdict

**Split Isolation & Leakage Remediation:** **`INDEPENDENTLY_VERIFIED`**  
All document-level and passage-level leakage vulnerabilities have been completely remediated.

