# Track 2, Step 3.1: Executive CPU Training Environment & Pilot Report

**Assessment Stage:** Track 2, Step 3.1  
**Auditor:** Independent ML Infrastructure Engineer  
**Date:** November 14, 2026  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Untouched)  

---

## 1. Executive Verdict & Determination

### Environment Verification Verdict: `ENVIRONMENT_READY`

The dedicated CPU-only training environment (`/home/aditya/rags/.venv-train`) has been successfully provisioned, verified, and benchmarked without modifying the primary project virtual environment or the protected Phase 10 baseline. All 10 runtime smoke tests and the 3-step bounded feasibility pilot passed with zero errors, zero NaN tensors, and strict memory safety (peak RSS: 420.6 MB vs 2,500 MB ceiling).

### Objective-Specific Training Authorization Status:

| Objective | Dataset Status (`sft_v2`) | Environment Status (`.venv-train`) | Pretrained Weights Status | Objective Training Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Objective A: Binary Classification** | `READY` (32,038 examples) | `READY` (Verified PyTorch CPU) | `PENDING_STAGING` | **`CONDITIONALLY_READY`** |
| **Objective B: 3-Way NLI** | `READY` (13,477 examples) | `READY` (Verified PyTorch CPU) | `PENDING_STAGING` | **`CONDITIONALLY_READY`** |
| **Objective C: Span Extraction** | `READY` (15,090 examples) | `READY` (Verified PyTorch CPU) | `PENDING_STAGING` | **`CONDITIONALLY_READY`** |
| **Objective D: G3 5-Outcome Verification** | `BLOCKED` (Supervision Gap) | `READY` (Infrastructure ready) | `BLOCKED` (Dataset gap) | **`BLOCKED`** |
| **Objective E: Generative Structured SRM** | `BLOCKED` (No CoT Traces) | `NOT_SUPPORTED` (Requires CUDA) | `BLOCKED` (OOM on Host) | **`BLOCKED`** |

---

## 2. Key Accomplishments & Audit Findings

1. **Dedicated Isolated Environment:**
   - Established `/home/aditya/rags/.venv-train` utilizing Python 3.10.22 (`/usr/bin/python3.10`).
   - The primary virtualenv (`/home/aditya/rags/.venv`, Python 3.14.9) remains **100% untouched**.
   - Installed a minimal, CPU-optimized stack: `torch==2.14.1+cpu`, `transformers==5.20.2`, `accelerate==1.15.0`, `scikit-learn==1.7.2`, and `sentencepiece==0.2.3`. Excluded all GPU bloat (`peft`, `trl`, `bitsandbytes`, CUDA runtime).

2. **Model Availability & Offline Compliance:**
   - Inspected local storage: Pretrained weights for `microsoft/deberta-v3-small` are **not present** locally.
   - Enforced project offline policy (`engine_config.py: local_files_only=True`): **Zero unapproved remote downloads were initiated.**

3. **Runtime Smoke Test Suite (10/10 Passed):**
   - Verified PyTorch CPU tensor math, multithreaded GEMM, forward pass, autograd backward pass, AdamW optimizer updates, state dict serialization, and deterministic seed reproducibility in 3.27 seconds.

4. **Bounded Feasibility Pilot Executed:**
   - Executed a 3-step pilot using 5 records from `sft_v2/binary/train.jsonl` (batch size 1, sequence length 64).
   - Average step latency: **13.7 ms**; Throughput: **78.1 tokens/sec**; Peak RSS: **420.6 MB**.
   - Host available RAM remained rock-solid at **3.27 GB**, and free swap was completely unharmed (zero thrashing).

5. **Dataset Integrity Re-Verified:**
   - All 18 SHA-256 checksums across `data/processed/sft_v2/` (`binary`, `nli`, `spans`, `g3_readiness`) were re-hashed and verified to match 100%.

---

## 3. Prerequisite for Full Training Authorization

Before issuing full training commands for Objectives A, B, or C:
- [ ] Explicitly stage authorized model snapshot for `microsoft/deberta-v3-small` into `/home/aditya/rags/models/pretrained/deberta-v3-small/`.
- [ ] Verify SHA-256 checksums of the staged checkpoint files (`config.json`, `model.safetensors`, `spm.model`, `tokenizer_config.json`).
- [ ] Wait for independent review approval before launching full training loops.
