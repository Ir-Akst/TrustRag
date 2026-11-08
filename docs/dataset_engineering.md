# TrustRAG — Dataset Engineering & Security Benchmark Construction (Phase 01 & Phase 02)

This document outlines the architecture, usage, and operational guidelines for the TrustRAG Dataset Engineering and Security Benchmark subsystem (`trustrag.data`), including acquisition management, quality auditing, standardized taxonomy, security benchmark construction, manifest portability, and workflow isolation.

---

## 1. Subsystem Architecture

The dataset engineering and benchmark construction pipeline resides under `src/trustrag/data/`:

```
src/trustrag/data/
├── base.py                   # BaseAdapter, DatasetMetadata, ProcessingStats interfaces
├── schemas.py                # Typed Pydantic record models (DocumentRecord, QueryRecord, etc.)
├── taxonomy.py               # Standardized taxonomy enums & label normalization
├── quality.py                # DatasetQualityAuditor & DatasetQualityReport (integrity & health)
├── resource.py               # ResourceManager & storage pre-allocation checks
├── registry.py               # Dataset registry, metadata inspection, and pipeline orchestration
├── isolation.py              # DatasetUsageCategory & DatasetUsageValidator (Training vs Eval isolation)
├── exceptions.py             # DataError, AcquisitionError, ValidationError, SplitError, UsageIsolationError, ManifestError
├── validation.py             # RecordValidator, quality checks, label validation, and reports
├── splitting.py              # LeakageResistantSplitter, grouped isolation, and leakage reports
├── storage.py                # DatasetStorage (atomic JSONL and Parquet serialization + SHA-256)
├── manifest.py               # ManifestManager, DatasetManifest, and Dataset Card generator
├── cli.py                    # Command-line interface (`trustrag-data` or `python -m trustrag.data.cli`)
├── acquisition/
│   ├── hf.py                 # Hugging Face Datasets integration (streaming, limits, offline check)
│   ├── local.py              # Local file importer (.json, .jsonl, .csv, .parquet)
│   └── manager.py            # AcquisitionManager (tier prioritization, immutable raw storage, audit logging)
├── benchmarks/
│   ├── builder.py            # BenchmarkBuilder (Clean RAG, Poisoning, Hallucination, Robustness)
│   └── security_generator.py # 1,000 paired clean/poisoned synthetic security document generator
├── preprocessing/
│   ├── cleaning.py           # Safe NFKC Unicode normalization, whitespace collapse
│   └── deduplication.py      # Stable SHA-256 content hash exact duplicate detection
└── loaders/                  # Concrete dataset adapters
    ├── natural_questions.py  # Google Natural Questions
    ├── hotpotqa.py           # HotpotQA multi-hop benchmark
    ├── ms_marco.py           # Microsoft MARCO
    ├── squad.py              # Stanford Question Answering Dataset (SQuAD)
    ├── boolq.py              # Google BoolQ
    ├── halueval.py           # HaluEval hallucination evaluation
    ├── ragtruth.py           # RAGTruth hallucination detection benchmark
    ├── llm_aggrefact.py      # LLM-AggreFact (gated, evaluation benchmark only)
    ├── wice.py               # WiCE fine-grained entailment
    ├── expertqa.py           # ExpertQA expert attribution evaluations
    ├── rsb.py                # RSB (RAG Security Bench) poisoning benchmark
    ├── custom_security.py    # Custom TrustRAG security & paired poisoning benchmark
    └── fineweb.py            # FineWeb training corpus (sampled)
```

---

## 2. Supported Datasets & Usage Categories

TrustRAG enforces 5 explicit workflow usage categories via `DatasetUsageValidator`:
- `TRAINING`: Datasets permitted for model fine-tuning and index construction.
- `VALIDATION`: Internal validation splits for checkpoint evaluation.
- `EVALUATION`: Benchmark datasets reserved strictly for out-of-domain evaluation.
- `TRAINING_CORPUS`: Large-scale pretraining corpora (e.g. FineWeb).
- `SECURITY_BENCHMARK`: Adversarial and poisoning evaluation benchmarks (e.g. RSB).

| Dataset Name | Category | Normalized Schema | Source Identifier / Repository | License | Permitted for Training | Permitted for Evaluation | Enforced Isolation |
|---|---|---|---|---|:---:|:---:|---|
| `natural_questions` | `rag_qa` | `QueryRecord` | `google-research-datasets/natural_questions` | CC-BY-SA-3.0 | Yes | Yes | `TRAINING`, `EVALUATION` |
| `hotpotqa` | `rag_qa` | `QueryRecord` | `hotpotqa/hotpot_qa` | CC-BY-SA-4.0 | Yes | Yes | `TRAINING`, `EVALUATION` |
| `ms_marco` | `rag_qa` | `QueryRecord` | `microsoft/ms_marco` | MSR-LA (Non-comm) | Yes | Yes | `TRAINING`, `EVALUATION` |
| `squad` | `rag_qa` | `QueryRecord` | `rajpurkar/squad` | CC-BY-SA-4.0 | Yes | Yes | `TRAINING`, `EVALUATION` |
| `boolq` | `rag_qa` | `QueryRecord` | `google/boolq` | CC-BY-SA-3.0 | Yes | Yes | `TRAINING`, `EVALUATION` |
| `halueval` | `hallucination` | `ClaimVerificationRecord` | `pminervini/HaluEval` | MIT | Yes | Yes | `TRAINING`, `EVALUATION` |
| `ragtruth` | `hallucination` | `ClaimVerificationRecord` | `ParticleMedia/RAGTruth` | MIT | Yes | Yes | `TRAINING`, `EVALUATION` |
| `llm_aggrefact` | `hallucination` | `ClaimVerificationRecord` | `lytang/LLM-AggreFact` | CC-BY-ND-4.0 | **NO** | Yes | **EVALUATION ONLY (Training Blocked)** |
| `wice` | `hallucination` | `ClaimVerificationRecord` | `ryokamoi/wice` | CC-BY-SA-4.0 | Yes | Yes | `TRAINING`, `EVALUATION` |
| `expertqa` | `hallucination` | `ClaimVerificationRecord` | `chaitanyamalaviya/ExpertQA` | MIT | Yes | Yes | `TRAINING`, `EVALUATION` |
| `rsb` | `security` | `SecurityRecord` | `arXiv:2505.18543` | Pending / Not Verified | **NO** | Yes | **SECURITY BENCHMARK ONLY (Training Blocked)** |
| `custom_security` | `security` | `SecurityRecord` | `trustrag/internal_security` | MIT | Yes | Yes | `TRAINING`, `SECURITY_BENCHMARK` |
| `fineweb` | `training_corpus` | `DocumentRecord` | `HuggingFaceFW/fineweb` | ODC-By-1.0 | Yes | **NO** | **TRAINING CORPUS ONLY (Eval Blocked)** |

---

## 3. Split Preservation and Leakage Prevention

### A. Official Split Preservation by Default
Official benchmark evaluation splits (such as `validation` or `test`) are never silently repartitioned. When inspecting or storing official partitions, they are saved under `data/processed/{name}/{split}.jsonl` with manifest metadata `split_type: "official"`.

### B. Explicit Custom Splitting
Custom 70/15/15 partitions are performed only when `--custom-split` is explicitly requested. Custom partitions are isolated into `data/processed/{name}/custom_splits/` with manifest `split_type: "custom"`.

### C. Grouped Split Isolation
All related records (clean and poisoned passage pairs sharing a document ID, or multiple queries referencing the same document) are guaranteed to remain in the same partition.

### D. Cross-Split Duplicate Content Leakage Audit
`LeakageResistantSplitter.audit_partitions` verifies that no identical content hashes or group IDs overlap across splits.

---

## 4. Manifest Portability & Consistency Validation

Manifests are saved as `manifest.json` and accompany a rendered `README.md` dataset card.

Key portability features:
1. **Relative Paths:** File paths are strictly relative to the manifest directory (e.g. `validation.jsonl` or `custom_splits/custom_train.jsonl`) using forward slashes (`/`), ensuring seamless execution on Windows and Linux.
2. **Recorded Line Counts and Checksums:** Every entry contains file size in bytes, SHA-256 checksum, and line/record counts.
3. **Consistency Validation:** `ManifestManager.validate_manifest()` verifies file existence, sizes, checksums, and record counts against disk state (`PASS`).

---

## 5. CLI Usage Guide

### A. List & Inspect
```bash
python -m trustrag.data.cli list
python -m trustrag.data.cli inspect boolq
python -m trustrag.data.cli inspect llm_aggrefact
```

### B. Acquire / Preprocess
```bash
# Preprocess with a smoke target of 100 records
python -m trustrag.data.cli preprocess boolq --split validation --smoke-test --limit 100 --output-dir data/processed/boolq
```

### C. Audit Official Split (No Silent Repartitioning)
```bash
python -m trustrag.data.cli split-stats boolq --local-path data/processed/boolq/validation.jsonl
```

### D. Generate Custom 70/15/15 Splits
```bash
python -m trustrag.data.cli split-stats boolq --local-path data/processed/boolq/validation.jsonl --custom-split --output-dir data/processed/boolq/custom_splits --seed 42
```

### E. Generate & Validate Manifest
```bash
python -m trustrag.data.cli manifest boolq --dir data/processed/boolq --validate
python -m trustrag.data.cli manifest boolq --dir data/processed/boolq/custom_splits --validate
```

---

## 6. Phase 02 Benchmark Construction & Security Generation

Phase 02 constructs 4 specialized research benchmarks under `data/benchmarks/`:

### A. Benchmark Categories
1. **Benchmark A — Clean RAG (`data/benchmarks/clean_rag/`):**
   - **Schema:** `QueryRecord`
   - **Focus:** Standard baseline retrieval accuracy and uncorrupted factual answering.
2. **Benchmark B — Knowledge Poisoning (`data/benchmarks/knowledge_poisoning/`):**
   - **Schema:** `SecurityRecord`
   - **Focus:** Evaluating detector and guardrail resilience against targeted factual poisoning and trigger denial-of-service. Clean and poisoned document pairs share identical `source_id` to guarantee grouped partition isolation.
3. **Benchmark C — Hallucination Detection (`data/benchmarks/hallucination/`):**
   - **Schema:** `ClaimVerificationRecord`
   - **Focus:** Evidence-grounded claim verification and fine-grained factual attribution (RAGTruth, WiCE, ExpertQA). Standardized labels: `SUPPORTED`, `CONTRADICTED`, `NOT_ENOUGH_EVIDENCE`.
4. **Benchmark D — Adversarial Robustness (`data/benchmarks/adversarial_robustness/`):**
   - **Schema:** `SecurityRecord`
   - **Focus:** Compound attack resilience spanning prompt injection, jailbreaks, malicious instruction payloads, denial-of-service, and benign instruction control samples.

### B. Benchmark Construction & Audit CLI Commands
```bash
# Report repository storage tiers (raw, processed, benchmarks) and acquisition targets
python -m trustrag.data.cli storage

# Acquire priority dataset with pre-allocation safety
python -m trustrag.data.cli acquire custom_security --smoke-test
python -m trustrag.data.cli acquire ragtruth --split test --limit 10 --offline

# Construct all 4 benchmarks
python -m trustrag.data.cli benchmark build --category all --limit 200

# Audit benchmarks for zero group/content hash leakage and data health
python -m trustrag.data.cli benchmark audit --category all
python -m trustrag.data.cli benchmark audit --category clean_rag
python -m trustrag.data.cli benchmark audit --category knowledge_poisoning
python -m trustrag.data.cli benchmark audit --category hallucination
python -m trustrag.data.cli benchmark audit --category adversarial_robustness

# Validate benchmark files with quality health metrics
python -m trustrag.data.cli validate data/benchmarks/clean_rag/test.jsonl
python -m trustrag.data.cli validate data/benchmarks/knowledge_poisoning/test.jsonl
```
