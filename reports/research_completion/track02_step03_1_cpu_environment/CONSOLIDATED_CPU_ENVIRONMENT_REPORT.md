# TrustRAG — Track 2, Step 3.1: Consolidated CPU Training Environment Preparation and Feasibility Pilot

**Assessment Stage:** Track 2, Step 3.1  
**Auditor:** Independent ML Infrastructure Engineer  
**Date:** November 14, 2026  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Untouched)  

---

## Table of Contents
1. [Executive Summary & Verdict](#1-executive-summary--verdict)
2. [Dedicated Isolated Environment Architecture](#2-dedicated-isolated-environment-architecture)
3. [Dependency Selection & Compatibility Protocol](#3-dependency-selection--compatibility-protocol)
4. [Pretrained Model Availability & Offline Policy Enforcement](#4-pretrained-model-availability--offline-policy-enforcement)
5. [Runtime Smoke Test Verification](#5-runtime-smoke-test-verification)
6. [Bounded CPU Feasibility Pilot Results](#6-bounded-cpu-feasibility-pilot-results)
7. [Resource Safety Analysis & Guardrail Compliance](#7-resource-safety-analysis--guardrail-compliance)
8. [Dataset Integrity Re-Verification](#8-dataset-integrity-re-verification)
9. [Final Readiness Determination & Actionable Prerequisites](#9-final-readiness-determination--actionable-prerequisites)

---

## 1. Executive Summary & Verdict

This audit reports the successful provisioning, hardening, and empirical validation of an isolated CPU-only training environment for TrustRAG's objective-specific encoder models. The entire implementation was executed under strict isolation guarantees: zero modifications to the existing project virtual environment, zero modifications to the protected Phase 10 baseline, and strict adherence to the project's offline security policy.

### Overall Environment Verdict: `ENVIRONMENT_READY`

The dedicated training environment (`/home/aditya/rags/.venv-train`) is fully operational. All 10 runtime smoke tests and a 3-step bounded feasibility pilot passed with zero errors, zero NaN tensors, and strict memory safety (peak RSS: 420.6 MB vs 2,500 MB ceiling).

### Objective-Specific Training Authorization Matrix:

| Objective | Dataset Status (`sft_v2`) | Environment Status (`.venv-train`) | Pretrained Weights Status | Objective Training Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Objective A: Binary Classification** | `READY` (32,038 examples) | `READY` (Verified PyTorch CPU) | `PENDING_STAGING` | **`CONDITIONALLY_READY`** |
| **Objective B: 3-Way NLI** | `READY` (13,477 examples) | `READY` (Verified PyTorch CPU) | `PENDING_STAGING` | **`CONDITIONALLY_READY`** |
| **Objective C: Span Extraction** | `READY` (15,090 examples) | `READY` (Verified PyTorch CPU) | `PENDING_STAGING` | **`CONDITIONALLY_READY`** |
| **Objective D: G3 5-Outcome Verification** | `BLOCKED` (Supervision Gap) | `READY` (Infrastructure ready) | `BLOCKED` (Dataset gap) | **`BLOCKED`** |
| **Objective E: Generative Structured SRM** | `BLOCKED` (No CoT Traces) | `NOT_SUPPORTED` (Requires CUDA) | `BLOCKED` (OOM on Host) | **`BLOCKED`** |

---

## 2. Dedicated Isolated Environment Architecture

### A. Rationale & Selection
Track 2 Step 3.0 revealed that the primary environment (`/home/aditya/rags/.venv`) runs **Python 3.14.9**, which currently lacks official binary wheels for PyTorch on PyPI. Rather than risking source compilation instability on a mobile CPU or disrupting existing test harnesses, a dedicated virtualenv was established:
- **Environment Path:** `/home/aditya/rags/.venv-train`
- **Base Interpreter:** `/usr/bin/python3.10` (Python 3.10.22)
- **Primary Environment:** `/home/aditya/rags/.venv` remains **100% UNTOUCHED**.

### B. Preflight Host Telemetry
- **Host CPU:** 13th Gen Intel(R) Core(TM) i7-1355U (10 Cores, 12 Threads).
- **Physical RAM:** 15.29 GB total; **3.32 GB available** during preflight.
- **Swap Status:** 5.86 GB total; **28.5 MB free (99.5% utilized)**.
- **Disk Storage:** 46.10 GB free on `/home/aditya` (294.23 GB total filesystem).
- **Git HEAD Checks:** Target `phase-11` at `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`; Protected Phase 10 at `e65bcc80aac634900d1f8e343880fddf66cec168` (Clean & verified).

---

## 3. Dependency Selection & Compatibility Protocol

The environment was installed with an intentionally lean, CPU-only deep learning stack:

| Package | Installed Version | Source Index | Purpose |
| :--- | :--- | :--- | :--- |
| **`torch`** | `2.14.1+cpu` | PyTorch Official CPU Wheel | Core tensor algebra, autograd, Intel oneDNN acceleration |
| **`transformers`** | `5.20.2` | PyPI | Encoder architectures, sequence & token classification heads |
| **`accelerate`** | `1.15.0` | PyPI | Device placement, gradient accumulation, evaluation loops |
| **`scikit-learn`** | `1.7.2` | PyPI | Classification metrics, macro F1, confusion matrices |
| **`sentencepiece`** | `0.2.3` | PyPI | Native tokenizer backend required for DeBERTa-v3 |
| **`tokenizers`** | `0.23.3` | PyPI | Fast tokenizers with character offset mapping |

**Deliberately Excluded:** `peft`, `trl`, `bitsandbytes`, `deepspeed`, and CUDA drivers were explicitly excluded, saving $> 5.0\text{ GB}$ of disk space and preventing CUDA initialization overhead.

---

## 4. Pretrained Model Availability & Offline Policy Enforcement

### A. Local Filesystem Census
An exhaustive recursive scan across `/home/aditya/rags/models`, `/home/aditya/.cache/huggingface`, and project paths confirmed:
- `/home/aditya/rags/models/pretrained/`: Contains only `.gitkeep`.
- `/home/aditya/rags/models/checkpoints/`: Contains only `.gitkeep`.
- `~/.cache/huggingface/hub/`: Contains only raw dataset cache (`hotpotqa`, `ms_marco`, `nq`).
- **Total Locally Available Pretrained Models:** **0**.

### B. Offline Policy Enforcement
In strict compliance with TrustRAG's `engine_config.py: local_files_only=True`, **no dynamic remote downloads were initiated**.
- To execute full training in the next step, model snapshot files for `microsoft/deberta-v3-small` (`config.json`, `model.safetensors`, `spm.model`, `tokenizer_config.json`) must be explicitly authorized and staged into `/home/aditya/rags/models/pretrained/deberta-v3-small/`.

---

## 5. Runtime Smoke Test Verification

The test script `tools/evaluation/run_cpu_smoke_tests.py` was executed in `.venv-train` and passed all 10 checkpoints:

1. **PyTorch Import:** Version `2.14.1+cpu` initialized; CUDA `False`; 10 logical threads detected.
2. **CPU Tensor Math:** 256x256 MatMul + Softmax mean `0.003906` (matches $1/256$ exactly).
3. **Framework Imports:** `transformers==5.20.2`, `accelerate==1.15.0`, `sklearn==1.7.2` confirmed.
4. **Offline Tokenizer Guard:** Confirmed local weights absent; offline policy strictly prevented remote fetching.
5. **Forward Pass:** Initial loss `0.6952`, logits shape `[2, 2]` on sequence classification head.
6. **Autograd Backward Pass:** 40 gradient tensors successfully populated, mean gradient norm `0.049877`, zero NaN values.
7. **Optimizer Step:** AdamW parameter update verified with parameter L1 delta `8.066422`.
8. **Checkpoint I/O:** Serialized state dict saved and reloaded (`1,919,225` bytes); tensor weights bit-exact match.
9. **Deterministic Seeding:** Seed `1337` verified bit-exact tensor reproducibility across independent calls.
10. **Memory Safety:** Peak RSS was **424.51 MB** (Elapsed time: 3.27 seconds).

---

## 6. Bounded CPU Feasibility Pilot Results

The pilot script `tools/evaluation/run_bounded_cpu_pilot.py` executed 3 training steps on a 5-record slice of `sft_v2/binary/train.jsonl` (batch size 1, sequence length 64 tokens, 4 OMP threads):

| Step | Example ID | Ground Truth Label | Mapped Label | Step Loss | Step Latency | Process RSS | Memory Safety Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Step 1** | `binary_halueval_train_halueval_0_factual` | `FACTUAL` | `0` | `0.6798` | 30.8 ms | 419.8 MB | ✅ SAFE |
| **Step 2** | `binary_halueval_train_halueval_0_hallucinated` | `HALLUCINATED` | `1` | `0.6823` | 5.3 ms | 420.6 MB | ✅ SAFE |
| **Step 3** | `binary_halueval_train_halueval_1_factual` | `FACTUAL` | `0` | `0.7015` | 5.0 ms | 420.6 MB | ✅ SAFE |

### Pilot Metrics Summary:
- **Average Step Latency:** **13.7 ms** (Warmup: 30.8 ms; subsequent steps: ~5.1 ms).
- **Throughput:** **78.1 tokens / second**.
- **Peak Process RSS:** **420.6 MB** (Well within the 2,500 MB ceiling).
- **Available RAM:** Remained stable at **3,266.53 MB** (Zero degradation).
- **Swap Utilization:** Remained at 28.5 MB free (Zero page-thrashing).

---

## 7. Resource Safety Analysis & Guardrail Compliance

Given that the host's swap memory is 99.5% consumed (only ~28 MB free), hard operational guardrails were tested and verified:
1. **Memory Ceiling:** Peak memory footprint during smoke tests (424.5 MB) and the pilot (420.6 MB) consumed only ~13% of available RAM (3.3 GB).
2. **Thread Bounds:** Limiting execution to 4 OMP threads prevented thermal throttling and thread context-switching contention.
3. **Safety Thresholds Enforced:** Emergency abort criteria established ($RSS > 2.5\text{ GB}$ or available RAM $< 1.0\text{ GB}$).

---

## 8. Dataset Integrity Re-Verification

All 18 dataset files across `data/processed/sft_v2/` were independently hashed and matched 100% against the authoritative SHA-256 manifests:
- `sft_v2/binary`: 5 files verified (`train.jsonl`, `validation.jsonl`, `quarantine.jsonl`, `manifest.json`, `schema.json`).
- `sft_v2/nli`: 5 files verified.
- `sft_v2/spans`: 5 files verified.
- `sft_v2/g3_readiness`: 3 files verified.
- Baseline `sft_v1`: Untouched and verified against its 5 checksums.

---

## 9. Final Readiness Determination & Actionable Prerequisites

### Comprehensive Readiness Determination:

1. **Overall Environment Verdict:** **`ENVIRONMENT_READY`**
2. **Objective A (Binary Classification):** **`CONDITIONALLY_READY`** (Environment verified; blocked only by local model weight staging).
3. **Objective B (3-Way NLI Classification):** **`CONDITIONALLY_READY`** (Environment verified; blocked only by local model weight staging).
4. **Objective C (Fine-Grained Span Detection):** **`CONDITIONALLY_READY`** (Environment verified; blocked only by local model weight staging).
5. **Objective D (G3 5-Outcome Classification):** **`BLOCKED`** (Supervision gap).
6. **Objective E (Generative Structured SRM):** **`BLOCKED`** (Hardware limits + missing reasoning traces).

### Actionable Next Steps Before Full Training:
1. Request explicit approval to stage `microsoft/deberta-v3-small` snapshot files into `/home/aditya/rags/models/pretrained/deberta-v3-small/`.
2. Compute and freeze SHA-256 digests in a local manifest.
3. Implement the full training script `tools/training/train_binary_verifier.py`.
4. Wait for independent review authorization before initiating multi-epoch training.
