# TrustRAG Track 2, Step 2.2: Split and Leakage Remediation Report

## 1. Audit & Remediation Framework

This report independently verifies the remediation of all document-level and passage-level leakage issues identified in Step 2.1 across the versioned `sft_v2` datasets.

---

## 2. RAGTruth Duplicate Article Remediation

### 2.1 The Vulnerability in `sft_v1`
In the canonical RAGTruth corpus (Niu et al., 2024), a CNN weather news article was accidentally duplicated under two consecutive source IDs:
- `source_id: 12084` (6 response records)
- `source_id: 12085` (6 response records)

In `sft_v1`, because partitioning was grouped strictly by string `source_id`, random hashing assigned `12084` to `train.jsonl` and `12085` to `validation.jsonl`, causing 1 document to leak across the partition boundary.

### 2.2 Remediation Mechanics in `sft_v2`
In `prepare_sft_v2_remediated.py`, document grouping is now enforced on the **normalized document text hash**:
$$\text{doc\_hash} = \text{SHA-256}(\text{normalize}(\text{document\_text}))$$
Because `12084` and `12085` share the identical normalized text, they evaluate to the same SHA-256 hash (`2011th` unique hash).

### 2.3 Post-Remediation Verification
- Document text hash for both articles: Assigned strictly to `train.jsonl`.
- Document overlap between RAGTruth train and validation: **0 (0.00%)**.
- Document overlap with RAGTruth canonical test set: **0 (0.00%)**.

---

## 3. HaluEval Passage Leakage Remediation

### 3.1 The Vulnerability in `sft_v1`
Upstream HaluEval QA was generated from HotpotQA multi-hop questions. Because multiple distinct questions in HotpotQA share the same introductory Wikipedia paragraph, row-index partitioning in the canonical benchmark caused context passages to be scattered across splits:
- 18 train records (9 QA pairs) shared context passages with the canonical test set.
- 8 validation records (4 QA pairs) shared context passages with the canonical test set.
- 26 validation records (13 QA pairs) shared context passages with the training set.

### 3.2 Remediation Mechanics in `sft_v2/binary`
1. **Canonical Test Quarantine:**
   Any training or validation candidate record whose passage hash appeared in `data/processed/halueval/test.jsonl` was **quarantined and excluded**. Exactly 26 records were removed.
2. **Train-Validation Passage Isolation:**
   Any validation record whose passage hash appeared in the clean training set was **quarantined and excluded**. Exactly 26 records were removed.
3. **Audit Trail:**
   All 52 quarantined records are fully preserved and cataloged in [`data/processed/sft_v2/binary/exclusion_manifest.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/exclusion_manifest.json).

### 3.3 Post-Remediation Verification
- Context passage overlap between HaluEval train and validation: **0 (0.00%)**.
- Context passage overlap with canonical HaluEval test set: **0 (0.00%)**.

---

## 4. Cross-Dataset & Retrieval Quarantine

- **Cross-Dataset ID Collisions:** Zero collisions between RAGTruth and HaluEval example IDs (all IDs are deterministically namespaced with `binary_ragtruth_`, `binary_halueval_`, etc.).
- **Retrieval Benchmark Quarantine:** HotpotQA (7,405 records) and MS MARCO (10,047 records) are **100% quarantined**. Exactly **0** retrieval records enter any `sft_v2` dataset.
- **Canonical Test Set Protection:** Canonical test datasets in `data/processed/ragtruth/test.jsonl` and `data/processed/halueval/test.jsonl` remain **strictly untouched and quarantined**.

---

## 5. Record Retention & Loss Ledger

| Dataset Objective | Upstream Records Available | Records Retained in `sft_v2` | Records Excluded | Excluded % | Primary Reason for Exclusion |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Binary Classification** | 32,090 | 32,038 | 52 | 0.16% | HaluEval test/train passage overlap quarantine |
| **Evidence-Grounded NLI** | 32,090 | 13,477 | 18,613 | 58.00% | HaluEval unmentioned conflation (17k) + RAGTruth mixed spans (1.6k) |
| **Span-Level Detection** | 32,090 | 15,090 | 17,000 | 52.98% | HaluEval zero-span quarantine |
| **G3 Five-Outcome** | 32,090 | **0** | 32,090 | 100.00% | Zero synthetic records fabricated; supervision gap |

