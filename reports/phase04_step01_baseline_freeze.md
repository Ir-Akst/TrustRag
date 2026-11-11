# TrustRAG Phase 04 — Step 1: Inspection and Baseline Freeze Report

**Date:** 2026-11-11  
**Repository:** `/home/aditya/rags/TrustRag` (mirrored from `Ir-Akst/TrustRag`, commit `ed576a1`)  
**Scope:** Phase 04 Step 1 Only (Repository Inspection, Dataset Integrity Audit, Configuration Snapshot, Baseline Regression Verification)

---

## 1. Environment & Runtime Snapshot

| Property | Observed Value |
|---|---|
| **OS / Platform** | `Linux-7.2.14-arch1-1-x86_64-with-glibc2.44` (12 CPUs) |
| **Python Interpreter** | `3.14.9` (`/home/aditya/rags/.venv/bin/python`) |
| **Package Version** | `trustrag 0.1.0` (editable install) |
| **Core Runtime Libraries** | `pydantic 2.14.3`, `pydantic-core 2.50.4`, `pydantic-settings 2.16.2`, `numpy 2.5.4`, `pandas 3.1.1`, `scipy 1.18.1`, `scikit-learn 1.9.1`, `pyarrow 26.0.1`, `httpx 0.28.1`, `requests 2.34.2`, `tenacity 9.2.1`, `PyYAML 6.0.3` |
| **Test & QA Tooling** | `pytest 9.2.0`, `pytest-cov 7.1.0`, `pytest-mock 3.17.0`, `ruff 0.17.4`, `mypy 2.4.1` |
| **Optional Heavy ML / Tracking** | `torch`, `transformers`, `sentence-transformers`, `mlflow` are **not installed** in `.venv`; evaluation uses the verified core TF-IDF/heuristic/deterministic runtime unless configured otherwise. |

---

## 2. Baseline Configuration Freeze (`configs/base.yaml` & `configs/datasets.yaml`)

All defense components load cleanly via `trustrag.config.settings.load_config()` (`Settings`).

### 2.1 Application & Reproducibility
- `app.env`: `development`
- `app.log_level`: `INFO`
- `app.random_seed`: `42` (enforced via `trustrag.utils.repro.set_random_seed`)

### 2.2 G1 Input Guardrail (`GuardrailsConfig`)
- `enabled`: `true`
- `max_input_length`: `4096`
- `flag_threshold`: `0.35`
- `block_threshold`: `0.70`
- `block_on_empty`: `true`
- `strip_zero_width_for_analysis`: `true`

### 2.3 Retrieval & Removal Cap (`RetrievalConfig`)
- `top_k`: `5`
- `candidate_multiplier`: `3`
- `min_relevance_score`: `0.01`
- `filtering_mode`: `remove_with_cap`
- `filter_low_trust`: `true`
- `enforce_removal_cap`: `true`
- `removal_cap_ratio`: `0.5` ($\text{removals} \le \lfloor K / 2 \rfloor$, where $K = \min(\text{top\_k}, |\text{candidates}|)$)
- `trust_weight`: `0.45`

### 2.4 G2 Multi-Signal Detector (`MSDConfig`)
- `enabled`: `true`
- **Signal Weights:** `weight_perplexity=0.8` (F1), `weight_embedding_norm=0.8` (F2), `weight_query_match=1.2` (F3), `weight_instruction_content=2.0` (F4), `weight_consensus_deviation=1.0` (F5), `weight_provenance=0.8` (F6), `bias=0.0`
- **Thresholds:** `trust_threshold=0.60`, `poison_threshold=0.38`, `instruction_poison_threshold=0.55`, `instruction_flag_threshold=0.30`
- **Missing Signal Policy:** `coverage_attenuated` (`min_available_signals=2`, `min_available_weight_ratio=0.25`)
- **Signal Backends:** `perplexity_backend=disabled` (F1 unavailable by default; `perplexity_reference_mean=25.0`, `std=15.0`, `z_threshold=2.0`), `embedding_backend=tfidf_raw`, `embedding_norm_reference_policy=require_configured` (F2 unavailable unless reference stats configured), `provenance_priors={}`, `enable_freq_density=false`

### 2.5 Generation, G3 Verification, and SRM (`GenerationConfig`, `VerificationConfig`, `SRMConfig`)
- **Generation:** `mode=extractive`, `max_context_docs=3`, `max_sentences_per_doc=2`, `abstain_on_empty_context=true`
- **G3 Output Verification:** `enabled=true`, `min_support_coverage=0.65`, `min_relevance_for_check=0.10`, `strict_numeric_matching=true`, `strict_negation_check=true`
- **SRM:** `enabled=true`, `backend=disabled`, `model_name=halluguard-srm-fallback`, `timeout_seconds=5.0`, `temperature=0.0`, `fallback_on_error=true`

---

## 3. Component & Evaluation Infrastructure Inventory

### 3.1 Existing Core Defense Interfaces
- **G1:** `InputGuardrail.evaluate(user_input: str) -> G1Assessment` (`src/trustrag/guardrails/input_guardrail.py`)
- **G2:** `MultiSignalDetector.assess_candidates(query, candidates, relevance_scores, ...) -> List[G2DocumentAssessment]` (`src/trustrag/detection/msd.py`, signals in `src/trustrag/detection/signals.py`)
- **Retrieval:** `TrustAwareRetriever.retrieve_trusted(query, top_k=...) -> RetrievalResult` (`src/trustrag/retrieval/retriever.py`)
- **Generation:** `AnswerGenerator.generate(query, trusted_documents, *, answer_override=None) -> GeneratedAnswer` (`src/trustrag/generation/generator.py`)
- **G3:** `OutputEvidenceVerifier.verify(answer_text, evidence_docs, *, abstained=False) -> G3VerificationReport` (`src/trustrag/verification/output_verifier.py`)
- **SRM:** `SRMClient.reason(request: SRMRequest) -> SRMResponse` (`src/trustrag/srm/client.py`, backends in `src/trustrag/srm/backends.py`)
- **Integrated Pipeline:** `TrustRAGPipeline.run(query, *, top_k=None, answer_override=None) -> PipelineResponse` (`src/trustrag/pipeline/trustrag_pipeline.py`) & CLI (`src/trustrag/pipeline/cli.py`)

### 3.2 Existing Logging, QA, and Validation Modules
- **Structured Logging:** `src/trustrag/utils/logging.py` (`JsonFormatter`, `SecretFilter`).
- **Dataset QA & Validation:** `DatasetQualityAuditor` (`src/trustrag/data/quality.py`), `RecordValidator` (`src/trustrag/data/validation.py`), `ManifestManager` (`src/trustrag/data/manifest.py`), `LeakageResistantSplitter` (`src/trustrag/data/splitting.py`).
- **Specification Validation:** `tools/spec_validation/run_all_validations.py` (10 validators, 13 gates; targets Phase 03 G3 spec conformance).
- **Gap Identified for Step 2:** There is currently **no `src/trustrag/evaluation/` package** or unified Phase 04 benchmark runner for empirical ASR/precision/recall/F1/ROC-AUC/latency/statistical CI evaluation.

---

## 4. Dataset & Benchmark Integrity Audit

### 4.1 Active Benchmarks (`data/benchmarks/`)
| Benchmark | Split | Records | Unique `source_id` | Sources | Labels / Attack Families | LF SHA-256 (first 16) | CRLF Manifest Match |
|---|---|---:|---:|---|---|---|---|
| `clean_rag` | `train` | 7 | 7 | `boolq` (7) | `QueryRecord` (no attack labels) | `75887ae3ae1a37b6` | **TRUE** |
| `clean_rag` | `val` | 1 | 1 | `boolq` (1) | `QueryRecord` | `466c9cc7881245b9` | **TRUE** |
| `clean_rag` | `test` | 2 | 2 | `boolq` (2) | `QueryRecord` | `ee55d8b39c4c7867` | **TRUE** |
| `knowledge_poisoning` | `train` | 14 | 7 | `custom_security` (14, synth) | `clean`: 7, `poisoned`: 7 (`CONFLICTING_EVIDENCE`: 4, `PROMPT_INJECTION`: 2, `TRIGGER_DOS`: 2, `BENIGN_INSTRUCTION_LIKE`: 2, `KNOWLEDGE_POISONING`: 4) | `df33307938751458` | **TRUE** |
| `knowledge_poisoning` | `val` | 2 | 1 | `custom_security` (2, synth) | `clean`: 1, `poisoned`: 1 (`MALICIOUS_INSTRUCTION`: 2) | `38da80990951cd2b` | **TRUE** |
| `knowledge_poisoning` | `test` | 4 | 2 | `custom_security` (4, synth) | `clean`: 2, `poisoned`: 2 (`KNOWLEDGE_POISONING`: 4) | `b1dcfd265c8a905e` | **TRUE** |
| `hallucination` | `train` | 7 | 7 | `ragtruth` (4), `wice` (2), `expertqa` (1) | `CONTRADICTED`: 3, `SUPPORTED`: 3, `NOT_ENOUGH_EVIDENCE`: 1 | `e891c4b0a39fc061` | **TRUE** |
| `hallucination` | `val` | 1 | 1 | `ragtruth` (1) | `SUPPORTED`: 1 | `6a2574388eb7d1cb` | **TRUE** |
| `hallucination` | `test` | 3 | 3 | `wice` (1), `expertqa` (2) | `NOT_ENOUGH_EVIDENCE`: 1, `SUPPORTED`: 1, `CONTRADICTED`: 1 | `dd23492b3f1b27c5` | **TRUE** |
| `adversarial_robustness` | `train` | 22 | 7 | `custom_security` (22, synth) | `clean`: 11, `poisoned`: 11 (10 within-split duplicates; 14 unique `record_id`s) | `c828a980d7d08ee1` | **TRUE** |
| `adversarial_robustness` | `val` | 4 | 1 | `custom_security` (4, synth) | `clean`: 2, `poisoned`: 2 (`MALICIOUS_INSTRUCTION`: 4; 2 unique `record_id`s) | `503a628db615b9ef` | **TRUE** |
| `adversarial_robustness` | `test` | 4 | 2 | `custom_security` (4, synth) | `clean`: 2, `poisoned`: 2 (`KNOWLEDGE_POISONING`: 4; 4 unique `record_id`s) | `b1dcfd265c8a905e` | **TRUE** |

### 4.2 Preserved Larger Phase 02 Snapshot (`data/benchmarks_backup/`) & Raw/Processed Sources
- `data/benchmarks_backup/clean_rag`: **100 records** (`train=70`, `val=15`, `test=15`, `boolq`, 0 duplicates, CRLF manifest match **TRUE**).
- `data/benchmarks_backup/knowledge_poisoning`: **150 records** (`train=104`, `val=22`, `test=24`, synthetic `custom_security`, `KNOWLEDGE_POISONING` + `TRIGGER_DOS`, 0 duplicates, CRLF manifest match **TRUE**).
- `data/benchmarks_backup/adversarial_robustness`: **250 records** (`train=174`, `val=36`, `test=40`, synthetic `custom_security`, `PROMPT_INJECTION`, `MALICIOUS_INSTRUCTION`, `CONFLICTING_EVIDENCE`, `BENIGN_INSTRUCTION_LIKE`, 0 duplicates, CRLF manifest match **TRUE**).
- `data/benchmarks_backup/hallucination`: **11 records** (`train=7`, `val=1`, `test=3`, identical to `data/benchmarks/hallucination`).
- `data/raw/custom_security/raw_train.jsonl`: **2,000 synthetic paired records** (1,000 clean/poison pairs across all 6 attack families).
- `data/processed/boolq/validation.jsonl`: **100 real BoolQ records** (`train=70`, `val=15`, `test=15` in `custom_splits/`, CRLF manifest match **TRUE**).

### 4.3 Integrity & Leakage Verification Findings
1. **Cross-Split Leakage:** **0 `source_id` overlaps** and **0 `content_hash` overlaps** across `train`/`val`/`test` in all 4 benchmarks (verified in both `data/benchmarks/` and `data/benchmarks_backup/`).
2. **Schema & Label Quality (`DatasetQualityAuditor`):** `invalid_records=0`, `empty_records=0`, `unknown_labels=0` across all 4 benchmarks (`is_healthy=True`).
3. **Important Baseline Observations (No Undocumented Modifications Made):**
   - **Finding 1 (CRLF vs LF Manifest Checksums):** `ManifestManager.validate_manifest()` reports `valid=False` under Linux LF line endings because the files were originally generated on Windows (`\r\n` bytes hashed in `manifest.json`) and normalized to `\n` upon Git checkout (`size_diff == line_count`). Normalizing `\n` back to `\r\n` confirms **100% SHA-256 checksum identity** across all 28 files in `data/benchmarks/`, `data/benchmarks_backup/`, and `data/processed/boolq/`.
   - **Finding 2 (Active `data/benchmarks/` Truncation from `scratch/run_phase02_full.py`):** On `2026-11-08T16:59:23Z`, `scratch/run_phase02_full.py` backed up the 100/150/250-record Phase 02 benchmarks to `data/benchmarks_backup/` and rebuilt `data/benchmarks/` with `limit=10`. As a result, active `data/benchmarks/` has very small splits (`val=1–4`, `test=2–4`), `adversarial_robustness` contains 10 within-split duplicate records, and its `val`/`test` splits contain only 1 attack family each. We keep `data/benchmarks/` strictly untouched for Step 1; in subsequent evaluation steps, we will report exact results on `data/benchmarks/` and document clearly where `data/benchmarks_backup/` (or `data/raw/custom_security`) is used for statistical power and full attack-family coverage.
   - **Finding 3 (Test Split Isolation):** Test splits were inspected solely for integrity counts/hashes and were **not** used for any tuning or threshold selection.

---

## 5. Baseline Verification & Regression Execution

| Check | Exact Command | Exit Code | Result Summary |
|---|---|---:|---|
| **Unit Regression Suite** | `PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest` | `0` | **303 passed, 2 deselected** (`integration`) in `2.27s` |
| **Bytecode Compilation** | `/home/aditya/rags/.venv/bin/python -m compileall -q src tests` | `0` | `COMPILEALL_OK` |
| **Spec Validation Harness** | `PYTHONPATH=src /home/aditya/rags/.venv/bin/python tools/spec_validation/run_all_validations.py` | `0` | `suite_status: PASS`, **10/10 validators**, **13/13 gates SATISFIED** |
| **Lint Check (Baseline)** | `/home/aditya/rags/.venv/bin/ruff check src --statistics` | `1` | 1,105 pre-existing lint warnings/errors (mostly `UP006`/`UP045`/`UP035` typing style) |
| **Type Check (Baseline)** | `PYTHONPATH=src /home/aditya/rags/.venv/bin/mypy src/trustrag/ --ignore-missing-imports` | `1` (ran standalone, 18 errors) | 18 pre-existing type errors across 11 Phase 00–03 files (recorded as baseline; not introduced by Phase 04) |

---

## 6. Step 1 Acceptance Verdict

- [x] **Baseline configuration recorded** (`configs/base.yaml`, `configs/datasets.yaml`, `Settings`).
- [x] **Dataset integrity verified** (0 cross-split leakage, 100% CRLF SHA-256 match, 0 invalid/unknown-label records; `data/benchmarks/` vs `data/benchmarks_backup/` state documented transparently).
- [x] **Existing tests executed** (303/303 unit tests passing, `compileall` clean, 13/13 spec gates passing).
- [x] **Existing implementation preserved** (zero source or dataset modifications performed).
- [x] **No undocumented dataset modifications**.

**Step 1 Status:** **PASS** — Ready to proceed to Step 2 (Evaluation Infrastructure).

