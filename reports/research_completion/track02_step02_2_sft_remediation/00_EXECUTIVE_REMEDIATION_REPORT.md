# TrustRAG Track 2, Step 2.2: Objective-Specific SFT Dataset Remediation — Executive Report

## 1. Executive Summary & Audit Preflight

- **Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, baseline HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)
- **Protected Phase 10 Baseline:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, baseline HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, **UNTOUCHED**)
- **Immutable Historical Baseline:** [`data/processed/sft_v1/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v1/) (**PRESERVED UNCHANGED**, all checksums match)
- **Remediated Datasets Location:** [`data/processed/sft_v2/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/)
- **Pipeline Implementation:** [`tools/data_prep/prepare_sft_v2_remediated.py`](file:///home/aditya/rags/TrustRag-phase11/tools/data_prep/prepare_sft_v2_remediated.py)

---

## 2. Objective-Specific Dataset Inventory

Rather than attempting to force all learning targets into a single collapsed schema, `sft_v2` provides **separately versioned, objective-specific datasets** with strict leakage remediation and explicit exclusion manifests:

| Dataset Objective | Output Directory | Train Records | Validation Records | Excluded Records | Target Label Scheme | Usable For Training Now? |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **1. Binary Classification** | [`data/processed/sft_v2/binary/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/) | 26,054 | 5,984 | 52 | `FACTUAL`, `HALLUCINATED` | **READY** |
| **2. Evidence-Grounded NLI** | [`data/processed/sft_v2/nli/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/) | 10,815 | 2,662 | 18,613 | `ENTAILMENT`, `CONTRADICTION`, `NEUTRAL` | **READY** |
| **3. Span-Level Detection** | [`data/processed/sft_v2/spans/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/spans/) | 12,072 | 3,018 | 17,000 | Verified character spans (`start`, `end`, `type`) | **READY** |
| **4. G3 Five-Outcome Verification** | [`data/processed/sft_v2/g3_readiness/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/g3_readiness/) | **0** | **0** | N/A | **0 records fabricated** (Gap specification only) | **BLOCKED** |
| **5. Generative Structured Verification** | [`data/processed/sft_v2/binary/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/) | 26,054 | 5,984 | 52 | Structured JSON generation | **CONDITIONALLY_READY** |

---

## 3. Key Remediation Accomplishments

### 3.1 RAGTruth Duplicate Document Remediation
- **Audit Discovery from Step 2.1:** RAGTruth upstream corpus contained an identical CNN news article under two distinct source IDs (`12084` and `12085`), which landed across train and validation in `sft_v1`.
- **Remediation in `sft_v2`:** Grouping is now enforced by normalized document text hash (`SHA-256`). Both `12084` and `12085` are assigned together to the training partition.
- **Verification:** Overlap between train and validation document texts is **0.00% (0 / 2,514 documents)**.

### 3.2 HaluEval Test Set Quarantine & Leakage Remediation
- **Audit Discovery from Step 2.1:** Upstream HaluEval QA had 18 train records (9 pairs) and 8 validation records (4 pairs) sharing context paragraphs with the canonical test set, plus 26 validation records sharing paragraphs with train.
- **Remediation in `sft_v2`:** Exactly **52 records** were quarantined and logged in [`exclusion_manifest.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/exclusion_manifest.json).
- **Verification:** Overlap between HaluEval train, validation, and test documents is **0.00%**.

### 3.3 Semantic Remediation of NLI Labels
- **Defect in `sft_v1`:** All non-factual examples were collapsed to `CONTRADICTED`, mislabeling 3,332 unmentioned info records as contradictions.
- **Remediation in `sft_v2/nli`:**
  - `label == FACTUAL` $\rightarrow$ `ENTAILMENT` (8,369 total records).
  - Pure Conflict (`Evident Conflict`, `Subtle Conflict`) $\rightarrow$ `CONTRADICTION` (1,776 total records).
  - Pure Baseless Info (`Evident Baseless Info`, `Subtle Baseless Info`) $\rightarrow$ `NEUTRAL` (3,332 total records).
  - Mixed Conflict & Baseless Info (1,613 records) are **excluded** and logged in `exclusion_manifest.json`.
  - HaluEval QA (17,000 records) is **excluded** from NLI due to lack of defensible 3-way supervision.

### 3.4 Span Offset Exactness
- **Verification in `sft_v2/spans`:** All 12,756 character spans in RAGTruth were verified against the candidate responses:
  $$\forall s: \quad \text{candidate\_response}[s.\text{start} : s.\text{end}] == s.\text{text}$$
- **Mismatches:** **0 (100.00% exact character match)**.
- HaluEval QA (0 spans) is strictly excluded to prevent zero-loss masking bugs.

### 3.5 Rejection of Fabricated Five-Outcome G3 Records
- Zero synthetic G3 records were created.
- A comprehensive supervision gap report was produced in [`data/processed/sft_v2/g3_readiness/G3_SUPERVISION_GAP_REPORT.md`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/g3_readiness/G3_SUPERVISION_GAP_REPORT.md).

---

## 4. Final Objective Readiness Verdicts

1. **Binary Hallucination Classification:** **`READY`**
2. **Evidence-Grounded NLI:** **`READY`** (Clean 3-way RAGTruth dataset; HaluEval quarantined)
3. **Span-Level Hallucination Detection:** **`READY`** (RAGTruth-only with 100% verified offsets)
4. **Full Five-Outcome G3 Verification:** **`BLOCKED`** (Supervision gap documented; zero records fabricated)
5. **Generative Structured Verification:** **`CONDITIONALLY_READY`** (Ready for JSON generation; `<think>` traces blocked pending teacher distillation)

