# TrustRAG — Track 2, Step 3.1.1: Consolidated Independent CPU Environment Acceptance Audit

**Assessment Stage:** Track 2, Step 3.1.1  
**Auditor:** Independent ML Infrastructure & Dataset Integrity Auditor  
**Date:** November 14, 2026  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Untouched)  

---

## Table of Contents
1. [Executive Audit Verdict & Findings](#1-executive-audit-verdict--findings)
2. [Resolution of the Step 3.1 Gap (Environment Ready vs Model Absence)](#2-resolution-of-the-step-31-gap-environment-ready-vs-model-absence)
3. [Repository Integrity & Environment Census](#3-repository-integrity--environment-census)
4. [Critical Pilot Validity Audit & Deconstruction](#4-critical-pilot-validity-audit--deconstruction)
5. [Dependency Compatibility & Interface Audit](#5-dependency-compatibility--interface-audit)
6. [Dataset Integrity Re-Verification (18/18 Files)](#6-dataset-integrity-re-verification-1818-files)
7. [Resource Safety Analysis & Real DeBERTa Feasibility](#7-resource-safety-analysis--real-deberta-feasibility)
8. [Final Readiness Determination & Actionable Prerequisites](#8-final-readiness-determination--actionable-prerequisites)

---

## 1. Executive Audit Verdict & Findings

This independent acceptance audit evaluated whether Track 2 Step 3.1 genuinely establishes CPU training readiness for TrustRAG's objective-specific encoder models:
- **Objective A:** Binary classification
- **Objective B:** Three-way NLI
- **Objective C:** Span extraction

### Final Audit Verdict: `CONDITIONALLY_READY`

The audit resolves the apparent contradiction in Step 3.1 between claiming `ENVIRONMENT_READY` and confirming the absence of `microsoft/deberta-v3-small` pretrained weights:
- **Environment Infrastructure is Ready:** The dedicated environment (`.venv-train`) has a fully verified, CPU-optimized installation of PyTorch (`2.14.1+cpu`), Transformers (`5.20.2`), and Accelerate (`1.15.0`).
- **The Feasibility Pilot Used a Substitute Toy Model:** The 3-step pilot did not execute on the 141.9M parameter `microsoft/deberta-v3-small` model or its tokenizer. Instead, it ran on a miniature 2-layer, 128-hidden-size toy substitute model with only **475,522 parameters (0.48M)** using synthetic uniform random integers.
- **Pilot Classification:** The pilot must be classified as a **Generic PyTorch CPU Runtime Smoke Test**, and **NOT** an empirical DeBERTa feasibility benchmark.
- **Pretrained Weights Remain Unstaged:** In strict adherence to project offline policy, weights were not downloaded. Full training is conditionally blocked until weights are staged out-of-band.

### Objective-Specific Readiness Breakdown:

| Objective | Dataset Status (`sft_v2`) | Runtime Environment | Model Staging Status | Audit Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Objective A: Binary Classification** | `READY` (32,038 records) | `READY` (Python 3.10 CPU) | `PENDING_STAGING` | **`CONDITIONALLY_READY`** |
| **Objective B: 3-Way NLI** | `READY` (13,477 records) | `READY` (Python 3.10 CPU) | `PENDING_STAGING` | **`CONDITIONALLY_READY`** |
| **Objective C: Span Extraction** | `READY` (15,090 records) | `READY` (Python 3.10 CPU) | `PENDING_STAGING` | **`CONDITIONALLY_READY`** |
| **Objective D: G3 5-Outcome** | `BLOCKED` (Supervision Gap) | `READY` (Infrastructure ready) | `BLOCKED` (Dataset gap) | **`BLOCKED`** |
| **Objective E: Generative Structured SRM**| `BLOCKED` (No CoT Traces) | `NOT_SUPPORTED` (Requires CUDA) | `BLOCKED` (Host OOM) | **`BLOCKED`** |

---

## 2. Resolution of the Step 3.1 Gap (Environment Ready vs Model Absence)

The apparent gap between declaring `ENVIRONMENT_READY` while pretrained weights are absent is resolved by separating the **runtime platform readiness** from **model artifact readiness**:

1. **Platform Readiness (`READY`):**
   The execution environment possesses all required binaries, C++ shared libraries, PyTorch CPU engines, fast tokenizers, and dataset parsers needed to execute forward and backward passes.
2. **Model Artifact Readiness (`PENDING_STAGING`):**
   Under `src/trustrag/config/engine_config.py`, `local_files_only: True` forbids automatic background downloads. Because no weights were staged on disk, no pretrained model could be instantiated.
3. **Pilot Scope Reconciliation:**
   The Step 3.1 pilot verified that autograd, loss calculation, backward propagation, and AdamW optimizer steps run without crashes on the host CPU. However, because it used a 0.48M parameter model and synthetic token tensors, it did not measure true memory consumption or throughput of the 141.9M parameter target model.

---

## 3. Repository Integrity & Environment Census

### A. Repository States
- **Target Repository (`TrustRag-phase11`):** Active branch `phase-11`, HEAD is `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` (Exact match).
- **Protected Phase 10 Baseline (`TrustRag`):** Active branch `phase-10`, HEAD is `e65bcc80aac634900d1f8e343880fddf66cec168` (**100% UNTOUCHED**).

### B. Environment Isolation
- **Dedicated Environment (`/home/aditya/rags/.venv-train`):**
  - Python: `3.10.22` (`/usr/bin/python3.10`)
  - PyTorch: `2.14.1+cpu` (`CUDA available: False`)
  - Transformers: `5.20.2`
  - Accelerate: `1.15.0`
  - Scikit-Learn: `1.7.2`
  - SentencePiece: `0.2.3`
  - Tokenizers: `0.23.3`
- **Primary Project Environment (`/home/aditya/rags/.venv`):**
  - Python: `3.14.9`
  - PyTorch: **NOT INSTALLED** (Completely unmodified).

### C. Host Hardware Status
- **Host CPU:** 13th Gen Intel(R) Core(TM) i7-1355U (10 Cores, 12 Threads).
- **Host Memory:** Total RAM 15.29 GB; **Available RAM: 3.18 GB**.
- **Swap Status:** Total Swap 5.86 GB; **Free Swap: 48 kB (99.99% consumed)**.
- **Host Storage:** 44.54 GB available on `/home/aditya` (294.23 GB filesystem).
- **GPU:** None (`nvidia-smi` missing, 0 GB VRAM). Pure CPU platform.

---

## 4. Critical Pilot Validity Audit & Deconstruction

An exhaustive line-by-line inspection of `tools/evaluation/run_bounded_cpu_pilot.py` and `bounded_pilot_results.json` answers the seven mandated questions:

### 1. Was the actual `microsoft/deberta-v3-small` architecture loaded?
**NO.** Lines 76–83 instantiated a 2-layer, 128-hidden-size toy config:
```python
cfg = DebertaV2Config(
    vocab_size=1000,
    hidden_size=128,
    num_hidden_layers=2,
    num_attention_heads=4,
    intermediate_size=256,
    num_labels=2,
)
```
- **Pilot Toy Model Parameters:** **475,522 (0.48M)**.
- **Canonical DeBERTa-v3-small Parameters:** **141,894,914 (141.89M)** (6 layers, 768 hidden, 12 heads, 3072 intermediate, 128,100 vocabulary).
- **Scale Discrepancy:** The actual target model is **298.4 times larger**.

### 2. Were pretrained DeBERTa weights loaded?
**NO.** Lines 55–57 explicitly noted that pretrained weights are absent locally and were not fetched. The model was initialized with random Gaussian weights.

### 3. Was a substitute model used?
**YES.** A randomly initialized 2-layer toy substitute model of 475,522 parameters was used.

### 4. Were real records from `sft_v2/binary/train.jsonl` consumed?
**PARTIALLY.** Lines 62–70 read 5 records to extract `example_id` and `binary_label`, but the text fields were never passed into the model.

### 5. Were actual DeBERTa tokenizer and sequence-processing steps executed?
**NO.** Lines 98–100 generated synthetic uniform random integers via `torch.randint(0, 1000)`. The SentencePiece tokenizer was never invoked.

### 6. Does the reported 420.6 MB peak RSS include the target model and its tokenizer?
**NO.** The 420.6 MB peak RSS represents the Python 3.10 runtime + imported PyTorch shared libraries + the 0.48M parameter toy model. The actual 141.9M parameter model and tokenizer will require ~1.5–1.8 GB.

### 7. Can the reported throughput be used to estimate DeBERTa training time?
**NO.** The reported throughput (78.1 tok/s) on a 0.48M toy model cannot estimate a 141.9M parameter model with ~298x higher FLOPs per token.

---

## 5. Dependency Compatibility & Interface Audit

1. **Transformers Compatibility:** `transformers==5.20.2` natively supports DeBERTa-v3 model classes (`DebertaV2ForSequenceClassification`, `DebertaV2ForTokenClassification`) and tokenizer interfaces (`DebertaV2Tokenizer`, `DebertaV2TokenizerFast`).
2. **Tokenizer Backend:** `sentencepiece==0.2.3` and `tokenizers==0.23.3` are present and operational.
3. **Zero Package Drift:** No packages were installed, modified, or deleted during this audit.

---

## 6. Dataset Integrity Re-Verification (18/18 Files)

Every file across `data/processed/sft_v2/` was independently re-hashed and matched its authoritative SHA-256 digest:

| Dataset Subdirectory | Files Verified | SHA-256 Digest Status | Records Verified |
| :--- | :--- | :--- | :--- |
| **`sft_v2/binary/`** | 5 files (`train`, `val`, `quarantine`, `manifest`, `schema`) | ✅ 5/5 MATCH | 26,054 train, 5,984 val, 52 quarantined |
| **`sft_v2/nli/`** | 5 files (`train`, `val`, `quarantine`, `manifest`, `schema`) | ✅ 5/5 MATCH | 10,815 train, 2,662 val, 18,613 quarantined |
| **`sft_v2/spans/`** | 5 files (`train`, `val`, `quarantine`, `manifest`, `schema`) | ✅ 5/5 MATCH | 12,072 train, 3,018 val, 12,756 ground-truth spans |
| **`sft_v2/g3_readiness/`** | 3 files (`gap_doc`, `manifest`, `schema`) | ✅ 3/3 MATCH | 32,090 unannotated instances documented |

**Total:** **18 of 18 files** matched authoritative checksums with zero drift.

---

## 7. Resource Safety Analysis & Real DeBERTa Feasibility

### A. Four-Tier Readiness Analysis
1. **Generic PyTorch Runtime:** `READY` (Verified).
2. **Pretrained Encoder Loading:** `BLOCKED` (Missing weights on disk).
3. **Forward/Backward Training:** `CONDITIONALLY_READY` (Math validated; single-step real pilot pending).
4. **Full Multi-Epoch Training:** `CONDITIONALLY_READY` (Requires memory guardrails).

### B. Host Memory Envelope vs Actual DeBERTa Footprint
- **Host Available RAM:** **3.18 GB**.
- **Host Free Swap:** **48 kB (99.99% consumed)**.
- **DeBERTa-v3-Small True Memory Footprint (FP32 AdamW, $B=8, S=512$):**
  - Model weights: ~568 MB
  - Gradients: ~568 MB
  - AdamW states: ~1,136 MB
  - Activations: ~220 MB
  - **Total Training RSS:** **$\approx 1.5\text{ to }1.8\text{ GB}$**.
- **Assessment:** Training fits within the 3.18 GB available RAM (leaving ~1.4 GB buffer), but leaves zero room for unconstrained memory leaks. Physical batch size must not exceed 8.

---

## 8. Final Readiness Determination & Actionable Prerequisites

### Comprehensive Verdict: `CONDITIONALLY_READY`

- **Generic Environment Platform:** `ENVIRONMENT_READY`
- **Objective A (Binary Classification):** `CONDITIONALLY_READY`
- **Objective B (3-Way NLI):** `CONDITIONALLY_READY`
- **Objective C (Span Extraction):** `CONDITIONALLY_READY`
- **Objective D (G3 5-Outcome):** `BLOCKED` (Supervision gap)
- **Objective E (Generative SRM):** `BLOCKED` (Hardware limitation)

### Mandatory Prerequisites for Track 2 Step 3.2:
1. **Explicit Weight Staging:** Secure authorization to stage the snapshot for `microsoft/deberta-v3-small` into `/home/aditya/rags/models/pretrained/deberta-v3-small/`.
2. **Full-Architecture Single-Step Pilot:** Execute a genuine single-example pilot using the actual loaded 141.9M model and real SentencePiece tokenizer to measure true resident memory (RSS) and step latency on host CPU.
3. **Freeze Checksums:** Compute and commit SHA-256 digests in a local manifest before training.
4. **Independent Review Approval:** Wait for independent review authorization before initiating multi-epoch training.
