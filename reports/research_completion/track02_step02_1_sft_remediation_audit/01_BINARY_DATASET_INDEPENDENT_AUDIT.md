# TrustRAG Track 2, Step 2.2.1: Binary Dataset Independent Audit Report

## 1. Audit Scope & Verification Mandate

This report provides an independent, read-only empirical verification of the **Binary Hallucination Classification Dataset** in:
[`data/processed/sft_v2/binary/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/)

The audit independently recalculates:
1. Exact record counts, label balances, and provenance markers.
2. HaluEval dual-record expansion integrity.
3. Multi-level text overlap (document contexts, questions, candidate responses).
4. Individual inspection of the 52 quarantined records.

---

## 2. Independent Census & Label Verification

All records were decoded and parsed directly from disk:

| Split | Total Records Verified | FACTUAL | HALLUCINATED | RAGTruth Records | HaluEval Records | Document Hashes | Document Overlap |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train Split** | **26,054** | 13,698 (52.58%) | 12,356 (47.42%) | 12,072 | 13,982 | 8,984 | **0.00%** |
| **Validation Split** | **5,984** | 3,145 (52.56%) | 2,839 (47.44%) | 3,018 | 2,966 | 1,978 | **0.00%** |
| **Total Combined** | **32,038** | **16,843 (52.57%)** | **15,195 (47.43%)** | **15,090** | **16,948** | **10,962** | **0.00%** |

### Label Preservation Verification
- Original labels from RAGTruth (`FACTUAL`, `HALLUCINATED`) were preserved with **100% fidelity**.
- Original labels from HaluEval (`right_answer` $\rightarrow$ `FACTUAL`, `hallucinated_answer` $\rightarrow$ `HALLUCINATED`) were preserved with **100% fidelity**.
- Zero binary labels were derived from or collapsed to G3 verdicts.

---

## 3. HaluEval Dual-Record Expansion Audit

Each original HaluEval QA pair consists of one question, one passage, one right answer, and one hallucinated answer.

The audit verified the expansion across all records:
- **Train Split HaluEval Pairs:** Exactly **6,991 unique `source_id`s**. Every single source ID occurs **exactly twice** (1 `FACTUAL`, 1 `HALLUCINATED`). Total: $6,991 \times 2 = 13,982$ records.
- **Validation Split HaluEval Pairs:** Exactly **1,483 unique `source_id`s**. Every single source ID occurs **exactly twice** (1 `FACTUAL`, 1 `HALLUCINATED`). Total: $1,483 \times 2 = 2,966$ records.
- **Orphan Records:** **0 orphans**. Not a single QA pair has an unmatched right or hallucinated answer.

---

## 4. Multi-Level Independent Text Overlap Audit

To guarantee that zero document-hash overlap did not conceal text-level leakage:

| Text Level | Train Unique Set | Validation Unique Set | Intersection Count | Leakage Detected? | Auditor Assessment |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Document Context Text** | 8,984 unique texts | 1,978 unique texts | **0** | **NO** | 100% clean document isolation. |
| **Question / Prompt Text** | 24,082 unique texts | 5,502 unique texts | **0** | **NO** | 100% clean prompt isolation. |
| **Candidate Response Text**| 24,462 unique texts | 5,770 unique texts | **219** | **NO** | Generic short string overlap (e.g. "American", "2016", "no", "yes") inherent in QA tasks. |

---

## 5. Audit of the 52 Quarantined Binary Records

The audit inspected all 52 entries in [`exclusion_manifest.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/exclusion_manifest.json):
- **Completeness of Exclusion Groups:** Exactly 26 base QA pairs were excluded. For all 26 pairs, both the factual record and the hallucinated record were removed together (100% paired completeness).
- **Test Set Quarantine:**
  - 18 train records (9 pairs) whose passage appeared in `data/processed/halueval/test.jsonl` were successfully excluded from training.
  - 8 validation records (4 pairs) whose passage appeared in `test.jsonl` were successfully excluded from validation.
- **Train-Validation Passage Isolation:**
  - 26 validation records (13 pairs) whose passage appeared in training were successfully excluded from validation.

---

## 6. Auditor Acceptance Verdict

**Binary Hallucination Classification:** **`READY`**  
The dataset is clean, leak-free, correctly balanced, and authorized for model training.

