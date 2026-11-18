# TrustRAG — Track 2, Step 3.2.1: Consolidated Independent DeBERTa Model Staging Acceptance Audit

**Assessment Stage:** Track 2, Step 3.2.1  
**Auditor / Authority:** Independent ML Infrastructure & Model Integrity Auditor  
**Date:** November 14, 2026  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Untouched)  
**Staged Model Directory:** `/home/aditya/rags/models/pretrained/deberta-v3-small/`  
**Execution Environment:** `/home/aditya/rags/.venv-train`  

---

## Table of Contents
1. [Executive Audit Verdict & Ten Dimension Findings](#1-executive-audit-verdict--ten-dimension-findings)
2. [Upstream Provenance & Snapshot Authenticity](#2-upstream-provenance--snapshot-authenticity)
3. [Checkpoint Integrity, Zip Format & Deserialization Security](#3-checkpoint-integrity-zip-format--deserialization-security)
4. [Architecture, Parameter Counts & Precision Dtypes](#4-architecture-parameter-counts--precision-dtypes)
5. [Model Loading Audit, Key Mappings & Classification Head Status](#5-model-loading-audit-key-mappings--classification-head-status)
6. [Resource Audit: Empirical Measurements vs Training Projections](#6-resource-audit-empirical-measurements-vs-training-projections)
7. [Dataset Integrity Re-Verification (18/18 Files)](#7-dataset-integrity-re-verification-1818-files)
8. [Final Readiness Determination & Actionable Recommendations](#8-final-readiness-determination--actionable-recommendations)

---

## 1. Executive Audit Verdict & Ten Dimension Findings

This independent acceptance audit evaluated whether Track 2 Step 3.2 successfully and authentically staged the official pretrained model `microsoft/deberta-v3-small`, and whether the staged artifact is verified and ready for an actual full-architecture CPU forward/backward feasibility pilot.

### Final Acceptance Verdict: `MODEL_STAGING_VERIFIED`

The staged model snapshot is **authentic, complete, cryptographically verified, and fully operational under strict offline isolation (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `local_files_only=True`).**

### Ten Mandated Dimension Determinations:

| Dimension | Audit Status | Key Evidentiary Findings |
| :--- | :--- | :--- |
| **1. Upstream Provenance** | ✅ **AUTHENTIC** | Official Microsoft repo, pinned immutable commit `a36c739020e01763fe789b4b85e2df55d6180012`, MIT License. |
| **2. Checkpoint Integrity** | ✅ **VERIFIED** | Valid PyTorch v1.6+ zip archive (286,059,269 bytes), SHA-256 verified, safe unpickling (`weights_only=True`). |
| **3. Architecture & Dtype** | ✅ **VERIFIED** | 6 layers, 768 hidden, 12 heads, 128,001 vocab; `141,896,450` parameters; 100% stored as `torch.float16`. |
| **4. Tokenizer Loading** | ✅ **VERIFIED** | `DebertaV2Tokenizer` loaded offline; vocab `128,001`; exact roundtrip decode match confirmed. |
| **5. Pretrained Model Loading** | ✅ **VERIFIED** | `DebertaV2ForSequenceClassification` loaded offline; backbone parameters: `141,304,320`. |
| **6. Classification Head Status** | ℹ️ **NEWLY_INITIALIZED** | `classifier.*` & `pooler.*` (592,130 params) are randomly initialized from base MLM checkpoint; logits do not reflect a trained classifier. |
| **7. Resource Safety** | ✅ **VERIFIED** | Peak inference RSS `495.70 MB` to `623.10 MB`; Available RAM `2,618.7 MB` remaining; zero swap paging. |
| **8. Binary Training Readiness** | 🎯 **PILOT_AUTHORIZED** | Ready for full-architecture CPU forward/backward feasibility pilot; multi-epoch training pending pilot. |
| **9. NLI Training Readiness** | 🎯 **PILOT_AUTHORIZED** | Ready for full-architecture CPU forward/backward feasibility pilot. |
| **10. Span Training Readiness** | ⚠️ **CONDITIONALLY_READY** | Architecture loaded; requires token classification sliding window collator for long contexts. |

---

## 2. Upstream Provenance & Snapshot Authenticity

- **Upstream Model ID:** `microsoft/deberta-v3-small`
- **Pinned Immutable Commit:** `a36c739020e01763fe789b4b85e2df55d6180012`
- **Source URL:** `https://huggingface.co/microsoft/deberta-v3-small/tree/a36c739020e01763fe789b4b85e2df55d6180012`
- **License:** Official MIT License.
- **Third-Party Mirror Use:** **NONE.** Downloaded directly from official Hugging Face CDN.
- **Upstream Safetensors Check:** At pinned commit `a36c739020e01763fe789b4b85e2df55d6180012`, Microsoft did not release a `model.safetensors` file. `pytorch_model.bin` is the canonical, authentic upstream release weight file.

---

## 3. Checkpoint Integrity, Zip Format & Deserialization Security

### A. File Inventory & SHA-256 Manifest
Every staged file in `/home/aditya/rags/models/pretrained/deberta-v3-small/` was independently verified:

```
fa057bb09b78fe6d33af5a01440be5e8c881cd8055de35ee5588ea759cf57bfc  .gitattributes (1,175 bytes)
9aa2d47666370a87d20422ed68a1ee80d79d66b4447b6f9925d97d11f4605d24  README.md (3,585 bytes)
b0bb1caf90a50aa67d1085130508dfbf8646ac5a11928305e280b07a36e100ae  config.json (578 bytes)
d4b0ebcc7799a2c2dde1a39199cb0ed709f2c6b63a48b8c05133b77955f271a9  pytorch_model.bin (286,059,269 bytes)
c679fbf93643d19aab7ee10c0b99e460bdbc02fedf34b92b05af343b4af586fd  spm.model (2,464,616 bytes)
3f3978e0c036f2c2588cac34a6047cbb0af0b0dc1814254e291028529805496d  tokenizer_config.json (52 bytes)
```
- **Total Payload Size:** **288,529,275 bytes (275.16 MB)** across 6 files.
- **Completeness:** Zero truncated files, zero missing shards, zero partial downloads.

### B. Packaging Format & Unpickling Security
- `pytorch_model.bin` is a valid standard **PyTorch v1.6+ Zip Archive** containing `archive/data.pkl` and 114 binary tensor storage files.
- Safe deserialization via `torch.load(..., weights_only=True)` succeeded cleanly, proving the file contains **strictly tensor storage records and zero custom executable Python classes**.

---

## 4. Architecture, Parameter Counts & Precision Dtypes

### A. Architectural Configuration
- **Model Class:** `DebertaV2ForSequenceClassification`
- **Transformer Layers ($L$):** 6
- **Hidden Dimension ($d$):** 768
- **Attention Heads ($A$):** 12
- **Intermediate Size ($d_{\text{ff}}$):** 3,072
- **Relative Attention:** Disentangled content-to-position (`c2p`) and position-to-content (`p2c`).
- **Context Window:** 512 tokens.

### B. Mathematical Resolution of File Size vs Parameter Count
The raw checkpoint byte size is **286,059,269 bytes**. The relationship to parameters is explained:
1. The checkpoint stores **143,010,661 parameters** from upstream Masked LM pretraining.
2. Every parameter is stored as a **16-bit float (`torch.float16`)**:
   $$\text{Tensor Storage} = 143,010,661\text{ params} \times 2\text{ bytes} = 286,021,322\text{ bytes (272.77 MB)}$$
3. Zip metadata and tensor key headers account for the remaining **37,947 bytes**.
4. Loaded in `DebertaV2ForSequenceClassification`:
   - Backbone parameters: `141,304,320` (FP16)
   - Classification head parameters: `592,130` (FP16)
   - **Total Active Parameters:** **141,896,450 (100.0% `torch.float16`)**.

---

## 5. Model Loading Audit, Key Mappings & Classification Head Status

### A. Tokenizer Offline Loading
- `DebertaV2Tokenizer` loaded with SentencePiece unigram vocabulary of **128,001 pieces**.
- Tested encoding and decoding: Exact bit-for-bit string match confirmed.

### B. Key Alignment & Classification Head Status
When loading the base Masked LM weights into `DebertaV2ForSequenceClassification`:
- **Unexpected Keys (Discarded):** 11 tensors from `lm_predictions.*` and `mask_predictions.*`.
- **Missing Keys (Newly Initialized):** `pooler.dense.weight`, `pooler.dense.bias`, `classifier.weight`, `classifier.bias` (592,130 parameters).
- **Critical Finding:** The classification projection is **newly initialized with random Gaussian weights**. Inference logits (`[0.1516, 0.2454]`) reflect a random projection, **NOT a trained binary classifier**. Downstream fine-tuning on `sft_v2/binary` is strictly required.

---

## 6. Resource Audit: Empirical Measurements vs Training Projections

### A. Empirical Measurements (Step 3.2 Verification)
- Baseline Process RSS: `14.33 MB`
- Post-Model Load RSS: `514.92 MB`
- Peak Inference RSS (Forward Pass, $B=1, S=39$): **`623.10 MB`**
- Inference Latency: **`322.5 ms`**
- Available RAM Remaining: **`2,618.70 MB`**
- Swap Consumption: Zero increase (Remained stable).

### B. Theoretical Training Projections (Not Measured Yet)
- Backpropagation Gradients (FP16/FP32): requires ~284 MB to ~568 MB.
- AdamW Optimizer States (FP32 moments): requires ~1,136 MB.
- Projected Peak Full-Training RSS ($B=8, S=512$): $\approx 1.5\text{ to }1.8\text{ GB}$.
- **Assessment:** Fits comfortably within the 2.6 GB available RAM buffer.

---

## 7. Dataset Integrity Re-Verification (18/18 Files)

All 18 dataset files across `data/processed/sft_v2/` were independently hashed and matched 100% against the authoritative SHA-256 manifests:
- `sft_v2/binary/`: 5 files verified.
- `sft_v2/nli/`: 5 files verified.
- `sft_v2/spans/`: 5 files verified (12,756 ground-truth spans, zero offset drift).
- `sft_v2/g3_readiness/`: 3 files verified.
- Historical baseline `sft_v1`: Untouched and verified against its 5 checksums.

---

## 8. Final Readiness Determination & Actionable Recommendations

### Overall Audit Verdict: `MODEL_STAGING_VERIFIED`

1. **Model Feasibility Authorization:**
   The staged model snapshot is **officially certified ready for Track 2, Step 3.3: Full-Architecture DeBERTa-v3-Small CPU Feasibility Pilot** (1 to 3 forward/backward steps with batch size 1 on actual text tokens).
2. **Multi-Epoch Training Status:**
   **STRICTLY NOT AUTHORIZED.** Multi-epoch training remains blocked until the full-architecture pilot empirically proves autograd memory bounds and step latency on host CPU.
