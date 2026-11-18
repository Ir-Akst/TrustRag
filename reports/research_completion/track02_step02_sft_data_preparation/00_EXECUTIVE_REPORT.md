# TrustRAG Track 2, Step 2: Evidence-Grounded SFT Data Preparation — Executive Audit Report

## 1. Executive Summary

- **Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, baseline HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)
- **Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, baseline HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, untouched)
- **Step Objective:** Implement a reproducible, research-grade, CPU-only data preparation pipeline for evidence-grounded Supervised Fine-Tuning (SFT), resolving dataset formatting blockers identified in Track 2 Step 1.
- **Pipeline Implementation:** [`tools/data_prep/prepare_sft_dataset.py`](file:///home/aditya/rags/TrustRag-phase11/tools/data_prep/prepare_sft_dataset.py)
- **Prepared Dataset Location:** [`data/processed/sft_v1/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v1/)
- **Final Audit Verdict:** **`SFT_DATA_CONDITIONALLY_READY`**

---

## 2. Definitive Record and Split Census

The SFT dataset (`sft_v1`) integrates canonical human-annotated records from **RAGTruth** and **HaluEval QA**, strictly partitioned to guarantee zero source document leakage:

| Dataset | Split | Total Records | FACTUAL | HALLUCINATED | Unique Source IDs | Source Leakage Rate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **RAGTruth** | train | 12,072 | 8,970 | 3,102 | 2,012 | 0.00% (0 / 2,012) |
| **RAGTruth** | validation | 3,018 | 2,234 | 784 | 503 | 0.00% (0 / 503) |
| **HaluEval QA** | train | 14,000 | 7,000 | 7,000 | 7,000 | 0.00% (0 / 7,000) |
| **HaluEval QA** | validation | 3,000 | 1,500 | 1,500 | 1,500 | 0.00% (0 / 1,500) |
| **Combined SFT** | **train** | **26,072** | **15,970** | **10,102** | **9,012** | **0.00% (0 / 9,012)** |
| **Combined SFT** | **validation** | **6,018** | **3,734** | **2,284** | **2,003** | **0.00% (0 / 2,003)** |
| **Combined Total** | **sft_v1** | **32,090** | **19,704** | **12,386** | **11,015** | **0.00%** |

### Benchmark Quarantine Compliance
- **RAGTruth Test Set (2,700 records, 450 sources):** Strictly quarantined. Overlap with `sft_v1` train/val is **0 records (0.00%)**.
- **HaluEval Test Set (3,000 records, 1,500 sources):** Strictly quarantined. Overlap with `sft_v1` train/val is **0 records (0.00%)**.
- **HotpotQA (7,405 records):** Quarantined retrieval-only benchmark. Overlap with `sft_v1` is **0 records (0.00%)**.
- **MS MARCO (10,047 records):** Quarantined retrieval-only benchmark. Overlap with `sft_v1` is **0 records (0.00%)**.

---

## 3. Blocker Status & Resolution Analysis

| Step 1 Audit Blocker | Status | Resolution Details |
| :--- | :---: | :--- |
| **Blocker 1: RAGTruth 0-byte `validation.jsonl`** | **RESOLVED** | The canonical upstream RAGTruth release (Niu et al., 2024) only provides `train` (15,090) and `test` (2,700). We executed an 80/20 source-grouped partition of `train.jsonl` with fixed seed 42. Exactly 2,012 source documents (12,072 examples) form the training split and 503 source documents (3,018 examples) form the validation split. Zero document overlap exists between splits or with the 450 test sources. |
| **Blocker 2: Non-standardized schemas & missing target format** | **RESOLVED** | Defined canonical Pydantic model `SFTExampleRecord` with strict `extra="forbid"`. Targets are deterministically structured JSON objects derived directly from original human annotations (verdicts, conflict types, and span annotations). Zero synthetic reasoning traces were hallucinated. |
| **Blocker 3: Generative reasoning traces (`<think>` tags)** | **CONDITIONAL** | Research paper review confirmed that TrustRAG G3 (Page 5, Section 6.3) and HalluGuard specify evidence grounding and verification targets, not freeform CoT. Synthesizing unverified chain-of-thought traces would violate research integrity rules. For discriminative/NLI fine-tuning (verdict classification, evidence coverage, span conflict detection), the dataset is fully ready. For generative reasoning models requiring explicit `<think>` traces, a teacher distillation protocol must be authorized. |
| **Blocker 4: Hardware and Training Scripts** | **DEFERRED** | Preserved in Step 2; model training and GPU compute are out of scope for Step 2 and remain deferred to Track 2 Step 3+. |

---

## 4. Verification and Regression Testing

- **Data Prep Unit Suite:** [`tests/unit/test_track02_step02_sft_data_prep.py`](file:///home/aditya/rags/TrustRag-phase11/tests/unit/test_track02_step02_sft_data_prep.py) (8/8 passed in 0.50s).
- **Full Unit Test Suite:** 693 passed in 24.43s (zero regressions).
- **Static Type Checking (`mypy`):** `src`, `tools/data_prep`, and unit tests passed with 0 errors.
- **Linter (`ruff`):** 100% compliant, zero warnings.
- **Bytecode Compilation (`compileall`):** 100% clean across all modules.
- **Cryptographic Integrity:** All SHA-256 digests in [`data/processed/sft_v1/checksums.sha256`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v1/checksums.sha256) match bit-for-bit.

---

## 5. Audit Verdict Justification

**Verdict: `SFT_DATA_CONDITIONALLY_READY`**

- **Why Conditioned?**
  The dataset is unconditionally ready for **discriminative/NLI fine-tuning** (training G3 output verifiers, claim classification, and hallucination span detectors). However, if the project intends to train an autoregressive generative model outputting explicit `<think>` reasoning traces, teacher distillation must first be executed.

