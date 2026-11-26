# TrustRAG Phase 22 — Exact Reproduction Commands & Execution Guide

**Author:** Principal ML Research Scientist & Reproducibility Specialist  
**Date:** 2026-11-24  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-22-external-benchmark-validation`  
**Deliverable:** `reports/phase22/reproduction_commands.md`  

---

## 1. Environment & Hardware Specifications

- **OS:** Linux x86_64 (Ubuntu 22.04 LTS / Debian 12)
- **CPU:** 8-core CPU or higher (minimum 16 GB RAM)
- **Python:** Python 3.10.x with virtual environment `/home/aditya/rags/.venv-phase15-clean10`
- **PyTorch Threads:** 2 CPU threads configured for intra-op parallelism
- **Evaluation Seed:** `42`

---

## 2. Pre-Evaluation Checkpoint Verification

Before executing evaluations, confirm that the frozen model checkpoint is bit-for-bit identical to reference checksums:

```bash
cd /home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch
sha256sum -c checksums.sha256
```
Expected output: All 8 files report `OK`.

---

## 3. Benchmark Dataset Integrity Check

Verify the presence and integrity of authentic PoisonedRAG and RSB benchmark files:

```bash
cd /home/aditya/rags/TrustRag-phase11

python -c '
import json, os

pr_dir = "data/raw/external_benchmarks/PoisonedRAG/results/adv_targeted_results"
for split in ["hotpotqa.json", "msmarco.json", "nq.json"]:
    data = json.load(open(os.path.join(pr_dir, split)))
    print(f"PoisonedRAG {split}: {len(data)} queries verified.")

pa_dir = "data/raw/external_benchmarks/PoisonArena/datasets/incorrect_ans"
data_ms = json.load(open(os.path.join(pa_dir, "ms-selected-queries-adv-ans-docs.json")))
data_nq = json.load(open(os.path.join(pa_dir, "nq-all-adv-docs.json")))
print(f"RSB MS-MARCO: {len(data_ms)} queries verified.")
print(f"RSB NQ: {len(data_nq)} queries verified.")
'
```

---

## 4. Full Benchmark Reproduction Command

Execute the end-to-end evaluation harness across all 6 configurations:

```bash
cd /home/aditya/rags/TrustRag-phase11
/home/aditya/rags/.venv-phase15-clean10/bin/python tools/evaluation/run_phase22_external_evaluation.py
```

Outputs generated:
- `reports/phase22/benchmark_metrics.csv`
- `reports/phase22/raw_predictions/poisonedrag_predictions.jsonl`
- `reports/phase22/raw_predictions/rsb_predictions.jsonl`

---

## 5. Deliverable Packaging & Metrics Generation

Generate summary tables, confidence intervals, and confusion matrices:

```bash
cd /home/aditya/rags/TrustRag-phase11
/home/aditya/rags/.venv-phase15-clean10/bin/python tools/evaluation/generate_phase22_deliverable_data.py
```

Outputs generated:
- `reports/phase22/subtype_metrics.csv`
- `reports/phase22/confidence_intervals.json`
- `reports/phase22/confusion_matrices.json`
- `reports/phase22/dataset_manifest.json`
