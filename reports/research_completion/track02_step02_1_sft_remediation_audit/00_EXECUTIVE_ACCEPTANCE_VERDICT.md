# TrustRAG Track 2, Step 2.2.1: Independent SFT Remediation Acceptance Audit — Executive Verdict

## 1. Audit Framework & Preflight Status

- **Audit Date:** 2026-11-14
- **Auditor Role:** Independent Adversarial ML Dataset Auditor
- **Audit Mandate:** Perform a strict, independent, read-only empirical verification of `data/processed/sft_v2/`, the remediation pipeline [`tools/data_prep/prepare_sft_v2_remediated.py`](file:///home/aditya/rags/TrustRag-phase11/tools/data_prep/prepare_sft_v2_remediated.py), and the Step 2.2 remediation claims.
- **Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)
- **Protected Phase 10 Baseline:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, **UNTOUCHED**)
- **Historical Baseline Integrity:** `data/processed/sft_v1/` remains **100% untouched and cryptographically verified**.
- **Final Overall Audit Acceptance Verdict:** **`INDEPENDENTLY_VERIFIED`** (with objective-specific boundaries).

---

## 2. Definitive Objective-Specific Acceptance Matrix

| Objective / Dataset | Verified Train Records | Verified Val Records | Quarantined / Excluded | Verified Offsets / Leakage | Final Readiness Verdict | Training Authorized? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Binary Hallucination Classification** | 26,054 | 5,984 | 52 records | 0.00% document overlap | **`READY`** | **YES** |
| **2. Evidence-Grounded 3-Way NLI** | 10,815 | 2,662 | 18,613 records | Pure 3-way mapping verified | **`READY`** | **YES (RAGTruth Only)** |
| **3. Span-Level Detection** | 12,072 | 3,018 | 17,000 records | 12,756 / 12,756 exact matches | **`READY`** | **YES (RAGTruth Only)** |
| **4. Full Five-Outcome G3 Verification** | **0** | **0** | N/A | 0 records fabricated | **`BLOCKED`** | **NO (Supervision Gap)** |
| **5. Generative Structured Verification** | 26,054 | 5,984 | 52 records | Direct JSON verified | **`CONDITIONALLY_READY`** | **YES (No `<think>` Traces)** |

---

## 3. Key Acceptance Audit Findings

### 3.1 Mathematical Reconciliation of the 1,533 Spans Discrepancy
The apparent discrepancy between Step 2.1 (14,289 spans reported) and Step 2.2 (12,756 spans reported) was independently investigated directly from the raw `response.jsonl` file:
$$\text{Total Raw Spans} = 14,289 = \underbrace{12,756}_{\text{train responses (15,090)}} + \underbrace{1,533}_{\text{test responses (2,700)}}$$
- **Finding:** Exactly **1,533 spans** belong to the canonical RAGTruth test set (`data/processed/ragtruth/test.jsonl`).
- **Verdict:** Zero spans were lost or dropped. The test set was strictly quarantined from fine-tuning to protect evaluation integrity.

### 3.2 Complete Leakage Remediation
1. **RAGTruth Duplicate Document (`12084` vs `12085`):** Both records evaluate to the identical SHA-256 document hash and are placed together in `train.jsonl`. Train-val document overlap is **0.00%**.
2. **HaluEval Test and Split Overlap:** Exactly 52 records (26 QA pairs) were quarantined (18 test-leaking in train, 8 test-leaking in val, 26 train-val leaking in val). Every excluded pair had both its factual and hallucinated records removed together.
3. **Retrieval Quarantine:** HotpotQA and MS MARCO contain **0 records** across all `sft_v2` datasets.

### 3.3 Semantic NLI Label Integrity
The remediation in `sft_v2/nli` successfully eliminated the pathological conflation of baseless information and contradiction:
- Factual (0 spans) $\rightarrow$ `ENTAILMENT` (8,369 records).
- Pure Conflict $\rightarrow$ `CONTRADICTION` (1,776 records).
- Pure Baseless Info $\rightarrow$ `NEUTRAL` (3,332 records).
- Mixed Conflict & Baseless Info $\rightarrow$ **EXCLUDED** (1,613 records).
- HaluEval QA $\rightarrow$ **EXCLUDED** (17,000 records).

### 3.4 Zero Fabricated G3 Records
No synthetic labels or pseudo-ground-truth five-outcome records were created. G3 remains cleanly blocked with an authoritative gap analysis.

---

## 4. Auditor Conclusion

The remediation executed in Step 2.2 adheres strictly to conservative machine learning engineering standards. `sft_v2` provides verified, leak-free, objective-specific datasets ready for model training under their designated task scopes.

