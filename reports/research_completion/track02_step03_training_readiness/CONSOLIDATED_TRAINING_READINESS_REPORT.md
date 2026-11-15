# TrustRAG — Track 2, Step 3.0: Consolidated Model, Hardware and Training Readiness Assessment

**Assessment Stage:** Track 2, Step 3.0  
**Auditor:** Independent ML Infrastructure & Training-Readiness Auditor  
**Date:** November 14, 2026  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Target Branch:** `phase-11`  
**Baseline HEAD:** `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`  
**Protected Repository:** `/home/aditya/rags/TrustRag` (HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Phase 10)  

---

## Table of Contents
1. [Executive Readiness Verdict & Summary](#1-executive-readiness-verdict--summary)
2. [Hardware Inventory & Compute Constraints](#2-hardware-inventory--compute-constraints)
3. [Pretrained Model Inventory & Architecture Compatibility](#3-pretrained-model-inventory--architecture-compatibility)
4. [Training Framework Compatibility & Environment Audit](#4-training-framework-compatibility--environment-audit)
5. [Objective-Specific Dataset Readiness Verification](#5-objective-specific-dataset-readiness-verification)
6. [Objective-Specific Training Design](#6-objective-specific-training-design)
7. [Quantitative Resource & Memory Footprint Estimates](#7-quantitative-resource--memory-footprint-estimates)
8. [Training, Validation and Evaluation Protocol](#8-training-validation-and-evaluation-protocol)
9. [Final Readiness Determination & Actionable Prerequisites](#9-final-readiness-determination--actionable-prerequisites)

---

## 1. Executive Readiness Verdict & Summary

This assessment evaluated the technical and operational readiness of TrustRAG to transition from objective-specific dataset remediation (`sft_v2`) into neural model training. The audit evaluated five distinct pillars: **Host Hardware Capabilities**, **Pretrained Model Availability**, **ML Framework & Runtime Compatibility**, **Dataset Readiness**, and **Mathematical Resource Feasibility**.

### Overall Readiness Verdict: `CONDITIONALLY_READY` (Stratified by Objective)

| Objective | Dataset Status | Runtime & Code Status | Host Hardware Feasibility | Overall Readiness Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Objective A: Binary Classification** | `READY` (32,038 examples) | `PREREQUISITES_REQUIRED` | `CPU_FEASIBLE` (Linear Probe / Small Encoder) | **`CONDITIONALLY_READY`** |
| **Objective B: 3-Way NLI** | `READY` (13,477 examples) | `PREREQUISITES_REQUIRED` | `CPU_FEASIBLE` (DeBERTa-v3-small / DistilBERT) | **`CONDITIONALLY_READY`** |
| **Objective C: Span Extraction** | `READY` (15,090 examples) | `PREREQUISITES_REQUIRED` | `CPU_FEASIBLE` (Token Classification Head) | **`CONDITIONALLY_READY`** |
| **Objective D: G3 5-Outcome Classification**| `BLOCKED` (Supervision Gap) | `BLOCKED` | N/A | **`BLOCKED`** |
| **Objective E: Generative Structured SRM (HalluGuard)** | `BLOCKED` (No CoT Traces) | `PREREQUISITES_REQUIRED` | `IMPOSSIBLE` (OOM on 3.34 GB available RAM / 0 VRAM) | **`BLOCKED`** |

### Key Executive Conclusions:
1. **Dataset Integrity Verified:** All four remediated datasets produced in Step 2.2 match verified SHA-256 checksums from the Step 2.2.1 audit.
2. **Discriminative Training is Feasible:** Compact cross-encoder architectures (`microsoft/deberta-v3-small` with 44M parameters or `distilbert-base-uncased` with 66M parameters) fit comfortably within the host's 3.34 GB available RAM.
3. **Generative SRM is Blocked:** Training generative causal reasoning models (1.5B–7B parameters) is physically impossible on this CPU host due to memory constraints and absence of synthetic `<think>` reasoning traces in the dataset.
4. **Environment Prerequisite:** Essential deep learning dependencies (`torch`, `transformers`, `accelerate`) are not yet installed in the virtual environment, and Python 3.14 lacks standard pre-built PyPI wheels for PyTorch.

---

## 2. Hardware Inventory & Compute Constraints

An exhaustive hardware probe was executed via `/proc/cpuinfo`, `/proc/meminfo`, `statvfs`, and OS diagnostics:

### A. Compute Infrastructure (CPU)
- **Model:** 13th Gen Intel(R) Core(TM) i7-1355U (Raptor Lake mobile architecture).
- **Core Topology:** 10 Physical Cores (2 Performance-cores + 8 Efficient-cores), 12 Logical Execution Threads.
- **Clock Frequencies:** 1.70 GHz Base Clock, up to 5.00 GHz Max Turbo Clock (15W base TDP, 55W boost).
- **SIMD Extensions:** SSE4.2, AVX, AVX2, FMA3, Intel DL Boost (AVX-VNNI). No AVX-512.

### B. Memory Subsystem (RAM & Swap)
- **Total System RAM:** 16,029,880 kB (15.29 GB).
- **Available Physical RAM:** 3,500,648 kB (**3.34 GB headroom**).
- **Free Physical RAM:** 1,563,696 kB (1.49 GB).
- **Swap Subsystem:** 6,143,996 kB (5.86 GB total) with 91,056 kB (0.09 GB) free.
- **Critical Memory Alert:** **98.5% of swap is currently consumed.** Any workload allocating more than 2.5 GB RSS risks triggering immediate kernel page-thrashing or the Linux Out-Of-Memory (OOM) killer.

### C. Accelerator Subsystem (GPU / NPU)
- `which nvidia-smi`: Command not found (Exit code 127).
- Discrete GPU Count: **0**
- Total VRAM: **0.00 GB**
- CUDA / ROCm / MPS Runtime: **Unavailable**.
- **Assessment:** Exclusively CPU-bound host platform. All forward/backward tensor passes must execute via CPU threads.

### D. Storage Subsystem
- **Filesystem Mount:** `/home/aditya` (ext4).
- **Total Capacity:** 294.23 GB.
- **Available Space:** 46.07 GB (84.3% utilized).
- **Storage Headroom:** Ample capacity for small encoder checkpoints (~0.5 GB each) and dataset cache (~0.15 GB), but inadequate for multiple large generative checkpoints (15 GB each).

---

## 3. Pretrained Model Inventory & Architecture Compatibility

### A. Local Filesystem Census
- `~/.cache/huggingface/hub/`: Contains only dataset shards (`hotpotqa`, `ms_marco`, `natural_questions`). **Zero pretrained model weights.**
- `/home/aditya/rags/models/`: Contains only `.gitkeep` files in `checkpoints/`, `pretrained/`, and `detectors/`.
- `TrustRag-phase11/models/`: Non-existent.
- **Local Model Count:** **0 models available locally.**

### B. Offline Policy Enforcement
TrustRAG's `src/trustrag/config/engine_config.py` enforces `local_files_only: True`. Unstaged models cannot be downloaded dynamically during training or inference. All model weights must be staged explicitly prior to launch.

### C. Architecture Feasibility Matrix

| Model Architecture | Parameter Count | Weight Footprint (FP32 / FP16) | Native Context Window | License | Host CPU Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`microsoft/deberta-v3-small`** | 44M | 176 MB / 88 MB | 512 tokens | MIT | **HIGHLY FEASIBLE** (Memory < 1.0 GB) |
| **`distilbert-base-uncased`** | 66M | 268 MB / 134 MB | 512 tokens | Apache 2.0 | **HIGHLY FEASIBLE** (Fast CPU training) |
| **`microsoft/deberta-v3-base`** | 86M | 344 MB / 172 MB | 512 tokens | MIT | **FEASIBLE** (Memory ~1.8 GB) |
| **`roberta-base`** | 125M | 500 MB / 250 MB | 512 tokens | MIT | **FEASIBLE WITH BOUNDED BATCH** |
| **`Qwen/Qwen2.5-1.5B-Instruct`**| 1.54B | 3.1 GB / 1.1 GB | 32,768 tokens | Apache 2.0 | **INFEASIBLE ON HOST** (Exceeds 3.34 GB RAM) |
| **`Qwen/Qwen2.5-Coder-7B-Instruct`**| 7.61B | 15.2 GB / 5.2 GB | 128,000 tokens | Apache 2.0 | **IMPOSSIBLE ON HOST** (Immediate OOM) |

---

## 4. Training Framework Compatibility & Environment Audit

### A. Installed Package Audit (`/home/aditya/rags/.venv`)
- `tokenizers`: `0.23.3` (Installed)
- `datasets`: `5.1.0` (Installed)
- `scikit-learn`: `1.9.1` (Installed)
- `scipy`: `1.18.1` (Installed)
- `numpy`: `2.5.4` (Installed)
- `pandas`: `3.1.1` (Installed)
- `torch`: **NOT INSTALLED**
- `transformers`: **NOT INSTALLED**
- `peft`: **NOT INSTALLED**
- `trl`: **NOT INSTALLED**
- `accelerate`: **NOT INSTALLED**
- `bitsandbytes`: **NOT INSTALLED**

### B. Python 3.14 Compatibility Hazard
The active virtualenv is running **Python 3.14.9**. Standard binary wheels on PyPI for `torch` are compiled for Python $\le 3.12 / 3.13$. Installing PyTorch under Python 3.14 may require C++ source compilation or encounter ABI incompatibility.
- **Recommended Remedy:** Utilize the existing system Python (`/usr/bin/python3.10`) to create a dedicated training virtualenv (`.venv-train`) where pre-built, Intel oneDNN-accelerated PyTorch CPU wheels install cleanly.

---

## 5. Objective-Specific Dataset Readiness Verification

All remediated `sft_v2` datasets were independently validated against Step 2.2.1 checksums and schemas:

| Objective Dataset | Train Records | Val Records | Quarantined | SHA-256 Checksum Status | Label Completeness |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`sft_v2/binary`** | 26,054 | 5,984 | 52 | ✅ All 5 files MATCH | 100% Binary (0=Faithful, 1=Hallucinated) |
| **`sft_v2/nli`** | 10,815 | 2,662 | 18,613 | ✅ All 5 files MATCH | 100% 3-Way (0=Entail, 1=Neutral, 2=Contradict) |
| **`sft_v2/spans`** | 12,072 | 3,018 | 0 | ✅ All 5 files MATCH | 100% Verified Spans (12,756 ground-truth spans) |
| **`sft_v2/g3_readiness`**| 0 | 0 | 32,090 | ✅ All 3 files MATCH | 0% (Documented supervision gap; 0 fabricated) |

### Sequence Word Count Census:
- **Binary Classification:** Median 128 words, 95th percentile 1,463 words, Max 3,783 words.
- **3-Way NLI:** Median 451 words, 95th percentile 1,102 words, Max 2,060 words.
- **Fine-Grained Spans:** Median 810 words, 95th percentile 2,015 words, Max 3,783 words.

---

## 6. Objective-Specific Training Design

### A. Objective A: Binary Classification
- **Architecture:** `microsoft/deberta-v3-small` Cross-Encoder (`AutoModelForSequenceClassification`).
- **Input:** `[CLS] Question: {q} [SEP] Context: {c} [SEP] Response: {r} [SEP]`.
- **Loss:** `torch.nn.BCEWithLogitsLoss()` (`pos_weight = 1.0`).
- **Optimizer:** AdamW (`lr=2e-5`, `weight_decay=0.01`).
- **Batch Size:** Physical 8, gradient accumulation 2 (Effective 16).

### B. Objective B: 3-Way NLI
- **Architecture:** `microsoft/deberta-v3-small` NLI Cross-Encoder.
- **Input:** `[CLS] Premise: {evidence} [SEP] Hypothesis: {candidate_sentence} [SEP]`.
- **Loss:** Class-weighted `torch.nn.CrossEntropyLoss()` to penalize majority bias.
- **Optimizer:** AdamW (`lr=3e-5`, `weight_decay=0.01`).
- **Batch Size:** Physical 8, gradient accumulation 2 (Effective 16).

### C. Objective C: Fine-Grained Span Extraction
- **Architecture:** `microsoft/deberta-v3-base` Token Classifier (`AutoModelForTokenClassification`).
- **Input:** `[CLS] Context [SEP] Candidate Response [SEP]`.
- **Tagging:** BIO scheme (`O`, `B-HALL`, `I-HALL`).
- **Loss:** Masked `torch.nn.CrossEntropyLoss(ignore_index=-100)` applied exclusively over candidate response tokens.
- **Sliding Window:** Stride = 128 tokens for long candidate responses.

---

## 7. Quantitative Resource & Memory Footprint Estimates

### A. Mathematical Formulation
$$M_{\text{total}} = M_{\text{params}} + M_{\text{grads}} + M_{\text{opt}} + M_{\text{act}} + M_{\text{overhead}}$$
For FP32 AdamW training: $M_{\text{state}} = 16P\text{ bytes}$.

### B. Memory Footprint Matrix (Host RAM Available: 3.34 GB)

| Model & Approach | Parameters | State Memory | Activation Memory ($B=8, S=512$) | Total Training Memory | Feasibility Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`deberta-v3-small` (Full FT)** | 44M | 704 MB | $\approx 220\text{ MB}$ | **$\approx 0.95\text{ GB}$** | ✅ **FEASIBLE (Safe)** |
| **`distilbert-base` (Full FT)** | 66M | 1,056 MB | $\approx 280\text{ MB}$ | **$\approx 1.35\text{ GB}$** | ✅ **FEASIBLE (Safe)** |
| **`deberta-v3-base` (Full FT)** | 86M | 1,376 MB | $\approx 450\text{ MB}$ | **$\approx 1.85\text{ GB}$** | ⚠️ **FEASIBLE (Bounded Batch)** |
| **`roberta-base` (Full FT)** | 125M | 2,000 MB | $\approx 550\text{ MB}$ | **$\approx 2.55\text{ GB}$** | ⚠️ **MARGINAL (Swap risk)** |
| **`roberta-base` (Linear Probe)** | 0.05M active | 501 MB | $\approx 150\text{ MB}$ | **$\approx 0.65\text{ GB}$** | ✅ **FEASIBLE (Fast)** |
| **`Qwen2.5-1.5B` (LoRA $r=16$)** | 1.54B | 3.5 GB | $\approx 1.8\text{ GB}$ | **$\approx 5.3\text{ GB}$** | ❌ **INFEASIBLE (OOM)** |
| **`Qwen2.5-Coder-7B` (QLoRA 4-bit)**| 7.61B | 6.4 GB | $\approx 4.5\text{ GB}$ | **$\approx 10.9\text{ GB}$** | ❌ **IMPOSSIBLE (Host Crash)** |

### C. Epoch Duration Estimates (Host CPU vs Cloud Reference GPU)

| Objective & Dataset Size | Host CPU (Intel i7-1355U, 6 threads) | NVIDIA T4 (Cloud Reference) | NVIDIA A10G (Cloud Reference) |
| :--- | :--- | :--- | :--- |
| **Binary Classification (26,054 examples)** | **$\approx 7.7\text{ hours / epoch}$** | $\approx 20.3\text{ minutes / epoch}$ | $\approx 7.6\text{ minutes / epoch}$ |
| **3-Way NLI (10,815 examples)** | **$\approx 5.3\text{ hours / epoch}$** | $\approx 19.5\text{ minutes / epoch}$ | $\approx 6.8\text{ minutes / epoch}$ |
| **Span Extraction (12,072 examples)** | **$\approx 9.5\text{ hours / epoch}$** | $\approx 34.2\text{ minutes / epoch}$ | $\approx 11.5\text{ minutes / epoch}$ |

---

## 8. Training, Validation and Evaluation Protocol

1. **Validation Protocol:** Evaluate every 0.5 epochs against canonical `validation.jsonl`.
2. **Primary Success Metrics:**
   - Objective A: Validation Macro F1 $\ge 0.78$
   - Objective B: Validation Balanced F1 $\ge 0.75$, Contradiction F1 $\ge 0.70$
   - Objective C: Character-level Span F1 $\ge 0.65$
3. **Stopping Criteria:** Early stopping with patience = 3 evaluation steps (1.5 epochs) without $\Delta \ge 0.005$ improvement.
4. **Thermal & Memory Safeguards:**
   - Thread limiting: `torch.set_num_threads(6)`.
   - Dynamic batch halving if resident memory exceeds 2.8 GB.

---

## 9. Final Readiness Determination & Actionable Prerequisites

### Comprehensive Readiness Determination:

1. **Objective A (Binary Classification): `CONDITIONALLY_READY`**
   - *Prerequisites:* Install PyTorch + Transformers in Python $\le 3.12$ environment; stage `deberta-v3-small` weights locally.
2. **Objective B (3-Way NLI Classification): `CONDITIONALLY_READY`**
   - *Prerequisites:* Install PyTorch + Transformers; stage `deberta-v3-small` weights locally.
3. **Objective C (Fine-Grained Span Detection): `CONDITIONALLY_READY`**
   - *Prerequisites:* Install PyTorch + Transformers; implement sliding window token collator; stage `deberta-v3-base` weights locally.
4. **Objective D (G3 5-Outcome Classification): `BLOCKED`**
   - *Prerequisites:* Resolve dataset supervision gap via teacher LLM distillation.
5. **Objective E (Generative Structured SRM): `BLOCKED`**
   - *Prerequisites:* Acquire GPU infrastructure ($\ge 16\text{ GB VRAM}$); synthesize `<think>` reasoning traces.

### Concrete Action Items for Next Step (Track 2, Step 3.1):
1. Create a dedicated Python 3.10 training virtualenv (`/home/aditya/rags/.venv-train`).
2. Install CPU-optimized `torch`, `transformers`, `accelerate`, and `scikit-learn`.
3. Stage base model checkpoints into `/home/aditya/rags/models/pretrained/`.
4. Implement the discriminative training script in `tools/training/train_discriminative_verifier.py`.
