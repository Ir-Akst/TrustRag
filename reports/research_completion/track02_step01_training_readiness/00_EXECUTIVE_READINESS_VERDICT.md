# TrustRAG — Track 2, Step 1: Independent Neural Training Readiness Audit
# 00 — Executive Readiness Verdict & Comprehensive Infrastructure Audit

**Audit Date:** November 14, 2026  
**Auditor Role:** Senior ML Infrastructure Engineer & Independent ML Research Evaluator  
**Audit Target:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Baseline:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Untouched)  
**Deliverable Directory:** [`reports/research_completion/track02_step01_training_readiness/`](file:///home/aditya/rags/TrustRag-phase11/reports/research_completion/track02_step01_training_readiness/)

---

## 1. Definitive Training Readiness Verdict

```
================================================================================
FINAL READINESS VERDICT: BLOCKED
================================================================================
```

TrustRAG is **NOT READY** to begin neural model training. While the underlying research benchmark datasets (RAGTruth and HaluEval) possess clean, well-partitioned training splits, neural training is fundamentally blocked by hard infrastructure, dependency, model artifact, and code implementation deficits.

---

## 2. Readiness Dimension Scorecard

| Readiness Dimension | Evaluation Status | Primary Evidence & Root Cause | Blocker Severity |
| :--- | :---: | :--- | :---: |
| **1. Hardware & Compute** | **BLOCKED** | Zero dedicated GPUs available (`nvidia-smi` not found). Host has only an Intel Core i7-1355U CPU with **2.2 GiB** available RAM; swap is 99.9% full (5.9 GiB used). | **CRITICAL BLOCKER** |
| **2. Software Dependencies** | **BLOCKED** | `torch`, `transformers`, `peft`, `trl`, `accelerate`, and `bitsandbytes` are **NOT INSTALLED** in the active virtual environment (`/home/aditya/rags/.venv`). | **CRITICAL BLOCKER** |
| **3. Model Weights & Artifacts** | **BLOCKED** | Zero pretrained model checkpoints exist locally (`models/` contains only empty `.gitkeep` files). `SRMConfig.local_files_only = True` disallows runtime downloading. | **CRITICAL BLOCKER** |
| **4. Training Implementation** | **BLOCKED** | Zero training scripts exist in the repository (`tools/`, `scripts/`, `src/`). No PyTorch `Trainer`, `SFTTrainer`, `ORPOTrainer`, or collators are implemented. | **CRITICAL BLOCKER** |
| **5. SFT Data Formatting** | **BLOCKED** | Raw classification data exists (15,090 RAGTruth, 14,000 HaluEval), but paper-mandated evidence-grounded reasoning traces (`<think>` blocks + JSON citations) do not exist. RAGTruth `validation.jsonl` is 0 bytes. | **MAJOR BLOCKER** |
| **6. ORPO / Preference Data** | **BLOCKED** | 7,000 raw QA answer pairs exist in HaluEval, but HalluGuard-mandated SRM reasoning trace preference pairs (chosen vs rejected justifications) do not exist. `trl` is absent. | **MAJOR BLOCKER** |
| **7. Dataset Split Integrity** | **CONDITIONALLY_READY** | RAGTruth (15,090 train, 2,700 test) and HaluEval (14,000 train, 3,000 val, 3,000 test) have zero source leakage. HotpotQA and MS MARCO are strictly validation-only. | **PASS WITH CONDITION** |
| **8. Research Compliance** | **BLOCKED** | Paper-mandated 4B parameter Small Reasoning Model (SRM) training cannot be executed under current hardware constraints. | **MAJOR BLOCKER** |
| **9. Evaluation Harness** | **READY** | Canonical zero-shot evaluation pipeline (`tools/evaluation/run_track02_benchmarks.py`) is fully verified, deterministic, and reproducible. | **PASS** |

---

## 3. Detailed Summary of Critical Blockers

### Blocker 1: Total Absence of Dedicated GPU Hardware
- **Observed Hardware:** 13th Gen Intel Core i7-1355U (10 cores, 12 threads), integrated graphics only.
- **GPU Availability:** `nvidia-smi` returned command not found. CUDA device count is 0. Available VRAM is **0 GB**.
- **Host Memory State:** 15 GiB physical RAM, 13 GiB in active use, only **2.2 GiB available**. Swap is **99.9% exhausted** (5.9 GiB used out of 5.9 GiB).
- **Impact:** The HalluGuard paper requires a **4B parameter** Small Reasoning Model (e.g. Qwen2.5-Coder-4B or Llama-3-4B backbone). In 16-bit precision, loading weights alone requires ~8 GB; training with LoRA requires ~14–16 GB VRAM; even 4-bit QLoRA requires ~6–8 GB VRAM. Training any model >100M parameters on this host will immediately trigger Linux Out-Of-Memory (OOM) process termination.

### Blocker 2: Machine Learning Framework Dependencies Not Installed
- Inspection of the active Python virtual environment (`/home/aditya/rags/.venv/bin/pip list`) revealed that:
  - `torch` is **missing**.
  - `transformers` is **missing**.
  - `peft` is **missing**.
  - `trl` (Transformer Reinforcement Learning for ORPO/DPO) is **missing**.
  - `accelerate` is **missing**.
  - `bitsandbytes` is **missing**.
- The environment contains data manipulation libraries (`pandas`, `scikit-learn`, `tokenizers`, `huggingface_hub`, `datasets`), but lacks the runtime libraries required to instantiate a neural model or compute a single gradient update.

### Blocker 3: Missing Model Checkpoints & Offline Policy
- **Directory Inspection:** `models/pretrained/`, `models/checkpoints/`, and `models/detectors/` contain only empty `.gitkeep` markers (0 bytes).
- **Hugging Face Cache:** `~/.cache/huggingface/hub/` contains dataset shards for HotpotQA and MS MARCO, but zero model weight snapshots.
- **Engine Configuration Invariant:** `trustrag.config.engine_config.SRMConfig` enforces `local_files_only: True` and defaults to `backend: "disabled"` and `model_name: "halluguard-srm-fallback"`.
- **Impact:** No neural model can be instantiated offline without staging model weights.

### Blocker 4: Zero Training Infrastructure Implemented
- An exhaustive search of `src/`, `tools/`, and `scripts/` found **zero training scripts**.
- There are no training configuration YAML files, no training entrypoints, no dataset-to-tensor collators, no learning rate schedulers, and no checkpoint-saving routines.
- `src/trustrag/srm/hf_local.py` is strictly an *inference-only* wrapper for pre-existing checkpoints and explicitly raises `ProviderError` when `torch` or `transformers` are absent.

### Blocker 5: Unformatted Training Targets for SRM Reasoning
- While `data/processed/ragtruth/train.jsonl` (15,090 records) and `data/processed/halueval/train.jsonl` (14,000 records) exist:
  - They provide raw ground-truth classification labels (`FACTUAL` vs `HALLUCINATED`).
  - They do **not** contain the multi-hop reasoning traces (`<think> ... </think>`) or structured JSON citation payloads required to train an evidence-grounded Small Reasoning Model as specified in the HalluGuard paper.
  - Furthermore, `data/processed/ragtruth/validation.jsonl` is **0 bytes** (empty file), leaving no intermediate validation set for checkpoint selection on RAGTruth.

---

## 4. Remediation Roadmap Required Prior to Training

Before Track 2 training can be marked `READY`, the following steps must be formally executed:

```
[Phase A: Compute & Environment Setup]
  ├── Step A1: Provision compute host with >= 1x NVIDIA A10G (24GB) or A100 (40GB/80GB) GPU.
  ├── Step A2: Install PyTorch (with CUDA support), Transformers, PEFT, TRL, Accelerate, BitsAndBytes.
  └── Step A3: Download and locally stage the designated base model checkpoint (e.g., Qwen2.5-3B/7B or Llama-3.2-3B).

[Phase B: Data Preprocessing & Target Construction]
  ├── Step B1: Generate/format SFT reasoning traces (<think> chains + evidence span citations) for RAGTruth & HaluEval.
  ├── Step B2: Construct valid 80/20 train/validation splits for RAGTruth (populating the empty validation.jsonl).
  └── Step B3: Pair HaluEval factual and hallucinated instances into canonical ORPO preference datasets.

[Phase C: Training Implementation]
  ├── Step C1: Author robust, reproducible training script (tools/training/train_srm.py) with deterministic seeding.
  ├── Step C2: Implement LoRA/QLoRA configuration, evaluation collators, and loss monitoring.
  └── Step C3: Implement automated checkpointing, evaluation logging, and tokenizer artifact persistence.
```

---

## 5. Audit Conclusion

Track 1 established rock-solid, verified heuristic baselines. However, beginning neural training at this juncture is impossible. **Track 2 training is formally classified as BLOCKED until GPU hardware, framework dependencies, model checkpoints, and training harnesses are provisioned and verified.**

