# Track 2, Step 3.1: Dependency Compatibility & Selection Protocol

**Audit Date:** November 14, 2026  
**Auditor:** Independent ML Infrastructure Engineer  
**Isolated Environment Path:** `/home/aditya/rags/.venv-train`  

---

## 1. Package Specification & Version Pinning

To support CPU-only training for objective-specific encoder models without pulling GPU runtimes or bloat, the package dependency set is explicitly curated:

| Targeted Dependency | Selected Package / Index | CPU Rationale & Compatibility |
| :--- | :--- | :--- |
| **`torch` (PyTorch)** | `torch==2.14.1+cpu` (`https://download.pytorch.org/whl/cpu`) | Intel oneDNN and AVX2-VNNI acceleration without 4+ GB of CUDA / cuDNN libraries. |
| **`transformers`** | `transformers==5.20.2` (PyPI) | Hugging Face model classes (`AutoModelForSequenceClassification`, `AutoModelForTokenClassification`). |
| **`accelerate`** | `accelerate==1.15.0` (PyPI) | Unified CPU device management, gradient accumulation, and evaluation looping. |
| **`scikit-learn`** | `scikit-learn==1.7.2` (PyPI) | Classification reports, macro F1, confusion matrices, and ROC/PR curve computation. |
| **`sentencepiece`** | `sentencepiece==0.2.3` (PyPI) | Mandatory native tokenizer backend required for DeBERTa-v3 (`spm.model`). |
| **`tokenizers`** | `tokenizers>=0.21.0` (PyPI) | Rust-backed fast tokenizer with character-to-token offset mapping for span extraction. |

---

## 2. Explicitly Excluded Packages & Justifications

The following packages are deliberately omitted from `.venv-train`:

| Excluded Package | Category | Exclusion Justification |
| :--- | :--- | :--- |
| **`peft`** | Parameter-Efficient Tuning | LoRA is designed for large causal LMs; small encoders (44M–86M params) undergo full fine-tuning or linear probes directly. |
| **`trl`** | RL / Preference Tuning | SFTTrainer and DPOTrainer are generative alignment utilities; discriminative cross-encoders use standard PyTorch loss loops. |
| **`bitsandbytes`** | Quantization Kernels | 4-bit and 8-bit NF4 quantization requires CUDA hardware; unsupported on host CPU. |
| **`deepspeed`** | Distributed Training | Host is a single-socket mobile CPU; distributed ZeRO partitioning is inapplicable. |
| **`vllm` / `sglang`** | Serving Engines | Causal LLM generation engines; not applicable to encoder classification. |

---

## 3. Dependency Footprint on Disk

- Standard CUDA PyTorch installation: $\approx 5.8\text{ GB}$ (torch, cuda runtime, cublas, cudnn).
- Lean CPU-only PyTorch installation: $\approx 0.65\text{ GB}$ total package footprint.
- **Disk Savings:** $> 5.0\text{ GB}$ preserved on the host's 46 GB available storage.
