# TrustRAG — Full Independent Reproducibility & Research Replication Guide

**Author:** Principal Research Engineer & Reproducibility Specialist  
**Date:** 2026-11-19T01:35:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Dedicated Branch:** `phase-17-20-final-release`  
**Target Release Tag:** `trustrag-v1.0.0-rc1`  
**Frozen Model Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  

---

## 1. Overview & Replication Mandate

This guide provides exhaustive, step-by-step instructions for an independent researcher or auditor to replicate all experimental results, benchmarks, and performance profiles documented across Phases 11 through 20.

All experiments are designed to run deterministically on standalone x86_64 CPU hardware without requiring GPUs or external network access.

---

## 2. Hardware, Software & Environment Prerequisites

### 2.1 Hardware Requirements
- **Architecture:** x86_64 Linux (tested on Linux 6.x kernel)
- **CPU:** 4+ physical cores (minimum 2 physical cores, 12 logical cores recommended)
- **RAM:** Minimum 4 GB available system memory (peak process RSS is $774.54\text{ MB}$)
- **Disk:** 5 GB free disk space

### 2.2 Clean Virtual Environment Setup
Ensure Python 3.10 is used. All dependencies must be isolated:

```bash
# Navigate to project root
cd /home/aditya/rags/TrustRag-phase11

# Activate the clean verified virtual environment
source /home/aditya/rags/.venv-phase15-clean10/bin/activate

# Verify critical package versions
python -c "
import torch, transformers, pydantic, numpy
print('PyTorch:', torch.__version__)
print('Transformers:', transformers.__version__)
print('Pydantic:', pydantic.__version__)
print('NumPy:', numpy.__version__)
"
```
*Expected Output:*
- PyTorch: `2.14.1+cpu`
- Transformers: `5.20.2`
- Pydantic: `2.14.3`
- NumPy: `2.2.6`

---

## 3. Checkpoint Integrity Verification

Before running any script, cryptographically verify that the frozen DeBERTa-v3-small checkpoint has not been modified or corrupted:

```bash
cd /home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch
sha256sum -c checksums.sha256
```
*Expected Output:*
```
added_tokens.json: OK
config.json: OK
model.safetensors: OK
special_tokens_map.json: OK
spm.model: OK
tokenizer_config.json: OK
tokenizer.json: OK
training_args.bin: OK
```
`model.safetensors` must strictly match SHA-256 digest: `0464758a5c317ad5fe93a64ec9e97c672b1236ef8b33c0ce293c06e8902d08a5`.

---

## 4. Step-by-Step Experiment Execution

### 4.1 Step 1: Replicate Phase 18 Advanced Security Red Teaming
Execute the 15-category red teaming evaluation ($N=460$ attack instances):

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv-phase15-clean10/bin/python tools/evaluation/run_phase18_redteam.py
```
*Expected Outcome:*
- Total Evaluated: `460`
- Defended: `166` (`36.09%`)
- Breached: `294` (`63.91%`)
- Wilson 95% CI: `[31.83%, 40.57%]`
- Output files created:
  - `reports/research_completion/final_independent_validation_and_release/raw_predictions/phase18_redteam_predictions.jsonl`
  - `reports/research_completion/final_independent_validation_and_release/phase18_attack_dataset_manifest.json`

### 4.2 Step 2: Replicate Phase 19 Performance & Scalability Profiling
Execute the hardware profiling and thread benchmark:

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv-phase15-clean10/bin/python tools/evaluation/run_phase19_scalability.py
```
*Expected Outcome:*
- 2 Threads P50 Latency: $\sim 55.84\text{ ms}$ (vs. $\sim 97.72\text{ ms}$ for 1 thread)
- Peak RSS: $\sim 774\text{ MB}$
- Output file created:
  - `reports/research_completion/final_independent_validation_and_release/phase19_scalability_results.json`

### 4.3 Step 3: Replicate Dataset Leakage & Statistical Verification
Verify zero data leakage between SFT training splits and test partitions:

```bash
cd /home/aditya/rags/TrustRag-phase11
PYTHONPATH=src /home/aditya/rags/.venv-phase15-clean10/bin/python -c '
import json, glob
print("Running Leakage Verification...")
# Check sft_v2/nli train vs val
with open("data/processed/sft_v2/nli/dataset_manifest.json") as f:
    m = json.load(f)
assert m["leakage_verification"]["train_val_doc_overlap"] == 0
assert m["leakage_verification"]["halueval_contamination"] == 0
print("LEAKAGE VERIFICATION: PASS (Zero Contamination)")
'
```

---

## 5. Artifact Verification via Manifest

Generate and verify all deliverable hashes:

```bash
cd /home/aditya/rags/TrustRag-phase11/reports/research_completion/final_independent_validation_and_release
sha256sum -c sha256_manifest.txt
```
All files must report `OK`.

