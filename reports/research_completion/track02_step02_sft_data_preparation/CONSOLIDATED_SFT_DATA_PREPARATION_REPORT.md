# TrustRAG Track 2, Step 2: Evidence-Grounded SFT Data Preparation — Comprehensive Consolidated Report

**Document Version:** 1.0.0  
**Audit Date:** 2026-11-14  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, baseline HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Baseline Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, baseline HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, UNTOUCHED)  
**Overall Verdict:** **`SFT_DATA_CONDITIONALLY_READY`**

---

## Table of Contents
1. [Executive Summary & Final Audit Verdict](#1-executive-summary--final-audit-verdict)
2. [Definitive Dataset Census & Split Breakdown](#2-definitive-dataset-census--split-breakdown)
3. [Research Paper Target Format Verification](#3-research-paper-target-format-verification)
4. [SFT Schema Specification & Provenance Rules](#4-sft-schema-specification--provenance-rules)
5. [Dataset Transformation & Processing Mechanics](#5-dataset-transformation--processing-mechanics)
6. [Split Integrity, Zero-Leakage & Quarantine Audit](#6-split-integrity-zero-leakage--quarantine-audit)
7. [Testing, Regression & Reproducibility Verification](#7-testing-regression--reproducibility-verification)
8. [Machine-Readable Readiness Checklist](#8-machine-readable-readiness-checklist)

---

## 1. Executive Summary & Final Audit Verdict

### 1.1 Scope & Objective
This report consolidates the complete research methodology, data preparation pipeline, schema design, leakage verification, and test results for **TrustRAG Track 2, Step 2: Evidence-Grounded SFT Data Preparation**.

The objective of Step 2 was to resolve the data formatting and dataset preparation blockers identified during the Track 2 Step 1 readiness audit, creating a reproducible, research-grade, CPU-only data pipeline for supervised fine-tuning (SFT) of TrustRAG verification models.

### 1.2 Final Audit Verdict: `SFT_DATA_CONDITIONALLY_READY`
- **Why Conditioned?**
  1. **Unconditionally Ready for Discriminative / NLI Fine-Tuning:**
     The pipeline, Pydantic schema, deterministic targets, zero-leakage partitions, and test suite are **100% complete and validated** for training G3 claim verifiers, verdict classifiers, and span conflict detectors.
  2. **Conditionally Ready for Generative CoT Models:**
     If the project intends to train an autoregressive model outputting explicit `<think>` reasoning traces, a verified teacher distillation protocol must first be authorized and executed. Raw human benchmark datasets do not contain CoT traces, and synthesizing unverified traces without a teacher model would violate research integrity.

### 1.3 Step 1 Blocker Resolution Status

| Step 1 Audit Blocker | Status | Resolution Details |
| :--- | :---: | :--- |
| **Blocker 1: RAGTruth 0-byte `validation.jsonl`** | **RESOLVED** | The canonical upstream RAGTruth release (Niu et al., ACL 2024) only provides `train` (15,090) and `test` (2,700). We executed an 80/20 source-grouped partition of `train.jsonl` with fixed seed 42. Exactly 2,012 source documents (12,072 examples) form the training split and 503 source documents (3,018 examples) form the validation split. Zero document overlap exists between splits or with the 450 test sources. |
| **Blocker 2: Non-standardized schemas & missing target format** | **RESOLVED** | Defined canonical Pydantic model `SFTExampleRecord` with strict `extra="forbid"`. Targets are deterministically structured JSON objects derived directly from original human annotations (verdicts, conflict types, and span annotations). Zero synthetic reasoning traces were hallucinated. |
| **Blocker 3: Generative reasoning traces (`<think>` tags)** | **CONDITIONAL** | Research paper review confirmed that TrustRAG G3 (Page 5, Section 6.3) and HalluGuard specify evidence grounding and verification targets, not freeform CoT. Synthesizing unverified chain-of-thought traces would violate research integrity rules. For discriminative/NLI fine-tuning (verdict classification, evidence coverage, span conflict detection), the dataset is fully ready. For generative reasoning models requiring explicit `<think>` traces, a teacher distillation protocol must be authorized. |
| **Blocker 4: Hardware and Training Scripts** | **DEFERRED** | Preserved in Step 2; model training and GPU compute are out of scope for Step 2 and remain deferred to Track 2 Step 3+. |

---

## 2. Definitive Dataset Census & Split Breakdown

The prepared dataset `sft_v1` is stored at [`data/processed/sft_v1/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v1/). It merges canonical records from **RAGTruth** and **HaluEval QA**:

| Dataset | Split | Total Records | FACTUAL | HALLUCINATED | Unique Source IDs | Source Leakage Rate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **RAGTruth** | train | 12,072 | 8,970 | 3,102 | 2,012 | **0.00%** (0 / 2,012) |
| **RAGTruth** | validation | 3,018 | 2,234 | 784 | 503 | **0.00%** (0 / 503) |
| **HaluEval QA** | train | 14,000 | 7,000 | 7,000 | 7,000 | **0.00%** (0 / 7,000) |
| **HaluEval QA** | validation | 3,000 | 1,500 | 1,500 | 1,500 | **0.00%** (0 / 1,500) |
| **Combined SFT** | **train** | **26,072** | **15,970** | **10,102** | **9,012** | **0.00% (0 / 9,012)** |
| **Combined SFT** | **validation** | **6,018** | **3,734** | **2,284** | **2,003** | **0.00% (0 / 2,003)** |
| **Combined Total** | **sft_v1** | **32,090** | **19,704** | **12,386** | **11,015** | **0.00%** |

### Benchmark Quarantine Verification
- **RAGTruth Test Set (2,700 records, 450 sources):** Strictly quarantined. Overlap with `sft_v1` train/val is **0 records (0.00%)**.
- **HaluEval Test Set (3,000 records, 1,500 sources):** Strictly quarantined. Overlap with `sft_v1` train/val is **0 records (0.00%)**.
- **HotpotQA (7,405 records):** Quarantined retrieval-only benchmark. Overlap with `sft_v1` is **0 records (0.00%)**.
- **MS MARCO (10,047 records):** Quarantined retrieval-only benchmark. Overlap with `sft_v1` is **0 records (0.00%)**.

---

## 3. Research Paper Target Format Verification

### 3.1 TrustRAG Paper (`TrustRAG_RAG_Security_Paper.pdf`)
- **Primary Section:** Section 6.3 "Output Guardrail (G3)" (Page 5)
- **Methodology & Mathematical Formulation:**
  - **Atomic Claim Decomposition:** G3 decomposes candidate generation responses into discrete, testable atomic claims:
    $$\mathcal{C}(y) = \{c_1, c_2, \dots, c_m\}$$
  - **Evidence Grounding:** Each claim $c_i$ is evaluated against retrieved evidence passages $\mathcal{D} = \{d_1, \dots, d_k\}$ to determine an alignment status:
    - `SUPPORTED`: Entailed by evidence.
    - `CONTRADICTED`: Directly refuted by evidence.
    - `UNMENTIONED` / `UNCERTAIN`: Absent from evidence passages.
  - **Evidence Coverage Check:** TrustRAG computes factual support coverage $\text{Cov}(y, \mathcal{D})$:
    $$\text{Cov}(y, \mathcal{D}) = \frac{|\{c \in \mathcal{C}(y) : \text{verdict}(c) = \text{SUPPORTED}\}|}{|\mathcal{C}(y)|}$$
    - Paper Page 5 empirical observations: Mean coverage is **0.93** for factual responses and **0.63** for hallucinated responses.
  - **Target Format Finding:** The paper specifies a **verification and evidence coverage framework**, NOT generative `<think>` reasoning traces. Structured outputs detailing claim verdicts and span conflicts are directly aligned with Section 6.3.

### 3.2 HalluGuard & FilterRAG Papers
- **HalluGuard (Evidence-Grounded Self-Correction):** Contrasts candidate responses against context evidence; downstream targets center on grounding verification and span conflict identification.
- **FilterRAG (Context Filtering & Verification):** Focuses on pre-generation evidence precision and post-generation NLI entailment relations (`SUPPORTED` vs `CONTRADICTED`).

### 3.3 Mandatory Requirements vs. Implementation Choices

| Capability | Mandatory Research Requirement? | Empirical Evidence from Literature | TrustRAG `sft_v1` Implementation |
| :--- | :---: | :--- | :--- |
| **Evidence Grounding** | **YES** (Mandatory) | TrustRAG Sec 6.3; HalluGuard Sec 3 | Each example pairs query, context document, candidate response, and grounding label. |
| **Structured JSON Format** | **YES** (Standard) | TrustRAG Sec 6.3; Automated evaluation | All targets serialized as deterministic JSON with `verdict`, `grounding_status`, and conflict details. |
| **Span-Level Conflicts** | **YES** (For RAGTruth) | RAGTruth (Niu et al., 2024) | For hallucinated RAGTruth examples, all annotated human conflict spans are preserved in the target JSON. |
| **Citation References** | **NO** (Optional for G3) | TrustRAG Sec 6.3 | Document source IDs and query metadata are preserved in the schema. |
| **Generative `<think>` Traces** | **NO** (Implementation Choice) | DeepSeek-R1 / Qwen-CoT style | **Omitted in `sft_v1`**. The raw human datasets do not contain CoT traces. Synthesizing unverified traces would violate data integrity rules. |

---

## 4. SFT Schema Specification & Provenance Rules

### 4.1 Pydantic Model Definition
```python
class SFTExampleRecord(BaseModel):
    """Canonical schema for TrustRAG evidence-grounded SFT examples."""

    model_config = ConfigDict(extra="forbid")

    example_id: str = Field(description="Unique identifier for the SFT example")
    source_dataset: str = Field(description="Source benchmark ('ragtruth' or 'halueval')")
    source_id: str = Field(description="Original document or query identifier from source benchmark")
    split: Literal["train", "validation"] = Field(description="Target SFT split ('train' or 'validation')")
    question_or_claim: str = Field(description="User query, prompt, or task specification")
    context_or_evidence: str = Field(description="Passage or document text against which claim is verified")
    candidate_response: str = Field(description="The generated claim or answer evaluated for faithfulness")
    ground_truth_label: Literal["FACTUAL", "HALLUCINATED"] = Field(
        description="Ground-truth binary faithfulness label"
    )
    target: str = Field(description="Structured target verification output derived from original annotations")
    target_provenance: str = Field(description="Explicit description of how target was derived from annotations")
```

### 4.2 Target Serialization Formats

#### RAGTruth Targets
- **Factual Target:**
  ```json
  {"grounding_status": "GROUNDED", "hallucination_spans": [], "verdict": "SUPPORTED"}
  ```
  *Provenance:* `"ragtruth_original_annotations: verified factual summary with zero hallucinated spans"`
- **Hallucinated Target:**
  ```json
  {
    "grounding_status": "HALLUCINATED",
    "hallucination_spans": [{"conflict_type": "Conflict", "meta": "...", "text": "..."}],
    "verdict": "CONTRADICTED"
  }
  ```
  *Provenance:* `"ragtruth_original_annotations: verified hallucination with N annotated span conflicts"`

#### HaluEval QA Targets
- **Factual Target:**
  ```json
  {"grounding_status": "GROUNDED", "source_pair_type": "right_answer", "verdict": "SUPPORTED"}
  ```
  *Provenance:* `"halueval_qa_original_annotations: canonical right_answer grounded in context passage"`
- **Hallucinated Target:**
  ```json
  {"grounding_status": "HALLUCINATED", "source_pair_type": "hallucinated_answer", "verdict": "CONTRADICTED"}
  ```
  *Provenance:* `"halueval_qa_original_annotations: canonical hallucinated_answer conflicting with or unsupported by passage"`

---

## 5. Dataset Transformation & Processing Mechanics

### 5.1 Pipeline Flow
The transformation pipeline implemented in [`tools/data_prep/prepare_sft_dataset.py`](file:///home/aditya/rags/TrustRag-phase11/tools/data_prep/prepare_sft_dataset.py) processes canonical datasets into `sft_v1`:

```
Canonical Preprocessed Data
├── data/processed/ragtruth/train.jsonl (15,090 records, 2,515 sources)
├── data/processed/halueval/train.jsonl  (14,000 records, 7,000 sources)
└── data/processed/halueval/validation.jsonl (3,000 records, 1,500 sources)
                     │
                     ▼
          prepare_sft_dataset.py
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
  RAGTruth 80/20          HaluEval Canonical
  Source Partition         Split Integration
         │                       │
         └───────────┬───────────┘
                     ▼
             Leakage Verifier
                     ▼
          Output: data/processed/sft_v1/
          ├── train.jsonl (26,072)
          └── validation.jsonl (6,018)
```

### 5.2 Class Balance Stability
- **Train Split (26,072 records):** 15,970 FACTUAL (61.25%), 10,102 HALLUCINATED (38.75%).
- **Validation Split (6,018 records):** 3,734 FACTUAL (62.05%), 2,284 HALLUCINATED (37.95%).
- Factual/hallucinated proportions between train and validation match within **0.8%**, ensuring identical distributional balance.

---

## 6. Split Integrity, Zero-Leakage & Quarantine Audit

### 6.1 Source-Level Document Leakage Audit

| Benchmark | Verification Check | Set A | Set B | Overlap Count | Overlap % | Verdict |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **RAGTruth** | Train vs. Validation | `sft_v1` Train Sources | `sft_v1` Val Sources | **0** | **0.00%** | **PASS** |
| **RAGTruth** | Train vs. Test | `sft_v1` Train Sources | Canonical Test Sources | **0** | **0.00%** | **PASS** |
| **RAGTruth** | Validation vs. Test | `sft_v1` Val Sources | Canonical Test Sources | **0** | **0.00%** | **PASS** |
| **HaluEval** | Train vs. Validation | `sft_v1` Train Sources | `sft_v1` Val Sources | **0** | **0.00%** | **PASS** |
| **HaluEval** | Train vs. Test | `sft_v1` Train Sources | Canonical Test Sources | **0** | **0.00%** | **PASS** |
| **HaluEval** | Validation vs. Test | `sft_v1` Val Sources | Canonical Test Sources | **0** | **0.00%** | **PASS** |

### 6.2 Record ID Collision Audit
- `example_id` collisions between train and validation: **0 (0.00%)**.
- Duplicate IDs within splits: **0 (0.00%)**.
- Overlap with benchmark test record IDs: **0 (0.00%)**.
- Retrieval benchmark contamination (HotpotQA / MS MARCO): **0 records (0.00%)**.

---

## 7. Testing, Regression & Reproducibility Verification

### 7.1 Quality Assurance Execution Summary
- **Dedicated SFT Unit Tests:** [`tests/unit/test_track02_step02_sft_data_prep.py`](file:///home/aditya/rags/TrustRag-phase11/tests/unit/test_track02_step02_sft_data_prep.py)
  - Result: **8/8 PASSED in 0.50s**.
- **Full Unit Test Regression Suite:** `pytest tests/unit/ -q`
  - Result: **693/693 PASSED in 24.43s** (zero regressions).
- **Static Type Checking (`mypy`):**
  - `mypy src`: **Success (112 files clean)**.
  - `mypy tools/data_prep/prepare_sft_dataset.py tests/unit/test_track02_step02_sft_data_prep.py`: **Success (2 files clean)**.
- **Linter (`ruff`):** 100% clean, zero errors or warnings.
- **Bytecode Compilation (`compileall`):** 100% clean across all modules.

### 7.2 Deterministic Reproduction Commands
```bash
# 1. Execute SFT dataset pipeline
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv/bin/python tools/data_prep/prepare_sft_dataset.py \
    --data-dir data \
    --output-dir data/processed/sft_v1 \
    --seed 42 \
    --ragtruth-val-ratio 0.20

# 2. Verify dataset checksums
cd /home/aditya/rags/TrustRag-phase11/data/processed/sft_v1
sha256sum -c checksums.sha256

# 3. Run unit tests
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest tests/unit/test_track02_step02_sft_data_prep.py -v
```

---

## 8. Machine-Readable Readiness Checklist

```json
{
  "track": "Track 2",
  "step": "Step 2",
  "title": "Evidence-Grounded SFT Data Preparation",
  "verdict": "SFT_DATA_CONDITIONALLY_READY",
  "readiness_checklist": {
    "ragtruth_validation_split_resolved": "PASSED (80/20 source-grouped partition, seed 42)",
    "halueval_split_integrated": "PASSED (Canonical train 14k, val 3k)",
    "split_isolation_and_zero_leakage": "PASSED (0.00% source document overlap)",
    "test_set_quarantine": "PASSED (RAGTruth & HaluEval test sets strictly excluded)",
    "retrieval_benchmark_quarantine": "PASSED (HotpotQA & MS MARCO strictly excluded)",
    "pydantic_schema_compliance": "PASSED (SFTExampleRecord with extra='forbid')",
    "target_provenance_and_integrity": "PASSED (100% expert human annotations; 0 fake CoT)",
    "unit_testing_and_regressions": "PASSED (8/8 SFT tests passed; 693/693 full regression tests passed)",
    "generative_reasoning_cot_traces": "CONDITIONALLY_READY (Ready for NLI/verification; CoT requires teacher distillation)",
    "hardware_and_training_scripts": "DEFERRED (Track 2 Step 3+)"
  },
  "dataset_summary": {
    "name": "sft_v1",
    "total_records": 32090,
    "train_records": 26072,
    "validation_records": 6018,
    "train_sources": 9012,
    "validation_sources": 2003,
    "train_sha256": "424ba69a38b00a5a3a7be3bf2bcae69738f7127e9095690bdf51649f8749830d",
    "validation_sha256": "f3161e0c8e4a9e5ce6eb9dbf170f3f6c8d20894be6a3e2154316d90ef26ec3ba"
  }
}
```

