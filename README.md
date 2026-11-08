# TrustRAG

## Project Overview

TrustRAG is a research-grade Retrieval‑Augmented Generation (RAG) security system focused on ensuring trustworthy generation through input guardrails, multi‑signal detection, and output verification.

## Architecture Overview

```
G1 (Input Guardrails) → MSD (Multi‑Signal Detection) → Retrieval → Generation → G3 (Output Verification)
```

- **Phase 00:** Engineering foundation, structured logging, configuration hierarchy, error taxonomy, and reproducibility utilities.
- **Phase 01:** Dataset engineering, multi-source acquisition, schema normalization, safe text cleaning, cryptographic deduplication, leakage-resistant splitting, dataset manifests, and dataset cards.
- **Phase 02:** Dataset acquisition engineering, priority-tier acquisition management, pre-allocation disk safety, label taxonomy standardization, synthetic security generation (clean/poisoned paired records with zero leakage), and construction of 4 research benchmarks (`clean_rag`, `knowledge_poisoning`, `hallucination`, `adversarial_robustness`).

## Setup

```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## Dataset Engineering & Security Benchmark CLI (Phase 01 & Phase 02)

The subsystem provides commands via `python -m trustrag.data.cli` or `trustrag-data`:

```bash
# List all registered datasets
python -m trustrag.data.cli list

# Inspect dataset metadata, licensing, and access conditions
python -m trustrag.data.cli inspect halueval

# Report repository storage breakdown (raw, processed, benchmarks) and acquisition status
python -m trustrag.data.cli storage

# Acquire priority datasets with pre-allocation disk safety
python -m trustrag.data.cli acquire custom_security --smoke-test
python -m trustrag.data.cli acquire ragtruth --split test --limit 10 --offline

# Build all 4 research benchmark categories under data/benchmarks/
python -m trustrag.data.cli benchmark build --category all --limit 200

# Audit benchmarks for group isolation and zero cross-partition leakage
python -m trustrag.data.cli benchmark audit --category all

# Validate benchmark and processed partitions with health quality checks
python -m trustrag.data.cli validate data/benchmarks/clean_rag/test.jsonl
python -m trustrag.data.cli validate data/benchmarks/knowledge_poisoning/test.jsonl

# Preprocess and deduplicate a dataset partition
python -m trustrag.data.cli preprocess boolq --split validation --smoke-test

# Audit leakage-resistant grouped splitting
python -m trustrag.data.cli split-stats boolq --smoke-test --seed 42

# Generate machine-readable manifest.json and dataset card README.md
python -m trustrag.data.cli manifest boolq --dir data/processed/boolq
```

Detailed documentation is available in [docs/dataset_engineering.md](docs/dataset_engineering.md).

## Testing

```bash
# Run unit tests (offline, hermetic)
pytest

# Run live integration tests (requires network access)
pytest -m integration
```

## Configuration

Dataset targets, paths, preprocessing, and splitting parameters are configured in `configs/datasets.yaml` and can be overridden via `TRUSTRAG_` environment variables.
