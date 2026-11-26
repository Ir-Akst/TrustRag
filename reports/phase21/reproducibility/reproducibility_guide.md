# TrustRAG Phase 21 — Standalone Research Reproducibility Guide

**Author:** Principal Research Scientist & Reproducibility Specialist  
**Date:** 2026-11-24  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-21-final-research-validation`  
**Anchor Commit:** `531bff32745ede1bd1b38609cc6daf653d3eff24`  
**Tag:** `trustrag-v1.0.0-rc1`  

---

## 1. System Requirements & Execution Environment

### 1.1 Hardware Specifications
- **CPU:** 8-core x86_64 CPU (Intel Xeon / AMD EPYC or equivalent)
- **RAM:** Minimum 16 GB system memory (32 GB recommended)
- **Storage:** Minimum 20 GB free disk space for model weights and benchmark splits
- **GPU:** Optional. All Phase 19/21 evaluations run deterministically on CPU via PyTorch / HuggingFace Transformers.

### 1.2 Software Specifications
- **Operating System:** Linux (Ubuntu 22.04 LTS / Debian 12 recommended)
- **Python Runtime:** Python 3.10.x or 3.11.x
- **Virtual Environment:** Dedicated venv containing:
  - `torch >= 2.0.0`
  - `transformers >= 4.30.0`
  - `scipy >= 1.10.0`
  - `numpy >= 1.24.0`
  - `pandas >= 2.0.0`
  - `scikit-learn >= 1.2.0`

---

## 2. Checkpoint Verification

Before running evaluations, verify the frozen DeBERTa checkpoint using SHA-256:

```bash
cd /home/aditya/rags/TrustRag-phase11
python -c '
import hashlib, json

manifest = json.load(open("reports/phase21/reproducibility/checkpoint_manifest.json"))
base_dir = manifest["checkpoint_directory"]

for filename, expected_hash in manifest["file_hashes_sha256"].items():
    filepath = f"{base_dir}/{filename}"
    computed = hashlib.sha256(open(filepath, "rb").read()).hexdigest()
    assert computed == expected_hash, f"Hash mismatch on {filename}!"
print("100% Checkpoint Integrity Confirmed.")
'
```

---

## 3. Evaluation Reproduction Commands

### 3.1 NLI Validation Set Evaluation ($N=2,662$)
```bash
python scripts/generate_confusion_and_ablation.py
```
This recomputes the $3 \times 3$ confusion matrix and confirms:
- Overall Accuracy: $70.40\%$
- Macro F1: $55.04\%$
- Contradiction F1: $36.22\%$

### 3.2 Controlled Defense Layer Ablations ($N=875$ Attacks, $N=1,000$ Clean)
```bash
python scripts/generate_confusion_and_ablation.py
```
Outputs:
- `reports/phase21/tables/ablation_metrics.csv`
- `reports/phase21/tables/ablation_subtype_metrics.csv`

### 3.3 Public Benchmark Reconciliation (RAGTruth & HaluEval, $N=200$ each)
```bash
python scripts/generate_phase21_reconciliation.py
```
Outputs:
- `reports/phase21/ragtruth_reconciled_results.csv`
- `reports/phase21/halueval_reconciled_results.csv`
- `reports/phase21/benchmark_reconciliation.json`

### 3.4 Dataset Leakage Verification
```bash
python scripts/verify_dataset_leakage.py
```
Confirms $0$ exact collisions between SFT training data and all evaluation splits.

---

## 4. Deterministic Seeds & Hyperparameters

- **Global Evaluation Seed:** `42`
- **PyTorch Determinism:**
  ```python
  import torch, numpy as np, random
  random.seed(42)
  np.random.seed(42)
  torch.manual_seed(42)
  torch.set_num_threads(2)
  ```
- **G2 Removal Cap:** $C_r = 0.50$ (Max $50\%$ passages pruned)
- **G3 Positive Entailment Threshold:** $\tau_{\text{entail}} = 0.65$
- **Premise Normalization:** Regex citation bracket removal enabled
