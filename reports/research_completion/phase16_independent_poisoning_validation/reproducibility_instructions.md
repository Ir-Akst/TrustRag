# TrustRAG Phase 16: Exact Reproducibility Instructions

**Auditor:** Senior RAG Security Research Engineer, Red-Team Evaluator & Independent ML Auditor  
**Date:** 2026-11-19T00:32:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-16`  
**Parent Release Tag:** `trustrag-v1.0.0-rc1` (Commit: `531bff32745ede1bd1b38609cc6daf653d3eff24`)  
**Frozen Model Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  

---

## 1. Prerequisites & Execution Environment

All experiments are executed in a clean, reproducible Python 3.10 virtual environment with local dependencies.

```bash
# Target repository root
cd /home/aditya/rags/TrustRag-phase11

# Verify Git status
git status
# Confirm HEAD is 531bff32745ede1bd1b38609cc6daf653d3eff24 (tag: trustrag-v1.0.0-rc1)

# Set execution environment variables
export PYTHONPATH=src
export VENV_PY=/home/aditya/rags/.venv-phase15-clean10/bin/python
```

---

## 2. Checkpoint Cryptographic Integrity Verification

Validate the frozen DeBERTa-v3-small NLI model weights:

```bash
cd /home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch
sha256sum -c checksums.sha256

# Expected output:
# checkpoint_meta.json: OK
# config.json: OK
# model.safetensors: OK
# optimizer.pt: OK
# rng_state.pt: OK
# scheduler.pt: OK
# tokenizer.json: OK
# tokenizer_config.json: OK
```

---

## 3. Dataset Integrity Verification

Validate the evaluation benchmark files:

```bash
cd /home/aditya/rags/TrustRag-phase11

# Compute and check SHA-256 digests:
sha256sum data/raw/custom_security/raw_train.jsonl
# Expected: 823bca9639587ff7170530a67c2b35c54d959ee2007bdb554c3e50143c4dae00

sha256sum data/benchmarks_backup/knowledge_poisoning/test.jsonl
# Expected: a833b154cdb9fd418beb5d33dd622ebfcbc5791a3849dec29b84cd27441c7dd7

sha256sum data/benchmarks_backup/knowledge_poisoning/train.jsonl
# Expected: ba83bceaa743c2e4ccaf3ea8fce52a99949444a866584815a460157efdd4b4d9

sha256sum data/benchmarks/knowledge_poisoning/test.jsonl
# Expected: b1dcfd265c8a905e6ca581f5624bc515ab16e5e56095dbb50d6a72693e3175e6
```

---

## 4. Executing the Controlled Baseline Campaign

To re-run the 5-configuration baseline comparison and reproduce all metrics:

```bash
cd /home/aditya/rags/TrustRag-phase11

PYTHONPATH=src $VENV_PY reports/research_completion/phase16_independent_poisoning_validation/evaluate_campaign.py
```

### Generated Artifacts
The script automatically produces and populates:
- `reports/research_completion/phase16_independent_poisoning_validation/step03_experiment_metrics.json`
- `reports/research_completion/phase16_independent_poisoning_validation/step03_baseline_comparison.md`
- `reports/research_completion/phase16_independent_poisoning_validation/step04_security_utility_analysis.md`
- `reports/research_completion/phase16_independent_poisoning_validation/step05_failure_analysis.md`

---

## 5. Verifying Deliverable Checksums

Validate all generated Phase 16 audit deliverables:

```bash
cd /home/aditya/rags/TrustRag-phase11/reports/research_completion/phase16_independent_poisoning_validation
sha256sum -c sha256_manifest.txt
```

