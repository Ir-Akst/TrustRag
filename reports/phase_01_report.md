# TrustRAG — Phase 01: Dataset Engineering Final Report

**Date:** November 8, 2026  
**Phase:** Phase 01 — Dataset Engineering  
**Subsystem:** `trustrag.data`  
**Status:** Completed  

---

## 1. Implemented Architecture

The Dataset Engineering subsystem is structured under `src/trustrag/data/` as a modular, decoupled, and reproducible pipeline:

```
src/trustrag/data/
├── base.py                   # BaseAdapter, DatasetMetadata, ProcessingStats interfaces
├── schemas.py                # Normalized Pydantic record schemas (DocumentRecord, QueryRecord, etc.)
├── registry.py               # Dataset registry, dynamic loader resolution, and pipeline runner
├── isolation.py              # DatasetUsageCategory & DatasetUsageValidator (Workflow Isolation)
├── exceptions.py             # Error hierarchy inheriting from trustrag.exceptions.DatasetError
├── validation.py             # RecordValidator, label validity checks, and ValidationReport
├── splitting.py              # LeakageResistantSplitter (grouped splitting, 0-overlap audit)
├── storage.py                # DatasetStorage (atomic JSONL and Parquet serialization + SHA-256)
├── manifest.py               # ManifestManager, DatasetManifest, and Dataset Card Markdown generator
├── cli.py                    # Unified CLI (trustrag-data / python -m trustrag.data.cli)
├── acquisition/              # Multi-source acquisition layer
│   ├── hf.py                 # Hugging Face Datasets integration (streaming, limits, offline check)
│   └── local.py              # Local file importer (.json, .jsonl, .csv, .parquet)
├── preprocessing/            # Preprocessing & deduplication layer
│   ├── cleaning.py           # Safe NFKC Unicode normalization, whitespace collapse, empty detection
│   └── deduplication.py      # Stable SHA-256 content-hash exact duplicate tracking & reporting
└── loaders/                  # 13 concrete dataset adapters across 4 categories
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

### Component Flow
```
[Official Source / Local File]
             │
             ▼
      [Acquisition Layer] (hf.py / local.py)
             │ (Raw stream)
             ▼
       [BaseAdapter] (Transform into Typed Record)
             │
             ▼
   [Preprocessing Layer] (clean_text, NFKC, Whitespace Collapse)
             │
             ▼
    [Validation Layer] (RecordValidator, Schema & Label Check)
             │
             ▼
   [Deduplication Layer] (DuplicateDetector via SHA-256 Content Hash)
             │
             ▼
     [Splitting Layer] (LeakageResistantSplitter, Grouped Isolation)
             │
             ▼
      [Storage Layer] (Atomic Write JSONL / Parquet + SHA-256)
             │
             ▼
  [Manifest & Dataset Card] (manifest.json & README.md)
```

---

## 2. Files Created and Modified

### Created Files:
- `src/trustrag/data/base.py`: Abstract adapter, dataset metadata, and processing stats.
- `src/trustrag/data/schemas.py`: Pydantic record models (`DocumentRecord`, `QueryRecord`, `ClaimVerificationRecord`, `SecurityRecord`, `compute_content_hash`).
- `src/trustrag/data/registry.py`: Registry for 13 datasets, adapter resolution, and public loader orchestration.
- `src/trustrag/data/isolation.py`: Workflow usage categories (`DatasetUsageCategory`) and isolation enforcement (`DatasetUsageValidator`).
- `src/trustrag/data/exceptions.py`: Dataset exception hierarchy (`DataError`, `AcquisitionError`, `ValidationError`, `DuplicateRecordError`, `SplitError`, `StorageError`, `ManifestError`, `UsageIsolationError`).
- `src/trustrag/data/validation.py`: Quality validation, label enforcement, and error reporting.
- `src/trustrag/data/splitting.py`: Leakage-resistant grouped train/val/test splitting, official split preservation, and leakage audits.
- `src/trustrag/data/storage.py`: Atomic JSONL and Parquet serialization and SHA-256 checksum computation.
- `src/trustrag/data/manifest.py`: Machine-readable `DatasetManifest` with relative paths, checksums, and Markdown dataset card generation.
- `src/trustrag/data/cli.py`: Unified CLI for listing, inspecting, acquiring, importing, preprocessing, validating, splitting, and manifesting datasets.
- `src/trustrag/data/acquisition/__init__.py`, `hf.py`, `local.py`: Multi-source data acquisition.
- `src/trustrag/data/preprocessing/__init__.py`, `cleaning.py`, `deduplication.py`: Safe cleaning and duplicate detection.
- `src/trustrag/data/loaders/__init__.py`, `natural_questions.py`, `hotpotqa.py`, `ms_marco.py`, `squad.py`, `boolq.py`, `halueval.py`, `ragtruth.py`, `llm_aggrefact.py`, `wice.py`, `expertqa.py`, `rsb.py`, `custom_security.py`, `fineweb.py`: 13 dataset adapters.
- `src/trustrag/config/dataset_config.py`: Pydantic configuration models for dataset settings.
- `configs/datasets.yaml`: Dataset engineering configurations, limits, targets, and paths.
- `tests/unit/data/test_schemas.py`: Schema unit tests.
- `tests/unit/data/test_preprocessing.py`: Cleaning and deduplication unit tests.
- `tests/unit/data/test_acquisition_local.py`: Local file import unit tests.
- `tests/unit/data/test_loaders.py`: Loader and adapter unit tests.
- `tests/unit/data/test_splitting.py`: Leakage-resistant splitting unit tests.
- `tests/unit/data/test_manifest_storage.py`: Storage and manifest unit tests.
- `tests/unit/data/test_registry.py`: Registry unit tests.
- `tests/unit/data/test_validation.py`: Validation unit tests.
- `tests/unit/data/test_cli.py`: CLI unit tests.
- `tests/unit/data/test_audit_corrections.py`: Unit tests for audit corrections (split preservation, custom splitting, leakage detection, group isolation, manifest consistency, portability, isolation rules).
- `tests/integration/test_data_acquisition.py`: Live integration tests.
- `docs/dataset_engineering.md`: Comprehensive subsystem documentation, usage guides, and examples.
- `docs/dataset_license_register.md`: Comprehensive legal license register for all 13 datasets.
- `docs/dataset_field_mapping.md`: Comprehensive field mapping tables and label normalization matrix.
- `reports/phase_01_report.md`: Phase 01 final report.
- `reports/phase_01_correction_report.md`: Phase 01 data integrity audit and correction report.

### Modified Files:
- `pyproject.toml`: Fixed duplicate block from Phase 00, added `pythonpath = ["src"]`, pytest integration markers, and `trustrag-data` console script.
- `src/trustrag/config/settings.py`: Resolved circular imports, integrated `DatasetRootConfig`, and supported environment variable overrides.
- `src/trustrag/config/base.py`: Corrected import of `Settings` and `load_config`.
- `src/trustrag/utils/logging.py`: Updated deprecated `datetime.utcfromtimestamp()` to modern timezone-aware UTC datetime.
- `tests/unit/test_foundation.py`: Added missing `random` import for Phase 00 reproducibility tests.
- `README.md`: Removed unresolved git merge conflict markers, added Phase 01 overview, CLI usage examples, and documentation links.

---

## 3. Supported Datasets and Acquisition Status

| Dataset | Category | Normalized Schema | Acquisition Source | Status |
|---|---|---|---|---|
| Natural Questions (NQ) | RAG QA | `QueryRecord` | `google-research-datasets/natural_questions` | Adapter Implemented & Tested |
| HotpotQA | RAG QA | `QueryRecord` | `hotpotqa/hotpot_qa` | Adapter Implemented & Tested |
| MS MARCO | RAG QA | `QueryRecord` | `microsoft/ms_marco` | Adapter Implemented & Tested |
| SQuAD | RAG QA | `QueryRecord` | `rajpurkar/squad` | Live Download Verified (Integration Test) |
| BoolQ | RAG QA | `QueryRecord` | `google/boolq` | Live Download Verified (100 Smoke Records) |
| HaluEval | Hallucination | `ClaimVerificationRecord` | `pminervini/HaluEval` | Adapter Implemented & Tested |
| RAGTruth | Hallucination | `ClaimVerificationRecord` | `ParticleMedia/RAGTruth` | Local Import Adapter Verified |
| LLM-AggreFact | Hallucination | `ClaimVerificationRecord` | `lytang/LLM-AggreFact` (Gated) | Gated Adapter (Manual HF Agreement Required) |
| WiCE | Hallucination | `ClaimVerificationRecord` | `ryokamoi/wice` | Local Import Adapter Verified |
| ExpertQA | Hallucination | `ClaimVerificationRecord` | `chaitanyamalaviya/ExpertQA` | Local Import / Mirror Adapter Verified |
| RSB Benchmark | Security | `SecurityRecord` | Academic paper arXiv:2505.18543 | Local Import Ready; Remote Marked Pending |
| Custom Security | Security | `SecurityRecord` | `trustrag/internal_security` | Local Import & Synthesis Ready |
| FineWeb | Training Corpus | `DocumentRecord` | `HuggingFaceFW/fineweb` | Streaming Sample Adapter Implemented |

---

## 4. Verified Sources and License Status

| Dataset | Official Source / Repository | Verified License | Terms & Restrictions |
|---|---|---|---|
| Natural Questions | `google-research-datasets/natural_questions` | CC-BY-SA-3.0 / Apache-2.0 | Open for research and development |
| HotpotQA | `hotpotqa/hotpot_qa` | CC-BY-SA-4.0 | Attribution required |
| MS MARCO | `microsoft/ms_marco` | Microsoft Research License | Non-commercial research use |
| SQuAD | `rajpurkar/squad` | CC-BY-SA-4.0 | Standard attribution |
| BoolQ | `google/boolq` | CC-BY-SA-3.0 | Standard attribution |
| HaluEval | `pminervini/HaluEval` | MIT | Permissive commercial and research use |
| RAGTruth | `https://github.com/ParticleMedia/RAGTruth` | MIT | Permissive research use |
| LLM-AggreFact | `https://huggingface.co/datasets/lytang/LLM-AggreFact` | CC-BY-ND-4.0 | **GATED:** Evaluation benchmark ONLY. Model training/fine-tuning strictly prohibited. |
| WiCE | `https://github.com/ryokamoi/wice` | ODC-BY / CC-BY-SA | Human annotations under ODC-BY; Wikipedia text CC-BY-SA |
| ExpertQA | `https://github.com/chaitanyamalaviya/ExpertQA` | MIT | Permissive research use |
| RSB Benchmark | arXiv:2505.18543 | Pending Verification | Academic publication reference; no standalone public download URL |
| Custom Security | Internal | MIT | TrustRAG internal security benchmark |
| FineWeb | `HuggingFaceFW/fineweb` | ODC-By-1.0 | Attribution required; training corpus (not evaluation benchmark) |

### 4.1 Workflow Usage Categories & Isolation Controls

TrustRAG enforces 5 distinct workflow categories via `trustrag.data.isolation.DatasetUsageValidator`:
- `TRAINING`: Datasets permitted for model training and retrieval indexing.
- `VALIDATION`: Internal validation splits for checkpoint selection.
- `EVALUATION`: Reserved benchmark evaluation sets (e.g. LLM-AggreFact).
- `TRAINING_CORPUS`: Pre-training corpora (FineWeb).
- `SECURITY_BENCHMARK`: Adversarial and poisoning benchmark sets (RSB, Custom Security).

**Isolation Rules:**
1. **Evaluation-Only Isolation:** Attempting to route `llm_aggrefact` or `rsb` into `TRAINING` or `TRAINING_CORPUS` raises `UsageIsolationError`.
2. **Corpus Isolation:** Attempting to route `fineweb` into `EVALUATION` or `SECURITY_BENCHMARK` raises `UsageIsolationError`.
3. Detailed legal registers and adapter mappings are maintained in [dataset_license_register.md](../docs/dataset_license_register.md) and [dataset_field_mapping.md](../docs/dataset_field_mapping.md).

---

## 5. Actual Download Counts vs. Configured Targets

Per research integrity rules, actual downloads are strictly kept separate from configured targets and paper-reported sizes:

| Dataset | Paper Reported Size | Configured Engineering Target | Actual Downloaded Records in Phase 01 | Notes |
|---|---:|---:|---:|---|
| BoolQ | ~16,000 | 10,000 | **100** | Downloaded and processed via smoke-test mode |
| SQuAD | ~100,000 | 20,000 | **5** | Downloaded during live integration test |
| Natural Questions | ~300,000 | 30,000 | **0** | Adapter ready; awaiting explicit full run |
| HotpotQA | ~113,000 | 30,000 | **0** | Adapter ready; awaiting explicit full run |
| MS MARCO | ~1,000,000 | 100,000 | **0** | Adapter ready; awaiting explicit full run |
| HaluEval | 35,000 | 10,000 | **0** | Adapter ready; awaiting explicit full run |
| RAGTruth | ~18,000 | Available subset | **0** | Local-import adapter ready |
| LLM-AggreFact | ~11,000 | Available subset | **0** | Requires manual HF user agreement; adapter ready |
| WiCE | ~10,000 | 5,000 | **0** | Local-import adapter ready |
| ExpertQA | ~2,100 | Available subset | **0** | Local-import adapter ready |
| RSB Benchmark | N/A | Available subset | **0** | Pending direct URL; local import adapter ready |
| Custom Security | N/A | 5,000 | **0** | Schema and local adapter ready |
| FineWeb | 15+ Trillion tokens | 20,000 docs | **0** | Streaming sample adapter ready |

---

## 6. Preprocessing and Normalization Behavior

1. **Unicode Normalization:** NFKC normalization transforms compatibility characters (e.g., ligatures `ﬃ` -> `ffi`, full-width `Ｔｅｓｔ` -> `Test`) while preserving semantics.
2. **Whitespace Normalization:** Consecutive spaces and tabs are collapsed to a single space. Consecutive line breaks are collapsed to a maximum of one empty line (`\n\n`), preserving paragraph breaks.
3. **Safe Text Cleaning:** Never strips punctuation (`?`, `!`, `.`, quotes), casing, negations (`not`, `no`, `never`), markdown formatting, or instruction-like keywords critical for security evaluations.
4. **Empty Record Detection:** Records with whitespace-only or empty target content are detected and logged as invalid.

---

## 7. Deduplication Statistics

Deduplication utilizes cryptographic SHA-256 hashes of normalized content. In testing and smoke verification:

- **Algorithm:** SHA-256 hex digest on stripped normalized text.
- **Detector:** `DuplicateDetector` tracks first-seen record IDs.
- **Smoke Run on BoolQ (100 records):**
  - Total records evaluated: 100
  - Unique records: 100 (100.0%)
  - Duplicate records: 0 (0.0%)
- **Synthetic Duplicate Test (5 raw records with intentional duplicates):**
  - Raw records: 5
  - Empty records dropped: 1
  - Duplicate records dropped: 1
  - Unique valid records retained: 2

---

## 8. Split Sizes, Preservation, and Leakage Checks

The `LeakageResistantSplitter` guarantees that related records never cross split boundaries, and enforces strict separation between official partitions and custom partitions:

### A. Official Partition Preservation (Default Mode)
- **Dataset:** `boolq` (Official `validation` split)
- **Input Records:** 100 records
- **Split Mode:** OFFICIAL (Preserved without silent repartitioning)
- **Partition:** `validation` (100 records, 100 unique groups)
- **Leakage Detected:** **NO (PASS)**
- **Storage Location:** `data/processed/boolq/validation.jsonl`
- **Manifest Split Type:** `"official"`

### B. Custom 70/15/15 Split Partition (Explicitly Requested)
- **Command:** `python -m trustrag.data.cli split-stats boolq --local-path data/processed/boolq/validation.jsonl --custom-split --output-dir data/processed/boolq/custom_splits --seed 42`
- **Total Records:** 100
- **Train partition (`custom_train.jsonl`):** 70 records (70.0%)
- **Validation partition (`custom_val.jsonl`):** 15 records (15.0%)
- **Test partition (`custom_test.jsonl`):** 15 records (15.0%)
- **Group Overlaps:**
  - Train ∩ Val: **0**
  - Train ∩ Test: **0**
  - Val ∩ Test: **0**
- **Content Hash Overlaps:**
  - Train ∩ Val: **0**
  - Train ∩ Test: **0**
  - Val ∩ Test: **0**
- **Leakage Detected:** **NO (PASS)**
- **Storage Location:** `data/processed/boolq/custom_splits/`
- **Manifest Split Type:** `"custom"`

### C. Grouped Security Variant Isolation:
- Clean and poisoned passages sharing a common `source_id` are grouped.
- Grouping ensures 100% of clean and poisoned variants remain strictly in the same split partition, preventing poison trigger leakage into evaluation sets.

---

## 9. Portable Manifest and Dataset Card Examples

### Official Split Manifest (`data/processed/boolq/manifest.json`):
```json
{
  "name": "boolq",
  "version": "1.0.0",
  "schema_version": "1.0.0",
  "preprocessing_version": "1.0.0",
  "source_identifier": "boolq",
  "source_url": "google/boolq",
  "source_revision": null,
  "license": "CC-BY-SA-3.0",
  "access_conditions": "open",
  "retrieval_date": "2026-11-07T19:16:37.684465+00:00",
  "config_name": "default",
  "split_type": "official",
  "splits_included": [
    "validation"
  ],
  "split_seed": 42,
  "split_sizes": {
    "validation": 100
  },
  "raw_records_count": 100,
  "processed_records_count": 100,
  "valid_records_count": 100,
  "invalid_records_count": 0,
  "duplicate_records_count": 0,
  "empty_records_count": 0,
  "record_type": "QueryRecord",
  "files": [
    {
      "split": "validation",
      "original_split": "validation",
      "processed_split": "validation",
      "split_type": "official",
      "file_path": "validation.jsonl",
      "format": "jsonl",
      "record_count": 100,
      "file_size_bytes": 93711,
      "sha256": "aaad91da64bb69f2ed70c0fb53ea43d5fb94b91effa717a3e02bddcb7168bc48"
    }
  ],
  "known_limitations": "Binary yes/no answers only",
  "intended_use": "Research evaluation and defense benchmarking",
  "usage_category": "TRAINING",
  "permitted_for_training": true,
  "permitted_for_evaluation": true,
  "metadata": {}
}
```

### Custom Split Manifest (`data/processed/boolq/custom_splits/manifest.json`):
```json
{
  "name": "boolq",
  "version": "1.0.0",
  "schema_version": "1.0.0",
  "preprocessing_version": "1.0.0",
  "source_identifier": "boolq",
  "source_url": "google/boolq",
  "source_revision": null,
  "license": "CC-BY-SA-3.0",
  "access_conditions": "open",
  "retrieval_date": "2026-11-07T19:16:56.039564+00:00",
  "config_name": "default",
  "split_type": "custom",
  "splits_included": [
    "train",
    "val",
    "test"
  ],
  "split_seed": 42,
  "split_sizes": {
    "train": 70,
    "val": 15,
    "test": 15
  },
  "raw_records_count": 100,
  "processed_records_count": 100,
  "valid_records_count": 100,
  "invalid_records_count": 0,
  "duplicate_records_count": 0,
  "empty_records_count": 0,
  "record_type": "QueryRecord",
  "files": [
    {
      "split": "custom_train",
      "original_split": "custom_train",
      "processed_split": "custom_train",
      "split_type": "custom",
      "file_path": "custom_train.jsonl",
      "format": "jsonl",
      "record_count": 70,
      "file_size_bytes": 66854,
      "sha256": "bfc1759cd62e87da4b9a72585377b28c7bafb77bce159272b5174e82b852375b"
    },
    {
      "split": "custom_val",
      "original_split": "custom_val",
      "processed_split": "custom_val",
      "split_type": "custom",
      "file_path": "custom_val.jsonl",
      "format": "jsonl",
      "record_count": 15,
      "file_size_bytes": 14559,
      "sha256": "1077922658522defd1a6ec67ac19ef36e776ed02a1f5eabf3beb0a732ea382fc"
    },
    {
      "split": "custom_test",
      "original_split": "custom_test",
      "processed_split": "custom_test",
      "split_type": "custom",
      "file_path": "custom_test.jsonl",
      "format": "jsonl",
      "record_count": 15,
      "file_size_bytes": 12298,
      "sha256": "b78ab07ac036e9d2405b7396894528b327173a6d2c1c1dd240421b131ccf11fc"
    }
  ],
  "known_limitations": "Binary yes/no answers only",
  "intended_use": "Research evaluation and defense benchmarking",
  "usage_category": "VALIDATION",
  "permitted_for_training": true,
  "permitted_for_evaluation": true,
  "metadata": {}
}
```

### Dataset Card Snippet (`data/processed/boolq/README.md`):
```markdown
# Dataset Card: boolq

## Summary
- **Dataset Name:** `boolq`
- **Schema Record Type:** `QueryRecord`
- **Source Identifier / URL:** google/boolq
- **License:** `CC-BY-SA-3.0`
- **Access Conditions:** `open`
- **Retrieval Date:** 2026-11-08T00:24:51.984534+00:00
- **Schema Version:** `1.0.0`
- **Preprocessing Version:** `1.0.0`

## Intended Use
- Research evaluation and defense benchmarking
- **Permitted for Training:** Yes
- **Permitted for Evaluation:** Yes

## Records and Split Statistics
- **Raw Records:** 100
- **Processed Records:** 100
- **Valid Records:** 100
- **Duplicate Records:** 0
- **Empty / Invalid Records:** 0
- **Split Seed:** 42

### Partition Sizes
- **validation:** 100 records

## Files and Checksums
| Split | Format | Records | Size (Bytes) | SHA-256 Checksum |
|---|---|---:|---:|---|
| validation | jsonl | 100 | 105655 | `aaad91da64bb69f2...` |
```

---

## 10. Exact Commands Executed and Exit Codes

| Step / Action | Exact Command | Exit Code | Result |
|---|---|:---:|---|
| List datasets | `$env:PYTHONPATH="src"; python -m trustrag.data.cli list` | 0 | Listed 13 datasets across 4 categories |
| Inspect metadata | `$env:PYTHONPATH="src"; python -m trustrag.data.cli inspect llm_aggrefact` | 0 | Displayed metadata, license (CC-BY-ND-4.0), and training prohibition |
| Inspect RSB | `$env:PYTHONPATH="src"; python -m trustrag.data.cli inspect rsb` | 0 | Displayed metadata, academic reference, and pending remote acquisition status |
| Preprocess smoke | `$env:PYTHONPATH="src"; python -m trustrag.data.cli preprocess boolq --split validation --smoke-test --output-dir data/processed/boolq` | 0 | Processed 100 records into `data/processed/boolq/validation.jsonl` |
| Validate records | `$env:PYTHONPATH="src"; python -m trustrag.data.cli validate data/processed/boolq/validation.jsonl --dataset boolq` | 0 | 100 records valid, 0 invalid, 0 empty, PASS |
| Split audit (official) | `$env:PYTHONPATH="src"; python -m trustrag.data.cli split-stats boolq --local-path data/processed/boolq/validation.jsonl` | 0 | Official split preserved without repartitioning; 0 leakage; PASS |
| Split audit (custom) | `$env:PYTHONPATH="src"; python -m trustrag.data.cli split-stats boolq --local-path data/processed/boolq/validation.jsonl --custom-split --output-dir data/processed/boolq/custom_splits --seed 42` | 0 | 70 train / 15 val / 15 test, 0 group overlap, 0 hash overlap, PASS |
| Generate & validate manifest | `$env:PYTHONPATH="src"; python -m trustrag.data.cli manifest boolq --dir data/processed/boolq --validate` | 0 | Generated relative POSIX `manifest.json`; Consistency Validation: PASS |
| Run unit tests | `$env:PYTHONPATH="src"; pytest -v` | 0 | **77 passed**, 2 deselected in 3.71s |
| Run integration tests | `$env:PYTHONPATH="src"; pytest -m integration -v` | 0 | **2 passed**, 77 deselected in 17.40s |

---

## 11. Unit and Integration Test Results

- **Unit Test Execution:**
  ```
  collected 79 items / 2 deselected / 77 selected

  tests\unit\data\test_acquisition_local.py ........                       [ 10%]
  tests\unit\data\test_audit_corrections.py ................               [ 31%]
  tests\unit\data\test_cli.py .....                                        [ 37%]
  tests\unit\data\test_loaders.py ...............                          [ 57%]
  tests\unit\data\test_manifest_storage.py ...                             [ 61%]
  tests\unit\data\test_preprocessing.py ......                             [ 68%]
  tests\unit\data\test_registry.py ...                                     [ 72%]
  tests\unit\data\test_schemas.py .....                                    [ 79%]
  tests\unit\data\test_splitting.py ....                                   [ 84%]
  tests\unit\data\test_validation.py ...                                   [ 88%]
  tests\unit\test_foundation.py .........                                  [100%]

  ====================== 77 passed, 2 deselected in 3.71s =======================
  ```

- **Integration Test Execution:**
  ```
  collected 79 items / 77 deselected / 2 selected

  tests\integration\test_data_acquisition.py ..                            [100%]

  ====================== 2 passed, 77 deselected in 17.40s ======================
  ```

---

## 12. Known Limitations and Blocked Items

1. **LLM-AggreFact Gated Access (BLOCKED for unauthenticated remote download):**
   - Repository `lytang/LLM-AggreFact` requires an explicit user agreement on Hugging Face.
   - License (CC-BY-ND-4.0) explicitly prohibits pretraining or fine-tuning models. It is permitted exclusively for evaluation.
   - Workaround: The system supports local import via `--local-path` once approved.
2. **RSB Benchmark Standalone Source (BLOCKED for direct remote acquisition):**
   - The paper *"Benchmarking Poisoning Attacks against Retrieval-Augmented Generation"* (arXiv:2505.18543) does not host a standalone public direct download URL.
   - Per research integrity guidelines, remote download is marked as pending verification, and a documented local import interface is provided.
3. **FineWeb Corpus Volume:**
   - The full FineWeb corpus comprises 15+ trillion tokens. Full downloads are strictly prevented by enforcing streaming and explicit sample limits.

---

## 13. Criterion-by-Criterion Acceptance Checklist

| # | Criterion | Result | Evidence / Notes |
|---|---|:---:|---|
| 1 | Inspect existing repo and Phase 00 code without rebuilding foundation | **PASS** | Fixed pyproject duplicate keys and Settings env var parsing; all 9 foundation tests pass. |
| 2 | Do not start Phase 02, detectors, guardrails, or model training | **PASS** | Scope strictly restricted to Phase 01 dataset engineering. |
| 3 | Acquire supported datasets from official sources | **PASS** | Hugging Face integration implemented and verified on BoolQ and SQuAD live. |
| 4 | Load local datasets (.json, .jsonl, .csv, .parquet) | **PASS** | `LocalFileImporter` tested across all 4 formats. |
| 5 | Normalize different schemas into common internal formats | **PASS** | 4 typed Pydantic record models implemented with hash validation. |
| 6 | Validate records and report malformed data | **PASS** | `RecordValidator` reports empty, invalid, and label errors. |
| 7 | Deduplicate records using stable content hashes | **PASS** | `DuplicateDetector` tracks exact SHA-256 content hashes. |
| 8 | Split data without leakage | **PASS** | `LeakageResistantSplitter` audits group and content hash overlap with 0 leakage. |
| 9 | Create and maintain dataset manifests and dataset cards | **PASS** | `ManifestManager` creates JSON manifests and Markdown cards with checksums. |
| 10 | Explicit sample limits and smoke-test mode (100 records) | **PASS** | Enforced via `--smoke-test` and `smoke_test_limit: 100` in configs. |
| 11 | Separate configurations for all 4 categories (13 datasets) | **PASS** | `configs/datasets.yaml` defines complete settings for all 13 datasets. |
| 12 | Verify licenses without fabricating URLs or claims | **PASS** | Licenses verified via web search; RSB marked pending; LLM-AggreFact restrictions recorded. |
| 13 | Provide explicit CLI commands | **PASS** | `trustrag.data.cli` implements `list`, `inspect`, `download`, `import`, `preprocess`, `validate`, `split-stats`, `manifest`. |
| 14 | Unit tests run offline without network access | **PASS** | 77 unit tests pass in 3.71s offline; integration tests isolated via marker. |
| 15 | Final report with exact commands, outputs, and exit codes | **PASS** | Documented in `reports/phase_01_report.md`. |

---
**Phase 01 Completion Verified.**

