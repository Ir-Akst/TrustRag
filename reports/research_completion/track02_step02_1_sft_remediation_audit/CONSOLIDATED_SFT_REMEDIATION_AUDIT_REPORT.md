# TrustRAG Track 2, Step 2.2.1: Independent SFT Remediation Acceptance Audit — Consolidated Master Report

**Document Version:** 1.0.0  
**Audit Date:** 2026-11-14  
**Auditor Role:** Independent Adversarial ML Dataset Auditor  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, baseline HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Phase 10 Baseline:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, baseline HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, **UNTOUCHED**)  
**Historical Baseline Integrity:** `data/processed/sft_v1/` (**PRESERVED UNCHANGED**, 5/5 checksums match)  
**Overall Acceptance Verdict:** **`INDEPENDENTLY_VERIFIED`**

---

## Table of Contents
1. [Executive Summary & Preflight Verification](#1-executive-summary--preflight-verification)
2. [Definitive Objective Acceptance Matrix](#2-definitive-objective-acceptance-matrix)
3. [Binary Dataset Independent Audit (`sft_v2/binary`)](#3-binary-dataset-independent-audit-sft_v2binary)
4. [NLI Semantic Independent Audit (`sft_v2/nli`)](#4-nli-semantic-independent-audit-sft_v2nli)
5. [Mathematical Reconciliation of the 1,533 Spans Discrepancy](#5-mathematical-reconciliation-of-the-1533-spans-discrepancy)
6. [Span Offset Exactness & Character Slicing Verification (`sft_v2/spans`)](#6-span-offset-exactness--character-slicing-verification-sft_v2spans)
7. [Split Isolation & Leakage Remediation Audit](#7-split-isolation--leakage-remediation-audit)
8. [Generative Target Capability Assessment](#8-generative-target-capability-assessment)
9. [G3 Supervision Gap Re-Verification (`sft_v2/g3_readiness`)](#9-g3-supervision-gap-re-verification-sft_v2g3_readiness)
10. [Master Acceptance Matrix](#10-master-acceptance-matrix)

---

## 1. Executive Summary & Preflight Verification

### 1.1 Scope & Operational Mandate
This independent acceptance audit empirically inspects the four remediated datasets in `data/processed/sft_v2/`, the transformation pipeline [`tools/data_prep/prepare_sft_v2_remediated.py`](file:///home/aditya/rags/TrustRag-phase11/tools/data_prep/prepare_sft_v2_remediated.py), and the claims presented in Step 2.2.

### 1.2 Preflight Status
- Target Repository HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` on `phase-11` (**VERIFIED**).
- Protected Phase 10 HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168` on `phase-10` (**VERIFIED UNTOUCHED**).
- Historical Baseline `sft_v1`: All 5 files match cryptographic checksums (**PRESERVED UNCHANGED**).
- Step 2.1 & Step 2.2 Report Checksums: Verified bit-for-bit.

---

## 2. Definitive Objective Acceptance Matrix

| Objective / Dataset | Verified Train Records | Verified Val Records | Quarantined / Excluded | Verified Offsets / Leakage | Final Readiness Verdict | Training Authorized? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Binary Classification** | 26,054 | 5,984 | 52 records | 0.00% document overlap | **`READY`** | **YES** |
| **2. Evidence-Grounded 3-Way NLI** | 10,815 | 2,662 | 18,613 records | Pure 3-way mapping verified | **`READY`** | **YES (RAGTruth Only)** |
| **3. Span-Level Detection** | 12,072 | 3,018 | 17,000 records | 12,756 / 12,756 exact matches | **`READY`** | **YES (RAGTruth Only)** |
| **4. Full 5-Outcome G3 Verification** | **0** | **0** | N/A | 0 records fabricated | **`BLOCKED`** | **NO (Supervision Gap)** |
| **5. Generative Structured Verification** | 26,054 | 5,984 | 52 records | Direct JSON verified | **`CONDITIONALLY_READY`** | **YES (No `<think>` Traces)** |

---

## 3. Binary Dataset Independent Audit (`sft_v2/binary`)

- **Train Split (26,054 records):** 13,698 FACTUAL, 12,356 HALLUCINATED.
- **Validation Split (5,984 records):** 3,145 FACTUAL, 2,839 HALLUCINATED.
- **HaluEval Expansion Audit:** Verified that every HaluEval base QA pair expands to exactly 2 records (1 factual, 1 hallucinated). Exactly 6,991 pairs in train ($6,991 \times 2 = 13,982$) and 1,483 pairs in validation ($1,483 \times 2 = 2,966$). Zero orphan records.
- **Multi-Level Text Overlap Audit:**
  - Document context overlap train vs val: **0 (0.00%)**.
  - Question / prompt overlap train vs val: **0 (0.00%)**.
  - Candidate response overlap: 219 generic short strings (e.g. "American", "2016", "no", "yes").
- **Exclusion Audit:** All 52 quarantined records (26 QA pairs) were removed as complete pairs.

---

## 4. NLI Semantic Independent Audit (`sft_v2/nli`)

- **Train Split (10,815 records):** 6,707 ENTAILMENT (62.02%), 1,420 CONTRADICTION (13.13%), 2,688 NEUTRAL (24.85%).
- **Validation Split (2,662 records):** 1,662 ENTAILMENT (62.43%), 356 CONTRADICTION (13.37%), 644 NEUTRAL (24.20%).
- **Total Combined:** **13,477 clean 3-way NLI records**.
- **Semantic Mapping Verification:**
  - `ENTAILMENT`: Verified 0 marked hallucination spans across all 8,369 records.
  - `CONTRADICTION`: Verified that 100% of the 1,776 records contain exclusively `Conflict` spans.
  - `NEUTRAL`: Verified that 100% of the 3,332 records contain exclusively `Baseless Info` spans.
- **Exclusion Manifest:** 1,613 mixed-span RAGTruth records and 17,000 HaluEval QA records were quarantined, protecting 3-way NLI from label corruption.

---

## 5. Mathematical Reconciliation of the 1,533 Spans Discrepancy

$$\begin{aligned}
\text{Total Raw Spans} &= 14,289 = \underbrace{12,756}_{\text{train responses (15,090)}} + \underbrace{1,533}_{\text{test responses (2,700)}}
\end{aligned}$$

- **Discrepancy Cause:** Exactly **1,533 spans** belong to the canonical RAGTruth test set (`data/processed/ragtruth/test.jsonl`).
- **Audit Proof:**
  - Raw `response.jsonl` (train slice): **12,756 spans**.
  - Processed `ragtruth/train.jsonl`: **12,756 spans**.
  - `sft_v1` preserved spans: **12,756 spans**.
  - `sft_v2/spans` preserved spans: **12,756 spans** (10,082 train, 2,674 validation).
  - Quarantined test set spans: **1,533 spans**.
- **Conclusion:** **Zero spans lost or corrupted.** Test set quarantine strictly preserved.

---

## 6. Span Offset Exactness & Character Slicing Verification (`sft_v2/spans`)

Every single span was tested via character slicing:
$$\text{candidate\_response}[\text{start} : \text{end}] == \text{text}$$
- **Total Spans Verified:** **12,756 spans**.
- **Exact Matches:** **12,756 spans (100.00%)**.
- **Mismatches / Boundary Inversions:** **0 (0.00%)**.
- **Factual Responses:** All 8,369 factual responses contain empty span lists (`[]`).

---

## 7. Split Isolation & Leakage Remediation Audit

1. **RAGTruth Duplicate Document (`12084` vs `12085`):** Both evaluate to the same SHA-256 hash and land together in `train.jsonl`. Train-val document overlap is **0.00%**.
2. **HaluEval Passage Quarantine:** Exactly 26 test-leaking records and 26 train-val leaking records were quarantined into `exclusion_manifest.json`. Train-val-test passage overlap is **0.00%**.
3. **Retrieval Quarantine:** HotpotQA (7,405 records) and MS MARCO (10,047 records) are **100% quarantined (0 records in `sft_v2`)**.

---

## 8. Generative Target Capability Assessment

- **Direct Binary JSON Generation:** **READY.** Schema supports serialized JSON verdicts.
- **Atomic Claim Extraction:** **BLOCKED.** Zero proposition decomposition targets present.
- **Evidence Citation Generation:** **BLOCKED.** Zero numbered passage citations present.
- **Five-Outcome Verdict Generation:** **BLOCKED.** Only binary labels present.
- **Chain-of-Thought Reasoning (`<think>`):** **BLOCKED.** Zero CoT traces present; teacher distillation required.

---

## 9. G3 Supervision Gap Re-Verification (`sft_v2/g3_readiness`)

- **Zero Fabricated Records:** Verified that `train.jsonl` and `validation.jsonl` do not exist in `sft_v2/g3_readiness/`.
- **Supervision Gaps Confirmed:** `PARTIALLY_SUPPORTED` (0 records), `INSUFFICIENT_EVIDENCE` (0 records), and `UNCERTAIN` (0 records) lack raw supervision.
- **G3 Status:** Formally **BLOCKED** until the 3-stage human annotation protocol is executed.

---

## 10. Master Acceptance Matrix

```json
{
  "track": "Track 2",
  "step": "Step 2.2.1",
  "title": "Independent SFT Remediation Acceptance Audit",
  "overall_verdict": "INDEPENDENTLY_VERIFIED",
  "objectives": {
    "binary_hallucination_classification": {
      "verdict": "READY",
      "authorized": true,
      "train_records": 26054,
      "val_records": 5984,
      "leakage": "0.00%_ZERO_DOCUMENT_LEAKAGE"
    },
    "evidence_grounded_3way_nli": {
      "verdict": "READY",
      "authorized": true,
      "train_records": 10815,
      "val_records": 2662,
      "leakage": "0.00%_ZERO_DOCUMENT_LEAKAGE"
    },
    "span_level_hallucination_detection": {
      "verdict": "READY",
      "authorized": true,
      "train_records": 12072,
      "val_records": 3018,
      "offsets": "100.00%_EXACT_MATCH (12,756 spans)"
    },
    "full_five_outcome_g3_verification": {
      "verdict": "BLOCKED",
      "authorized": false,
      "fabricated_records": 0,
      "status": "SUPERVISION_GAP_DOCUMENTED_NO_FABRICATION"
    },
    "generative_structured_verification": {
      "verdict": "CONDITIONALLY_READY",
      "authorized": true,
      "scope": "Direct JSON only; reasoning traces blocked pending teacher distillation"
    }
  }
}
```

