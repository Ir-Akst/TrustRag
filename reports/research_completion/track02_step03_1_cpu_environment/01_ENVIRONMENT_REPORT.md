# Track 2, Step 3.1: Isolated CPU Training Environment Report

**Audit Date:** November 14, 2026  
**Auditor:** Independent ML Infrastructure Engineer  
**Isolated Environment Path:** `/home/aditya/rags/.venv-train`  
**Base Interpreter:** `/usr/bin/python3.10` (Python 3.10.22)  

---

## 1. Environment Architecture & Rationale

Track 2 Step 3.0 determined that the primary virtual environment (`/home/aditya/rags/.venv`) operates on **Python 3.14.9**. Deep learning libraries such as PyTorch do not yet provide stable pre-built manylinux wheels for Python 3.14 on standard package indices. Compiling PyTorch from source under Python 3.14 on this 15W host CPU would introduce significant latency, compilation risk, and compiler toolchain overhead.

To preserve the primary development environment completely untouched while establishing a standard, reproducible deep learning runtime, a dedicated isolated environment was provisioned:

- **Isolated Virtualenv:** `/home/aditya/rags/.venv-train`
- **Python Binary:** `/home/aditya/rags/.venv-train/bin/python` (`3.10.22`)
- **Pip Binary:** `/home/aditya/rags/.venv-train/bin/pip` (`23.0.1` bootstrapping)
- **Primary Environment Status:** `/home/aditya/rags/.venv` remains **100% UNMODIFIED**.

---

## 2. Preflight System Health & Resource State

A preflight audit prior to environment provisioning verified host infrastructure limits:

| Metric | Measured Preflight Value | Operational Assessment |
| :--- | :--- | :--- |
| **CPU Architecture** | 13th Gen Intel(R) Core(TM) i7-1355U | 10 Cores (2 P-cores + 8 E-cores), 12 Threads. |
| **Total Physical RAM** | 16,029,880 kB (15.29 GB) | Standard desktop memory pool. |
| **Available Physical RAM** | 3,479,616 kB (3.32 GB) | Headroom for CPU training processes. |
| **Swap Total / Free** | 6,143,996 kB / 28,476 kB | **99.5% Swap consumed** (Critical host pressure). |
| **Disk Headroom** | 46.10 GB Available (294.23 GB Total) | Adequate for CPU wheels and small encoders. |
| **GPU / Accelerator** | None (`nvidia-smi` missing, 0 GB VRAM) | Pure CPU-bound environment. |

---

## 3. Git Repository Protection Verification

Preflight and post-environment git checks confirmed:
- **Target Repository (`TrustRag-phase11`):**
  - Path: `/home/aditya/rags/TrustRag-phase11`
  - Active Branch: `phase-11`
  - Current HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` (Exact expected baseline)
- **Protected Phase 10 Baseline (`TrustRag`):**
  - Path: `/home/aditya/rags/TrustRag`
  - Active Branch: `phase-10`
  - Current HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168` (Exact expected baseline)
  - Status: **UNTOUCHED. No commits, branch changes, or modified files.**

---

## 4. Isolation & Containment Principles

The `.venv-train` environment is strictly governed by the following constraints:
1. **CPU-Only Wheels:** No CUDA, cuDNN, Triton, or NVIDIA runtime wheels are installed, saving ~3.5 GB of disk space and preventing CUDA driver initialization overhead.
2. **Lean Dependency Set:** Only `torch`, `transformers`, `accelerate`, `scikit-learn`, and `sentencepiece` are targeted. Generative/LLM training stacks (`peft`, `trl`, `bitsandbytes`, `deepspeed`, `vllm`) are explicitly excluded.
3. **No Project Disruption:** The main pipeline, CLI commands (`trustrag-pipeline`), and Phase 10 baselines continue to reference their designated interpreters without interference.
