# Track 2, Step 3.1.1: Independent Acceptance Audit — CPU Environment & Feasibility Pilot

**Audit Authority:** Independent ML Infrastructure & Dataset Integrity Auditor  
**Date:** November 14, 2026  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Untouched)  

---

## 1. Executive Determination & Final Verdict

### Final Acceptance Verdict: `CONDITIONALLY_READY`

This independent audit resolves the apparent gap in Track 2 Step 3.1 between claiming `ENVIRONMENT_READY` and confirming the absence of `microsoft/deberta-v3-small` pretrained weights:

1. **Environment Infrastructure is Ready (`ENVIRONMENT_READY`):**
   A dedicated Python 3.10 virtual environment (`/home/aditya/rags/.venv-train`) has been successfully created and populated with CPU-only wheels (`torch==2.14.1+cpu`, `transformers==5.20.2`, `accelerate==1.15.0`, `scikit-learn==1.7.2`, `sentencepiece==0.2.3`). All core PyTorch CPU tensor math, multithreaded GEMM, and autograd mechanics operate cleanly. The primary development virtualenv (`.venv`, Python 3.14.9) and the protected Phase 10 baseline remain completely untouched.

2. **The Step 3.1 Pilot Was a Synthetic Runtime Test, NOT a DeBERTa Benchmark:**
   Inspection of `tools/evaluation/run_bounded_cpu_pilot.py` (lines 76–85 and 97–100) confirms that the three-step pilot executed on a **2-layer, 128-hidden-size toy substitute model with only 475,522 parameters (0.48M)** using synthetic uniform random integers (`torch.randint(0, 1000)`). The canonical `microsoft/deberta-v3-small` model has **141,894,914 parameters (141.89M)** — making the actual target model **298.4 times larger** than the model tested in the pilot. Therefore, **the Step 3.1 pilot does NOT establish DeBERTa-v3-small training feasibility, real memory footprint, or throughput.**

3. **Pretrained Weights Remain Unstaged:**
   In compliance with TrustRAG's offline policy (`engine_config.py: local_files_only=True`), no weights were downloaded. Training cannot begin until weights are explicitly authorized and staged out-of-band.

### Objective-Specific Readiness Breakdown:

| Objective | Dataset Status (`sft_v2`) | Runtime Environment | Model Staging Status | Audit Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Objective A: Binary Classification** | `READY` (32,038 records) | `READY` (Python 3.10 CPU) | `PENDING_STAGING` | **`CONDITIONALLY_READY`** |
| **Objective B: 3-Way NLI** | `READY` (13,477 records) | `READY` (Python 3.10 CPU) | `PENDING_STAGING` | **`CONDITIONALLY_READY`** |
| **Objective C: Span Extraction** | `READY` (15,090 records) | `READY` (Python 3.10 CPU) | `PENDING_STAGING` | **`CONDITIONALLY_READY`** |
| **Objective D: G3 5-Outcome** | `BLOCKED` (Supervision Gap) | `READY` (Infrastructure ready) | `BLOCKED` (Dataset gap) | **`BLOCKED`** |
| **Objective E: Generative Structured SRM**| `BLOCKED` (No CoT Traces) | `NOT_SUPPORTED` (Requires CUDA) | `BLOCKED` (Host OOM) | **`BLOCKED`** |

---

## 2. Seven Critical Pilot Audit Questions & Explicit Findings

| Audit Question | Independent Finding | Evidentiary Basis |
| :--- | :--- | :--- |
| **1. Was actual DeBERTa-v3-small architecture loaded?** | **NO** | `tools/evaluation/run_bounded_cpu_pilot.py:76-83` instantiated a 2-layer, 128-dim toy config (0.48M params vs 141.89M canonical). |
| **2. Were pretrained DeBERTa weights loaded?** | **NO** | Lines 55–57 explicitly logged that pretrained weights are absent locally and were not fetched. |
| **3. Was a substitute model used?** | **YES** | A randomly initialized `DebertaV2ForSequenceClassification` toy substitute (475,522 parameters) was instantiated from scratch. |
| **4. Were real records from `sft_v2/binary` consumed?** | **PARTIALLY** | Records were read to extract `example_id` and `binary_label` (lines 62–70), but text fields were never passed into the model. |
| **5. Were actual DeBERTa tokenizer steps executed?** | **NO** | Lines 98–100 generated synthetic random token tensors via `torch.randint(0, 1000)`. SentencePiece tokenizer was never invoked. |
| **6. Does reported 420.6 MB RSS include target model?** | **NO** | 420.6 MB RSS represents Python 3.10 + PyTorch CPU runtime + 0.48M toy model. Canonical DeBERTa-v3 will require ~1.2–1.8 GB. |
| **7. Can reported throughput estimate DeBERTa time?** | **NO** | 78.1 tok/s on a 0.48M toy model cannot estimate a 141.9M model (298x parameter difference, differing FLOPs/token). |

---

## 3. Actionable Prerequisites Before Authorizing Training

To transition from `CONDITIONALLY_READY` to training authorization:
1. **Explicit Weight Staging:** Secure authorization to stage the snapshot for `microsoft/deberta-v3-small` into `/home/aditya/rags/models/pretrained/deberta-v3-small/`.
2. **Real DeBERTa Single-Step Pilot:** Execute a genuine single-example pilot using the actual loaded 141.9M model and real SentencePiece tokenizer to measure true resident memory (RSS) and step latency on host CPU.
3. **Wait for Independent Review:** Do not issue full multi-epoch training commands until the true-model pilot passes review.
