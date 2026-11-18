# TrustRAG — Track 2, Step 3.2: Consolidated Model Staging & Integrity Verification Report

**Assessment Stage:** Track 2, Step 3.2  
**Auditor / Engineer:** Senior ML Infrastructure Engineer  
**Date:** November 14, 2026  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Untouched)  

---

## Table of Contents
1. [Executive Summary & Verdict](#1-executive-summary--verdict)
2. [Model Provenance, Lineage & Licensing](#2-model-provenance-lineage--licensing)
3. [Staged Model File Inventory & Technical Specifications](#3-staged-model-file-inventory--technical-specifications)
4. [Authoritative SHA-256 Manifest](#4-authoritative-sha-256-manifest)
5. [Offline Loading & Inference Forward Pass Verification](#5-offline-loading--inference-forward-pass-verification)
6. [Resource Safety & Memory Telemetry Analysis](#6-resource-safety--memory-telemetry-analysis)
7. [Strict Restrictions & Operational Boundaries](#7-strict-restrictions--operational-boundaries)
8. [Final Readiness Determination & Next Steps](#8-final-readiness-determination--next-steps)

---

## 1. Executive Summary & Verdict

Under explicit user authorization, the official pretrained model snapshot for **`microsoft/deberta-v3-small`** was downloaded from Hugging Face Hub, staged locally under `/home/aditya/rags/models/pretrained/deberta-v3-small/`, and verified under strict offline isolation (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `local_files_only=True`).

### Final Stage Verdict: `MODEL_STAGED_AND_VERIFIED`

| Dimension | Status | Key Observables |
| :--- | :--- | :--- |
| **Model Acquisition Status** | ✅ **ACQUIRED** | Official HF repo `microsoft/deberta-v3-small`, upstream commit `a36c739020e01763fe789b4b85e2df55d6180012`. |
| **File Integrity Status** | ✅ **VERIFIED** | 6 files staged (275.16 MB total); all match SHA-256 manifest; zero partial shards. |
| **Tokenizer Loading Status** | ✅ **VERIFIED** | `DebertaV2Tokenizer` loaded offline; vocab `128,001`; exact roundtrip decode match confirmed. |
| **Pretrained Model Loading Status** | ✅ **VERIFIED** | `DebertaV2ForSequenceClassification` loaded offline; `141,896,450` parameters (6 layers, 768 hidden, 12 heads). |
| **Inference Forward Pass** | ✅ **VERIFIED** | Single inference pass executed on CPU; latency `322.5 ms`; output logits `[0.1516, 0.2454]`. |
| **Resource Safety Status** | ✅ **VERIFIED** | Peak RSS `623.1 MB`; Available physical RAM `2,618.7 MB` remaining; zero swap degradation. |

---

## 2. Model Provenance, Lineage & Licensing

### A. Provenance Attributes
- **Repository Identifier:** `microsoft/deberta-v3-small`
- **Hugging Face Hub URL:** https://huggingface.co/microsoft/deberta-v3-small
- **Upstream Commit SHA:** `a36c739020e01763fe789b4b85e2df55d6180012`
- **Model Author:** Microsoft Corporation
- **Mirror / Third-Party Use:** **NONE.** Downloaded directly via `huggingface_hub.snapshot_download`.

### B. Architectural Lineage
DeBERTa-v3 utilizes:
1. **Disentangled Attention:** Decomposing self-attention into content-to-content, content-to-position, and position-to-content cross-terms.
2. **Enhanced Masked Language Modeling with ELECTRA-Style RTD:** Replacing traditional MLM with Replaced Token Detection using a shared generator-discriminator embedding table.

### C. Licensing & Terms of Use
- **License Type:** **MIT License**
- **Commercial / Research Use:** Fully compliant with TrustRAG research and defense verification objectives.

---

## 3. Staged Model File Inventory & Technical Specifications

Staged local directory: `/home/aditya/rags/models/pretrained/deberta-v3-small/`

| File Name | Exact File Size (Bytes) | Size (MB) | Purpose in DeBERTa Pipeline | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **`pytorch_model.bin`** | 286,059,269 | 272.81 MB | Pretrained model weights (state_dict in PyTorch pickle format) | ✅ SHA-256 Verified & Model Loaded |
| **`spm.model`** | 2,464,616 | 2.35 MB | SentencePiece unigram vocabulary model (128,000 subwords) | ✅ Native SPM & Tokenizer Verified |
| **`README.md`** | 3,585 | < 0.01 MB | Official Hugging Face model card & license documentation | ✅ Text Inspected |
| **`config.json`** | 578 | < 0.01 MB | Model architecture hyperparameters & configuration | ✅ JSON Parsed & Config Loaded |
| **`.gitattributes`** | 1,175 | < 0.01 MB | Git LFS tracking configuration from upstream repository | ✅ Text Inspected |
| **`tokenizer_config.json`** | 52 | < 0.01 MB | Tokenizer mapping rules and special token references | ✅ JSON Parsed |

**Total Snapshot Footprint:** **288,529,275 bytes (275.16 MB)** across 6 files.

---

## 4. Authoritative SHA-256 Manifest

Every staged file was hashed using cryptographic SHA-256:

```
fa057bb09b78fe6d33af5a01440be5e8c881cd8055de35ee5588ea759cf57bfc  .gitattributes
9aa2d47666370a87d20422ed68a1ee80d79d66b4447b6f9925d97d11f4605d24  README.md
b0bb1caf90a50aa67d1085130508dfbf8646ac5a11928305e280b07a36e100ae  config.json
d4b0ebcc7799a2c2dde1a39199cb0ed709f2c6b63a48b8c05133b77955f271a9  pytorch_model.bin
c679fbf93643d19aab7ee10c0b99e460bdbc02fedf34b92b05af343b4af586fd  spm.model
3f3978e0c036f2c2588cac34a6047cbb0af0b0dc1814254e291028529805496d  tokenizer_config.json
```

---

## 5. Offline Loading & Inference Forward Pass Verification

Executed via `tools/evaluation/verify_offline_deberta_loading.py` under complete network isolation (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `local_files_only=True`):

### A. Tokenizer Verification
- **Tokenizer Class:** `DebertaV2Tokenizer`
- **Vocabulary Size:** `128,001` pieces
- **Load Latency:** `202.9 ms`
- **Sample Text:** `"TrustRAG verifies evidence grounding in retrieved passages."`
- **Roundtrip Decode Match:** `True` (Exact bit-for-bit string match).

### B. Pretrained Model Verification
- **Model Class:** `DebertaV2ForSequenceClassification`
- **Total Parameters:** **141,896,450 (141.9M)**
- **Architecture:** 6 Layers, 768 Hidden Dimension, 12 Attention Heads.
- **Load Latency:** `312.3 ms`

### C. Single Inference Forward Pass
- **Input Prompt:** Question + Context + Candidate Answer (39 tokens).
- **Execution Mode:** Inference-only with `torch.no_grad()`. Zero backward pass or optimizer steps.
- **Inference Latency:** **322.5 ms** on host CPU.
- **Output Logits:** `[0.151611328125, 0.245361328125]` (Valid finite non-NaN floats).
- **Softmax Probabilities:** `[0.4765625, 0.5234375]`.

---

## 6. Resource Safety & Memory Telemetry Analysis

| Phase | Process RSS (MB) | Available Physical RAM (MB) | Swap Free (MB) |
| :--- | :--- | :--- | :--- |
| **Pre-Test Baseline** | 14.33 MB | 3,014.91 MB | 0.41 MB |
| **Post-Model Load** | 514.92 MB | 2,634.87 MB | 0.41 MB |
| **Peak During Forward Pass** | **623.10 MB** | **2,618.70 MB** | 0.41 MB |

- **RAM Headroom:** Peak memory (623.1 MB) consumed only ~20% of available RAM. Over **2.6 GB of unallocated physical RAM** remained free.
- **Swap Impact:** Zero additional bytes were paged to swap. Zero page thrashing occurred.
- **Persistent Disk Impact:** 275.16 MB staged; over 44.2 GB free space remains available.

---

## 7. Strict Restrictions & Operational Boundaries

1. **No Training Executed:** Zero full or multi-epoch training loops were started.
2. **No Backpropagation:** Zero backward passes or optimizer updates were executed on the staged weights.
3. **Repository Integrity:** Phase 10 baseline is untouched; target Phase 11 HEAD remains `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`.
4. **Dataset Preservation:** All 18 dataset files in `data/processed/sft_v2/` remain untouched and verified.

---

## 8. Final Readiness Determination & Next Steps

### Operational Status:
- The target model **`microsoft/deberta-v3-small` is officially staged and verified**.
- It is ready for downstream objective-specific training pipeline integration (Objective A, B, C).
- **Full training is NOT authorized** in this step.
- Next step: Await independent acceptance review before authorizing model training.
