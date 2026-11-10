# TrustRAG

## Project Overview

TrustRAG is a research-grade Retrieval‑Augmented Generation (RAG) security system focused on ensuring trustworthy generation through input guardrails, multi‑signal detection, and output verification.

## Architecture Overview

```
User Query → G1 (Input Guardrails) → Retrieval → G2 (Multi‑Signal Detection) → Generation → G3 (Output Verification) → SRM
```

- **Phase 00:** Engineering foundation, structured logging, configuration hierarchy, error taxonomy, and reproducibility utilities.
- **Phase 01:** Dataset engineering, multi-source acquisition, schema normalization, safe text cleaning, cryptographic deduplication, leakage-resistant splitting, dataset manifests, and dataset cards.
- **Phase 02:** Dataset acquisition engineering, priority-tier acquisition management, pre-allocation disk safety, label taxonomy standardization, synthetic security generation (clean/poisoned paired records with zero leakage), and construction of 4 research benchmarks (`clean_rag`, `knowledge_poisoning`, `hallucination`, `adversarial_robustness`).
- **Phase 03:** Core defense engine integrating G1 Input Guardrail, TF-IDF trust-aware retrieval with G2 Multi-Signal Detection (MSD), evidence-grounded generation, G3 claim-level evidence verification, HalluGuard-inspired SRM integration (configurable HTTP + deterministic fallback), and end-to-end `TrustRAGPipeline`.

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

Detailed documentation is available in [docs/dataset_engineering.md](docs/dataset_engineering.md) and [docs/architecture.md](docs/architecture.md).

## End-to-End Defense Pipeline CLI (Phase 03)

Run the integrated `G1 -> Retrieval/G2 -> Generation -> G3 -> SRM` pipeline over local datasets:

```bash
# Clean RAG query execution
python -m trustrag.pipeline.cli --corpus data/benchmarks/clean_rag/test.jsonl --query "Can an odd number be divided by an even number?" --top-k 2

# Knowledge poisoning conflict & prompt-injection defense run
python -m trustrag.pipeline.cli --corpus data/benchmarks/adversarial_robustness/train.jsonl --query "How do agents verify customer identity?" --top-k 2 --json
```

## Testing

```bash
# Run unit tests (offline, hermetic)
pytest

# Run live integration tests (requires network access)
pytest -m integration
```

## Configuration

Engine and defense parameters (G1 guardrails, retrieval, G2 MSD weights/thresholds, G3 verification, SRM backends) are configured in `configs/base.yaml`, dataset targets in `configs/datasets.yaml`, and all sections support `TRUSTRAG_<SECTION>_<FIELD>` environment overrides.
