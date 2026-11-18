# TrustRAG Track 2, Step 2.1: Independent SFT Dataset Semantic and Integrity Audit — Executive Verdict

## 1. Audit Identification & Framework

- **Audit Date:** 2026-11-14
- **Auditor Role:** Independent Adversarial ML Data Auditor
- **Audit Mandate:** Perform an independent, read-only empirical audit of `data/processed/sft_v1/`, the transformation pipeline [`tools/data_prep/prepare_sft_dataset.py`](file:///home/aditya/rags/TrustRag-phase11/tools/data_prep/prepare_sft_dataset.py), and the Step 2 completion claims. Do not trust previous report summaries; re-verify all claims from raw source records.
- **Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)
- **Protected Phase 10 Baseline:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, **UNTOUCHED**)
- **Final Overall Audit Verdict:** **`CONDITIONALLY_VERIFIED`**

---

## 2. Core Audit Findings & Discrepancies

### 2.1 Discrepancy in Step 2 Executive Report Label Census
The previous Step 2 executive report ([`00_EXECUTIVE_REPORT.md`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step02_sft_data_preparation/00_EXECUTIVE_REPORT.md)) reported an erroneous label census for RAGTruth:
- *Reported:* RAGTruth Train FACTUAL: 8,970, HALLUCINATED: 3,102.
- *Actual Independent Verification:*
  - **RAGTruth Train (12,072 records):** **6,660 FACTUAL**, **5,412 HALLUCINATED**.
  - **RAGTruth Validation (3,018 records):** **1,709 FACTUAL**, **1,309 HALLUCINATED**.
  - **HaluEval Train (14,000 records):** **7,000 FACTUAL**, **7,000 HALLUCINATED**.
  - **HaluEval Validation (3,000 records):** **1,500 FACTUAL**, **1,500 HALLUCINATED**.
  - **Total SFT Train (26,072 records):** **13,660 FACTUAL** (52.4%), **12,412 HALLUCINATED** (47.6%).
  - **Total SFT Validation (6,018 records):** **3,209 FACTUAL** (53.3%), **2,809 HALLUCINATED** (46.7%).
*Note:* The actual machine-generated [`dataset_manifest.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v1/dataset_manifest.json) contained the correct counts; the error was an unverified manual copy-paste in the Step 2 executive text.

### 2.2 Semantic Conflation: Baseless Information vs. Direct Contradiction
The Step 2 pipeline automatically assigned `verdict: "CONTRADICTED"` to **all** hallucinated examples:
1. In **RAGTruth**, human annotators distinguished between `Evident Conflict` (direct contradiction) and `Evident Baseless Info` (information absent from the context).
   - In training, **2,678 records (22.18% of RAGTruth train)** contain **only Baseless Info** and zero conflict with the text.
   - In validation, **654 records (21.67% of RAGTruth val)** contain **only Baseless Info**.
   - **Total of 3,332 records** that represent *unmentioned/unsupported* facts were forcibly assigned `verdict: "CONTRADICTED"`.
2. In **HaluEval QA**, ChatGPT was prompted to introduce "factual errors or unsupported claims".
   - Empirical lexical analysis reveals that **51.8% of hallucinated answers** introduce completely unmentioned external entities rather than contradicting passage tokens.
   - All 17,000 HaluEval hallucinated pairs across train and validation were unconditionally labeled `CONTRADICTED`.

### 2.3 G3 Five-Outcome Taxonomy Collapse
TrustRAG G3 Output Guardrail defines a five-outcome decision framework:
`SUPPORTED`, `CONTRADICTED`, `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`, `UNCERTAIN`.
In `sft_v1`:
- `SUPPORTED`: 16,869 (52.6%)
- `CONTRADICTED`: 15,221 (47.4%)
- `PARTIALLY_SUPPORTED`: **0 (0.00%)**
- `INSUFFICIENT_EVIDENCE`: **0 (0.00%)**
- `UNCERTAIN`: **0 (0.00%)**

Training a neural model on `sft_v1` as a "G3 verifier" will teach the model an artificial, pathological equivalence: **absence of evidence = contradiction**.

---

## 3. Disaggregated Training Objective Verdicts

| Training Objective | Verdict | Supervision Available in `sft_v1` | Missing Supervision / Blockers | Usable As-Is? |
| :--- | :---: | :--- | :--- | :---: |
| **1. Binary Hallucination Classification** | **`VERIFIED`** | 32,090 balanced examples (16,869 Factual, 15,221 Hallucinated). | None. Binary faithfulness is authoritative. | **YES** |
| **2. Evidence-Grounded NLI (3-Way)** | **`CONDITIONALLY_VERIFIED`** | Entailment (16,869) and Contradiction (~5,500 pure conflicts). | 3,332 RAGTruth baseless info records and ~8,800 HaluEval unmentioned cases are mislabeled as Contradiction instead of Neutral. | **NO** (Requires re-mapping baseless info to Neutral/Insufficient Evidence) |
| **3. Span-Level Hallucination Detection** | **`CONDITIONALLY_VERIFIED`** | 14,289 human annotated character spans with conflict metadata in RAGTruth. | HaluEval QA contains **0 span annotations** (empty span lists despite hallucinated label). | **NO** (Must restrict token loss to RAGTruth only) |
| **4. Full 5-Outcome G3 Verification** | **`NOT_VERIFIED`** | Only `SUPPORTED` and `CONTRADICTED`. | **0 records** for `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`, and `UNCERTAIN`. | **NO** (Missing 60% of target taxonomy) |
| **5. Generative Structured Verification** | **`CONDITIONALLY_VERIFIED`** | Schema-validated structured JSON output targets across all 32,090 records. | Reasoning traces (`<think>` tags) are completely absent. | **YES** (For direct JSON generation); **NO** (For CoT reasoning models) |

---

## 4. Overall Auditor Verdict Justification

**Verdict: `CONDITIONALLY_VERIFIED`**

- The pipeline executed deterministically, zero synthetic reasoning traces were fabricated, the Pydantic schema validates with `extra="forbid"`, and test isolation is intact.
- However, `sft_v1` **cannot be authorized for full G3 five-outcome training** without relabeling baseless information and acquiring supervision for partial support and uncertainty.
- It is immediately authorized **only for binary hallucination classification** or **token-level span detection on the RAGTruth subset**.

