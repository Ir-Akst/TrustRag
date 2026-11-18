# TrustRAG Track 2, Step 2.2: Objective-Specific SFT Dataset Remediation — Comprehensive Consolidated Report

**Document Version:** 2.0.0  
**Audit & Remediation Date:** 2026-11-14  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, baseline HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Phase 10 Baseline:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, baseline HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, **UNTOUCHED**)  
**Historical Baseline Status:** [`data/processed/sft_v1/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v1/) (**PRESERVED UNCHANGED**, 5/5 checksums verified)  
**Remediated Objective Datasets:** [`data/processed/sft_v2/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/)  
**Remediation Pipeline Implementation:** [`tools/data_prep/prepare_sft_v2_remediated.py`](file:///home/aditya/rags/TrustRag-phase11/tools/data_prep/prepare_sft_v2_remediated.py)

---

## Table of Contents
1. [Executive Summary & Preflight Verification](#1-executive-summary--preflight-verification)
2. [Objective-Specific Dataset Inventory](#2-objective-specific-dataset-inventory)
3. [Binary Classification Dataset Report (`sft_v2/binary`)](#3-binary-classification-dataset-report-sft_v2binary)
4. [Evidence-Grounded 3-Way NLI Dataset Report (`sft_v2/nli`)](#4-evidence-grounded-3-way-nli-dataset-report-sft_v2nli)
5. [HaluEval Quarantine & Semantic Mapping Policy](#5-halueval-quarantine--semantic-mapping-policy)
6. [RAGTruth Character Span Integrity Report (`sft_v2/spans`)](#6-ragtruth-character-span-integrity-report-sft_v2spans)
7. [Split Isolation & Document Leakage Remediation](#7-split-isolation--document-leakage-remediation)
8. [G3 Supervision Gap & Human Annotation Protocol (`sft_v2/g3_readiness`)](#8-g3-supervision-gap--human-annotation-protocol-sft_v2g3_readiness)
9. [Testing, Quality Assurance & Reproducibility](#9-testing-quality-assurance--reproducibility)
10. [Master Objective Readiness Matrix](#10-master-objective-readiness-matrix)

---

## 1. Executive Summary & Preflight Verification

### 1.1 Scope & Operational Mandate
Following the findings of the Track 2 Step 2.1 independent semantic audit, Step 2.2 remakes the TrustRAG fine-tuning data architecture. Instead of forcing all verification objectives into a single collapsed schema, Step 2.2 introduces **separately versioned, objective-specific training datasets** under `data/processed/sft_v2/`.

The historical baseline dataset (`sft_v1`) remains **strictly preserved and immutable**. Phase 10 baseline is completely untouched.

### 1.2 Mandatory Preflight Verification
- Target Repository HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` on `phase-11` (**VERIFIED**).
- Protected Phase 10 HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168` on `phase-10` (**VERIFIED UNTOUCHED**).
- `sft_v1` Cryptographic Hashes: All 5 files match their historical hashes (`checksums.sha256` verified).
- Step 2.1 Audit Reports: All 9 report files match their cryptographic digests.

---

## 2. Objective-Specific Dataset Inventory

| Dataset Objective | Output Directory | Train Records | Val Records | Excluded Records | Target Label Scheme | Training Readiness Verdict |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **1. Binary Classification** | [`sft_v2/binary/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/) | 26,054 | 5,984 | 52 | `FACTUAL`, `HALLUCINATED` | **`READY`** |
| **2. Evidence-Grounded NLI** | [`sft_v2/nli/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/) | 10,815 | 2,662 | 18,613 | `ENTAILMENT`, `CONTRADICTION`, `NEUTRAL` | **`READY`** |
| **3. Span-Level Detection** | [`sft_v2/spans/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/spans/) | 12,072 | 3,018 | 17,000 | 12,756 character spans (100% verified) | **`READY`** |
| **4. Full 5-Outcome G3** | [`sft_v2/g3_readiness/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/g3_readiness/) | **0** | **0** | N/A | **0 records fabricated** (Gap specification) | **`BLOCKED`** |
| **5. Generative Structured** | [`sft_v2/binary/`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/binary/) | 26,054 | 5,984 | 52 | Structured JSON generation | **`CONDITIONALLY_READY`** |

---

## 3. Binary Classification Dataset Report (`sft_v2/binary`)

### 3.1 Objective Scope
Designed strictly for binary hallucination detection:
$$f(x_{\text{prompt}}, x_{\text{context}}, x_{\text{candidate}}) \rightarrow y \in \{\text{FACTUAL}, \text{HALLUCINATED}\}$$
Binary labels originate directly from source benchmarks and are never derived from G3 five-outcome verdicts.

### 3.2 Schema Definition (`BinaryExampleRecord`)
```python
class BinaryExampleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    example_id: str = Field(description="Unique identifier for binary SFT example")
    source_dataset: Literal["ragtruth", "halueval"] = Field(description="Upstream source corpus")
    source_id: str = Field(description="Original document or query ID")
    split: Literal["train", "validation"] = Field(description="Partition split")
    question_or_claim: str = Field(description="Input prompt, task, or user query")
    context_or_evidence: str = Field(description="Passage or document text")
    candidate_response: str = Field(description="Candidate claim or response")
    binary_label: Literal["FACTUAL", "HALLUCINATED"] = Field(description="Ground truth binary label")
    source_provenance: str = Field(description="Audit trail of label origin")
```

### 3.3 Census & Distribution
- **Train Split (26,054 records):**
  - RAGTruth: 12,072 records (6,660 Factual, 5,412 Hallucinated across 2,011 unique docs).
  - HaluEval: 13,982 records (6,991 Factual, 6,991 Hallucinated across 6,973 unique docs).
  - Combined: 13,651 FACTUAL (52.39%), 12,403 HALLUCINATED (47.61%).
- **Validation Split (5,984 records):**
  - RAGTruth: 3,018 records (1,709 Factual, 1,309 Hallucinated across 503 unique docs).
  - HaluEval: 2,966 records (1,483 Factual, 1,483 Hallucinated across 1,475 unique docs).
  - Combined: 3,192 FACTUAL (53.34%), 2,792 HALLUCINATED (46.66%).
- **Leakage Remediation Exclusions:** 52 records quarantined (18 test-leaking in train, 8 test-leaking in val, 26 train-leaking in val).
- **Document Text Overlap:** **0.00% (0 / 10,962 unique documents)**.

---

## 4. Evidence-Grounded 3-Way NLI Dataset Report (`sft_v2/nli`)

### 4.1 Objective Scope
Designed for 3-way inference classification:
$$f(x_{\text{premise}}, x_{\text{hypothesis}}) \rightarrow y \in \{\text{ENTAILMENT}, \text{CONTRADICTION}, \text{NEUTRAL}\}$$

### 4.2 Definitive RAGTruth NLI Mapping Rules
1. **`label == 'FACTUAL'` (0 spans)** $\rightarrow$ **`ENTAILMENT`** (8,369 total records). Human annotators verified the response is entirely entailed by the document.
2. **Pure Conflict Spans Only** (`Evident Conflict`, `Subtle Conflict` with NO baseless info) $\rightarrow$ **`CONTRADICTION`** (1,776 total records). All spans directly refute the text.
3. **Pure Baseless Info Spans Only** (`Evident Baseless Info`, `Subtle Baseless Info` with NO conflict) $\rightarrow$ **`NEUTRAL`** (3,332 total records). Information introduced is unmentioned in the text, representing neutral/unsupported assertions rather than contradictions.
4. **Mixed Conflict & Baseless Info** $\rightarrow$ **EXCLUDED** (1,613 records). Cannot be collapsed into a single 3-way label without atomic proposition decomposition. Logged in `exclusion_manifest.json`.
5. **HaluEval QA Benchmark** $\rightarrow$ **EXCLUDED** (17,000 records). Quarantined due to conflation of contradiction and unmentioned entities.

### 4.3 Census & Distribution
- **Train Split (10,815 records):** 6,660 ENTAILMENT (61.58%), 1,415 CONTRADICTION (13.08%), 2,740 NEUTRAL (25.34%).
- **Validation Split (2,662 records):** 1,709 ENTAILMENT (64.20%), 361 CONTRADICTION (13.56%), 592 NEUTRAL (22.24%).
- **Total Combined:** **13,477 records** (8,369 Entailment, 1,776 Contradiction, 3,332 Neutral).
- **Exclusion Ledger:** Exactly 18,613 records logged in [`exclusion_manifest.json`](file:///home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/exclusion_manifest.json).

---

## 5. HaluEval Quarantine & Semantic Mapping Policy

1. **Rejection of Pseudo-Labeling:**
   The generation prompt in HaluEval (*Li et al., 2023*) instructed ChatGPT to introduce *"factual errors OR unsupported claims"*. The dataset provides only binary pairs (`right_answer` vs `hallucinated_answer`). Extrapolating sample percentages into per-record ground truth or using an LLM to guess NLI labels without human validation was rejected.
2. **Policy Across Datasets:**
   - **Binary:** Retained with 52 leaking records quarantined.
   - **NLI:** 100% excluded (17,000 records).
   - **Spans:** 100% excluded (0 spans in HaluEval).
   - **G3 Five-Outcome:** 100% excluded.

---

## 6. RAGTruth Character Span Integrity Report (`sft_v2/spans`)

### 6.1 Objective Scope
Designed for token-level sequence labelers and pointer networks:
$$f(x_{\text{context}}, x_{\text{candidate}}) \rightarrow \{(s_i, e_i, \text{label\_type})\}$$

### 6.2 Offset Integrity Verification
Every single span was verified by character slicing:
$$\text{candidate\_response}[\text{start} : \text{end}] == \text{text}$$
- **Total Spans Verified:** **12,756 spans** (10,248 in train, 2,508 in validation).
- **Exact Slicing Matches:** **12,756 spans (100.00%)**.
- **Mismatches / Corrupt Offsets:** **0 (0.00%)**.

### 6.3 Census & Multi-Span Breakdown
- **Train Split:** 12,072 records (6,660 factual with empty spans, 5,412 hallucinated with 10,248 verified spans).
- **Validation Split:** 3,018 records (1,709 factual with empty spans, 1,309 hallucinated with 2,508 verified spans).
- **Total Combined:** **15,090 records** (8,369 factual, 6,721 hallucinated).
- **Spans per Response:** 1 span (3,365), 2 spans (1,811), 3 spans (868), 4 spans (398), 5+ spans (279).

---

## 7. Split Isolation & Document Leakage Remediation

1. **RAGTruth Article Duplication Remediated:**
   - Source IDs `12084` and `12085` contained the exact same CNN news story.
   - Grouping by normalized document text hash (`SHA-256`) placed both IDs together in `train.jsonl`.
   - Result: **0.00% document overlap** between RAGTruth train and validation.
2. **HaluEval Passage Isolation Remediated:**
   - 26 test-leaking records and 26 train-val leaking records were quarantined into `exclusion_manifest.json`.
   - Result: **0.00% passage overlap** between HaluEval train, validation, and test.
3. **Retrieval Benchmark Quarantine:**
   - HotpotQA (7,405 records) and MS MARCO (10,047 records) are **100% quarantined (0 records in `sft_v2`)**.
4. **Canonical Test Set Protection:**
   - Canonical test files in `data/processed/ragtruth/test.jsonl` and `data/processed/halueval/test.jsonl` remain **strictly untouched**.

---

## 8. G3 Supervision Gap & Human Annotation Protocol (`sft_v2/g3_readiness`)

### 8.1 Executive Position
**Readiness Verdict:** **`BLOCKED (NO DATASET FABRICATION)`**  
Zero synthetic five-outcome G3 training records were fabricated. The project strictly refuses to guess labels for missing classes.

### 8.2 The Supervision Gap
- `SUPPORTED`: Available via factual summaries.
- `CONTRADICTED`: Available via pure conflict spans.
- `PARTIALLY_SUPPORTED`: **0 records** (Requires atomic claim decomposition).
- `INSUFFICIENT_EVIDENCE`: **0 records** (Requires negative retrieval supervision).
- `UNCERTAIN`: **0 records** (Requires conflicting evidence pairs).

### 8.3 Required Protocol Before G3 Training
1. **Atomic Decomposition:** Decompose responses into atomic claims $\{c_1, \dots, c_m\}$.
2. **Claim Verification:** Annotate each claim as `SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, or `UNCERTAIN`.
3. **Formal Aggregation:** Aggregate claim verdicts into response-level outcomes via coverage thresholds.
4. **Independent Adjudication:** Dual-annotator agreement with $\kappa \ge 0.80$.

---

## 9. Testing, Quality Assurance & Reproducibility

### 9.1 Verification Gates
- **Dedicated SFT Remediation Unit Tests:** [`tests/unit/test_track02_step02_2_sft_remediation.py`](file:///home/aditya/rags/TrustRag-phase11/tests/unit/test_track02_step02_2_sft_remediation.py) — **8/8 PASSED** in 1.17s.
- **Historical Baseline Unit Tests:** [`tests/unit/test_track02_step02_sft_data_prep.py`](file:///home/aditya/rags/TrustRag-phase11/tests/unit/test_track02_step02_sft_data_prep.py) — **8/8 PASSED** in 0.63s.
- **Static Typing (`mypy`):** `prepare_sft_v2_remediated.py` and test suite passed with **0 errors**.
- **Linter (`ruff`):** 100% clean, zero warnings.
- **Bytecode Compilation (`compileall`):** Clean compilation across all modules.

### 9.2 Deterministic Reproduction Commands
```bash
# 1. Execute remediation pipeline
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv/bin/python tools/data_prep/prepare_sft_v2_remediated.py \
    --data-dir data \
    --output-base-dir data/processed/sft_v2 \
    --seed 42 \
    --val-ratio 0.20

# 2. Verify all checksums
(cd data/processed/sft_v2/binary && sha256sum -c checksums.sha256)
(cd data/processed/sft_v2/nli && sha256sum -c checksums.sha256)
(cd data/processed/sft_v2/spans && sha256sum -c checksums.sha256)
(cd data/processed/sft_v2/g3_readiness && sha256sum -c checksums.sha256)

# 3. Run unit tests
PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest tests/unit/test_track02_step02_2_sft_remediation.py -v
```

---

## 10. Master Objective Readiness Matrix

```json
{
  "track": "Track 2",
  "step": "Step 2.2",
  "title": "Objective-Specific SFT Dataset Remediation",
  "timestamp_iso": "2026-11-14T02:26:00Z",
  "baseline_sft_v1": "PRESERVED_UNCHANGED",
  "objectives": {
    "binary_hallucination_classification": {
      "verdict": "READY",
      "location": "data/processed/sft_v2/binary/",
      "train_records": 26054,
      "validation_records": 5984,
      "total_records": 32038,
      "quarantined_exclusions": 52,
      "leakage": "0.00%_ZERO_DOCUMENT_LEAKAGE"
    },
    "evidence_grounded_nli": {
      "verdict": "READY",
      "location": "data/processed/sft_v2/nli/",
      "train_records": 10815,
      "validation_records": 2662,
      "total_records": 13477,
      "quarantined_exclusions": 18613,
      "leakage": "0.00%_ZERO_DOCUMENT_LEAKAGE"
    },
    "span_level_hallucination_detection": {
      "verdict": "READY",
      "location": "data/processed/sft_v2/spans/",
      "train_records": 12072,
      "validation_records": 3018,
      "total_records": 15090,
      "quarantined_exclusions": 17000,
      "offset_verification": "100.00%_EXACT_MATCH (12,756 spans)"
    },
    "full_five_outcome_g3_verification": {
      "verdict": "BLOCKED",
      "location": "data/processed/sft_v2/g3_readiness/",
      "train_records": 0,
      "validation_records": 0,
      "fabricated_records": 0,
      "status": "SUPERVISION_GAP_DOCUMENTED_NO_FABRICATION"
    },
    "generative_structured_verification": {
      "verdict": "CONDITIONALLY_READY",
      "status": "VALID_FOR_DIRECT_JSON_BLOCKED_FOR_REASONING_TRACES"
    }
  }
}
```

