# Track 2, Step 3.0: Framework Compatibility & Software Environment Audit

**Audit Date:** November 14, 2026  
**Auditor:** ML Infrastructure Auditor  
**Python Runtime:** `/home/aditya/rags/.venv/bin/python`  
**Python Version:** `3.14.9`  

---

## 1. Deep Learning Framework Census

An audit of the active virtual environment (`/home/aditya/rags/.venv`) identified the following package statuses:

| Package Name | Installed Version | Required for Neural Training | Status | Audit Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **`torch` (PyTorch)** | **None** (Not installed) | **MANDATORY** | ❌ **CRITICAL BLOCKER** | Core tensor engine missing. |
| **`transformers`** | **None** (Not installed) | **MANDATORY** | ❌ **CRITICAL BLOCKER** | Hugging Face model architectures missing. |
| **`peft`** | **None** (Not installed) | Optional (Required for LoRA) | ⚠️ **MISSING** | Parameter-efficient fine-tuning unavailable. |
| **`trl`** | **None** (Not installed) | Optional (Required for SFT/ORPO) | ⚠️ **MISSING** | SFTTrainer & DPOTrainer unavailable. |
| **`accelerate`** | **None** (Not installed) | **MANDATORY** | ❌ **CRITICAL BLOCKER** | Device management and mixed precision missing. |
| **`bitsandbytes`** | **None** (Not installed) | Optional (4-bit/8-bit QLoRA) | ⚠️ **MISSING** | Quantization kernels unavailable (CUDA-only). |
| **`deepspeed`** | **None** (Not installed) | Optional (Distributed) | ℹ️ **NOT APPLICABLE** | Host has single node, no GPU. |
| **`tokenizers`** | `0.23.3` | **MANDATORY** | ✅ **INSTALLED** | Fast Rust tokenizer backend present. |
| **`datasets`** | `5.1.0` | **MANDATORY** | ✅ **INSTALLED** | Hugging Face dataset processing present. |
| **`scikit-learn`** | `1.9.1` | **MANDATORY** | ✅ **INSTALLED** | Metrics, classification reports, PR-curves. |
| **`scipy`** | `1.18.1` | Auxiliary | ✅ **INSTALLED** | Statistical testing & calibration utilities. |
| **`numpy`** | `2.5.4` | **MANDATORY** | ✅ **INSTALLED** | Numerical array manipulation present. |
| **`pandas`** | `3.1.1` | Auxiliary | ✅ **INSTALLED** | Tabular processing present. |
| **`safetensors`** | **None** (Not installed) | Strongly Recommended | ⚠️ **MISSING** | Zero-copy weight serialization format. |

---

## 2. Python 3.14 Runtime & Wheel Availability Hazard

The active Python interpreter is **Python 3.14.9**. This introduces a significant infrastructure risk:

1. **Pre-built C-Extension Wheel Lag:**
   - Deep learning frameworks (PyTorch, TorchVision, Triton, FlashAttention) distribute binary manylinux wheels compiled against standard stable CPython ABIs (primarily Python 3.10, 3.11, and 3.12).
   - PyPI does not currently host standard release wheels of `torch` for `cp314-cp314-manylinux`.
   - Running `pip install torch` within Python 3.14 will fail if wheels are unavailable or trigger an unoptimized source compilation requiring C++17 compilers, CMake, and extended compilation time.

2. **System Alternative:**
   - The host system contains `/usr/bin/python3.10` natively on the filesystem.
   - Establishing a parallel virtual environment using Python 3.10 or 3.11 will guarantee access to pre-built, optimized, CPU-accelerated (Intel oneDNN / MKL) wheels directly from PyPI or PyTorch's official repository.

---

## 3. Dependency Declaration in Repository

In `TrustRag-phase11/pyproject.toml`, the project defines dependency groups:

```toml
[dependency-groups]
core = [
    "numpy", "pandas", "scipy", "scikit-learn", "pydantic", ...
]
ml = [
    "torch",
    "transformers",
    "datasets>=2.15,<3",
    "sentence-transformers",
    "accelerate",
    "tokenizers",
    "scikit-learn",
    "xgboost",
    "joblib",
    "faiss-cpu",
]
```

### Discrepancy Findings:
- The virtual environment was provisioned with the `core` group and development packages, but the `ml` group was **never installed**.
- Furthermore, `peft`, `trl`, and `bitsandbytes` are not declared in `pyproject.toml`.
- The version pin `datasets>=2.15,<3` conflicts with the currently installed `datasets==5.1.0`.

---

## 4. Minimum Compatible Stack Specification

For CPU-based neural training on this host, the verified target configuration is:

```ini
python >= 3.10, <= 3.12
torch == 2.5.1+cpu  # Or standard CPU wheel with Intel oneDNN support
transformers >= 4.46.0
accelerate >= 1.0.0
tokenizers >= 0.20.0
datasets >= 3.0.0
scikit-learn >= 1.5.0
safetensors >= 0.4.5
```
