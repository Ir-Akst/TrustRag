# TrustRAG — Track 2, Step 1: Independent Neural Training Readiness Audit
# 05 — Model Selection, Hardware Feasibility & Compute Profile

**Audit Objective:** Measure and evaluate the host hardware, memory capacity, compute resources, base model candidates, and determine the physical feasibility of training small reasoning models.

---

## 1. Measured Host Hardware & Environment Specifications

The following empirical measurements were captured directly from the execution environment:

| Hardware / Resource Attribute | Measured Value | Audit Finding & Constraint |
| :--- | :--- | :--- |
| **CPU Architecture** | x86_64, 10 Physical Cores, 12 Threads | 13th Gen Intel(R) Core(TM) i7-1355U (Base 400 MHz, Max 5,000 MHz) |
| **Dedicated GPU Model** | **NONE** | `nvidia-smi` command not found; no dedicated GPU detected |
| **GPU VRAM Capacity** | **0 GB** | CUDA device count = 0; no GPU memory available |
| **System Physical RAM** | 15.0 GiB Total | **13.0 GiB Used**, **294 MiB Free**, **2.2 GiB Available** |
| **System Swap Memory** | 5.9 GiB Total | **5.9 GiB Used (99.9% Exhausted)**, 3.9 MiB Free |
| **Root Filesystem Storage** | 7.7 GB Available | `df -h /home/aditya` reports 7.7G available on root volume |
| **PyTorch / CUDA Runtime** | **NOT INSTALLED** | `import torch` raises `ModuleNotFoundError` |
| **Transformers / Accelerate** | **NOT INSTALLED** | `import transformers` raises `ModuleNotFoundError` |

---

## 2. Base Model Architectures & Parameter Scales

Based on Paper A (HalluGuard), Paper B (TrustRAG), and existing codebase configurations:

| Model Architecture | Parameter Count | Weight Footprint (fp16) | Weight Footprint (4-bit QLoRA) | Checkpoint Staged Locally? | Feasibility on Current Host |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **HalluGuard-4B SRM (Paper Mandate)** | 4.0 Billion | ~8.0 GB | ~3.5 GB | **NO (Absent)** | **IMPOSSIBLE (OOM)** |
| **Llama-3.2-3B / Qwen-2.5-3B** | 3.0 Billion | ~6.0 GB | ~2.5 GB | **NO (Absent)** | **IMPOSSIBLE (OOM)** |
| **Qwen-2.5-Coder-1.5B** | 1.5 Billion | ~3.0 GB | ~1.2 GB | **NO (Absent)** | **IMPOSSIBLE (OOM)** |
| **DeBERTa-v3-large (NLI Cross-Encoder)** | 435 Million | ~1.7 GB | ~0.8 GB | **NO (Absent)** | **EXTREMELY CONSTRAINED (CPU ONLY)** |
| **DeBERTa-v3-base (NLI Cross-Encoder)** | 86 Million | ~350 MB | ~150 MB | **NO (Absent)** | **POTENTIALLY FEASIBLE ON CPU** |

---

## 3. Training Feasibility & Memory Estimations for 4B SRM

To train the paper-mandated 4B parameter model, the minimum physical resource requirements are:

### 3.1 Full Parameter Fine-Tuning (fp16 / bf16)
- Model Weights: $4 \times 10^9 \times 2 \text{ bytes} \approx 8.0\text{ GB}$
- AdamW Optimizer States: $4 \times 10^9 \times 8 \text{ bytes} \approx 32.0\text{ GB}$
- Gradients: $4 \times 10^9 \times 2 \text{ bytes} \approx 8.0\text{ GB}$
- Activations (Context length 2048, batch size 2): $\approx 4.0\text{–}6.0\text{ GB}$
- **Total Minimum GPU VRAM Required:** **~52 to 60 GB** (e.g. 1x NVIDIA A100 80GB or 2x A100 40GB).
- **Feasibility on Current Host:** **IMPOSSIBLE**.

### 3.2 Parameter-Efficient LoRA (fp16 backbone, rank 16)
- Frozen Model Weights: ~8.0 GB
- Trainable Adapter Weights & Optimizer: ~0.5 GB
- Gradients & Activations: ~4.0 GB
- **Total Minimum GPU VRAM Required:** **~14 to 16 GB** (e.g. 1x NVIDIA RTX 4090 24GB or A10G 24GB).
- **Feasibility on Current Host:** **IMPOSSIBLE**.

### 3.3 4-bit Quantized LoRA (QLoRA)
- 4-bit NF4 Quantized Weights: ~2.5 to 3.0 GB
- Trainable Adapter Weights & Optimizer: ~0.5 GB
- Compute Activations (batch size 1, gradient accumulation 16): ~3.0 GB
- **Total Minimum GPU VRAM Required:** **~6.5 to 8.0 GB** (plus CUDA compute capability $\ge 7.0$).
- **Feasibility on Current Host:** **IMPOSSIBLE** (Host has no GPU and CUDA is not supported by integrated Intel graphics).

### 3.4 CPU-Only Fine-Tuning Assessment
Attempting CPU fine-tuning of a 4B or 1.5B model in PyTorch:
- The host has only **2.2 GiB of available RAM**, and swap memory is already 99.9% full (5.9 GiB allocated).
- Loading a 1.5B or 4B model into system memory will immediately cause system freezing and Linux OOM killer invocation.
- CPU training throughput on 10 mobile cores would average less than 0.1 examples/second, requiring months to process 29,090 training examples.

---

## 4. Hardware Audit Conclusion

The current local development machine is suitable for lightweight verification scripts, dataset preprocessing, unit testing, and heuristic evaluations. **It cannot support neural model training for any generative Small Reasoning Model (1.5B–4B).**

### Hardware Requirements to Unblock Track 2:
1. **GPU:** Minimum 1x NVIDIA GPU with $\ge 24\text{ GB}$ VRAM (e.g. NVIDIA A10G, A100, RTX 3090/4090) with CUDA driver installed.
2. **System RAM:** Minimum 32 GB host RAM (to stage and tokenize multi-gigabyte datasets).
3. **Storage:** Minimum 50 GB fast NVMe disk space to store base model weights, optimizer checkpoints, and tokenized caches.

