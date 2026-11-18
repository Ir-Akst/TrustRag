# Track 2, Step 3.2.1: Independent Acceptance Audit — DeBERTa Model Staging

**Audit Authority:** Independent ML Infrastructure & Model Integrity Auditor  
**Date:** November 14, 2026  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Untouched)  
**Staged Model Directory:** `/home/aditya/rags/models/pretrained/deberta-v3-small/`  
**Execution Environment:** `/home/aditya/rags/.venv-train`  

---

## 1. Final Acceptance Audit Verdict

### Overall Verdict: `MODEL_STAGING_VERIFIED`

This independent audit confirms that the official pretrained model snapshot for **`microsoft/deberta-v3-small`** is authentic, complete, cryptographically verified, and cleanly loaded under strict offline isolation (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `local_files_only=True`). 

The staged model artifact resolves the blocker identified in Step 3.1.1 and **is officially authorized and ready for a true full-architecture CPU forward/backward feasibility pilot.**

Multi-epoch training remains strictly unauthorized pending the results of the subsequent pilot.

---

## 2. Ten Mandated Audit Dimension Determinations

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

## 3. Critical Architectural & Technical Insights

1. **Checkpoint Size vs Parameter Count Resolution:**
   The apparent paradox between the 286 MB file size and ~141.9M parameters is fully resolved: **all 143,010,661 tensors in `pytorch_model.bin` are stored in FP16 (`torch.float16`)**.
   $$143,010,661\text{ parameters} \times 2\text{ bytes} = 286,021,322\text{ bytes} \approx 272.77\text{ MB}$$
   Adding 37,947 bytes of zip headers, archive metadata, and tensor name records accounts for the exact 286,059,269 bytes on disk.
2. **Classification Head Initialization:**
   Upstream `microsoft/deberta-v3-small` was pretrained as a Masked Language Model (`DebertaV2ForMaskedLM`). When loaded into `DebertaV2ForSequenceClassification`, the MLM prediction heads (`lm_predictions.*`, `mask_predictions.*`) are discarded as UNEXPECTED, and the 2-class classification projection head (`classifier.*`, `pooler.*`) is newly initialized with random Gaussian weights. The inference logits (`[0.1516, 0.2454]`) are mathematically expected and represent an untrained projection.
3. **Absence of Safetensors Upstream:**
   Official commit `a36c739020e01763fe789b4b85e2df55d6180012` contains only 6 files; no `model.safetensors` was released by Microsoft at that revision. `pytorch_model.bin` was verified to be a valid PyTorch zip archive loadable via `torch.load(..., weights_only=True)`.

---

## 4. Next Step Recommendation

The environment and model are certified ready to execute **Track 2, Step 3.3: Full-Architecture DeBERTa-v3-Small CPU Feasibility Pilot** (1 to 3 forward/backward steps with batch size 1 on actual text tokens) to establish true CPU backpropagation throughput and resident memory under autograd.
