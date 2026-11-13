# 01 — Repository Discovery & Packaging Reality Audit

**Git Head:** `713c54e2065b4cd37f63b2fb8c9a8bf3694ed831` (`main`)
**Host OS:** `Windows-11-10.0.26200-SP0`
**Runtimes Inspected:** System Python `3.13.14`, Workspace `.venv313`, Node.js test runner (`node --test`)

---

## 1. Repository Layout & Untracked State

`trustrag` uses a standard `src/trustrag/` package layout accompanied by `configs/`, `data/`, `docs/`, `frontend/`, `reports/`, `tests/`, `tools/`, and a local offline `wheelhouse/` (`65` basic wheels). At audit start, `git status --short` showed pre-existing untracked consolidation artifacts alongside tracked phase deliverables:

- `configs/benchmark_reference.json` (untracked)
- `docs/security.md` (untracked)
- `reports/dataset_coverage_audit/` (untracked prior dataset audit)
- `src/trustrag/engine/taxonomy.py` (untracked)
- `tests/test_*.py` (`5` consolidated test files duplicating unit tests in `tests/unit/`, untracked)

> [!NOTE]
> Running `tools/spec_validation/run_all_validations.py` during verification updated timestamps inside three tracked files under `reports/evaluation/g3_linguistic_suite_g3_linguistic_suite_eval_ed2dae3f96*` (no `src/`, `configs/`, `tests/`, or `data/` files were modified by this audit).

---

## 2. Source Code Inventory (`src/trustrag/`)

| Package | Key Modules | Functional Role |
| :--- | :--- | :--- |
| `engine/` | `text_utils.py`, `taxonomy.py` | Shared regex injection patterns, obfuscation/Unicode checks, claim/hallucination taxonomy |
| `guardrails/` | `input_guardrail.py`, `paraphraser.py` | G1 prompt injection, Unicode/confusable normalization, rule-based query paraphrasing & drift validator |
| `retrieval/` | `retriever.py` | Ephemeral in-memory `TfidfVectorizer` + lexical overlap + G2 filtering with `floor(K/2)` cap |
| `detection/` | `msd.py` | G2 Multi-Signal Detector (6 defined signals `F1`–`F6`; calibrated threshold & coverage fusion) |
| `generation/` | `generator.py` | Extractive sentence selector + caller-supplied `llm_callable` wrapper with abstention |
| `verification/` | `output_verifier.py`, `query_consistency.py`, `generalization.py` | G3 heuristic claim extraction, negation/number/temporal/unit checks, query consistency |
| `srm/` | `client.py`, `backends.py`, `hf_local.py`, `registry.py` | SRM interface (`DeterministicFallbackBackend`, `hf_local`, `local_ollama`, `openai_compatible`) |
| `pipeline/` | `trustrag_pipeline.py`, `cli.py` | Main `TrustRAGPipeline` orchestrator + CLI entry point |
| `adaptive/` | `calibration.py`, `thresholding.py`, `drift.py`, `feedback.py`, `policy_engine.py`, `controller.py` | Platt/Temperature JSON calibrators, PSI/KS drift, non-circular G3 feedback, bounded policy updates |
| `serving/` | `service.py` | Production wrapper with latency budgets & Unix `resource.RLIMIT_*` limits (**fails import on Windows**) |
| `api/` | `app.py`, `server.py`, `schemas.py`, `audit.py`, `config_manager.py`, `monitoring.py`, `security.py` | `aiohttp` REST server, token-bucket rate limit, CSP headers, audit JSONL logger |
| `data/` | `registry.py`, `cli.py`, `quality.py`, `splitting.py`, `benchmarks/*`, `loaders/*` | Dataset schemas, 13 adapters, synthetic security generator (`security_generator.py`), benchmark builder |
| `evaluation/` | `runner.py`, `suites.py`, `metrics_extended.py`, `external_benchmarks.py`, `filterrag_experiment.py` | Phase 10 evaluation runner, Wilson/McNemar/Holm stats, FilterRAG proxies |
| `config/` | `engine_config.py`, `dataset_config.py`, `settings.py` | YAML/env/JSON configuration loaders |
| `utils/` | `logging.py`, `repro.py` | Structured JSON logger (`get_logger` with secret redaction) and determinism seeds |

Zero `TODO` or `FIXME` markers were found across `src/` and `configs/` (`0` hits).

---

## 3. Configuration & Packaging Mismatches

Direct comparison of [pyproject.toml](file:///c:/Users/Dell/Desktop/trustrag/pyproject.toml), `requirements*.txt`, and `.venv313` exposed three operational mismatches:

1. **Web Framework Drift (`fastapi`/`uvicorn` vs `aiohttp`):** `pyproject.toml` defines `[dependency-groups] api = ["fastapi>=0.110", "uvicorn[standard]>=0.27"]`, whereas [app.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/api/app.py) and [server.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/api/server.py) implement the HTTP server entirely in **`aiohttp`**, which is absent from both `requirements.txt` and `pyproject.toml`.
2. **Core Requirements Omission:** `requirements.txt` omits `scikit-learn` (hard runtime requirement for `TfidfVectorizer` in `retriever.py`, `msd.py`, `output_verifier.py`) and `aiohttp`. As a result, the local `.venv313` environment fails `35` pytest test collections with missing-module errors.
3. **Incomplete Offline Wheelhouse:** `wheelhouse/` (`65` wheels) contains basic utilities (`numpy`, `pydantic`, `pytest`, `ruff`, `mypy`, `aiohttp`? Wait: verified `.venv313` lacks `sklearn`, `aiohttp`, `torch`, `transformers`, `faiss-cpu`), lacking `scikit-learn`, `aiohttp`, `torch`, `transformers`, and `faiss-cpu`.
4. **POSIX Assumption on Windows (`RED`):** Unconditional `import resource` at [service.py:7](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/serving/service.py#L7) and [suites.py:1843](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/evaluation/suites.py#L1843) crashes on Windows 11 before any route, CLI `--health`, `--adaptive`, or perf-smoke code can execute. By contrast, [audit.py:21](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/api/audit.py#L21) checks `fcntl` availability and gracefully falls back on Windows with a warning that multi-process file locking is disabled.
5. **Runtime Overhead Note:** `tools/spec_validation/run_all_validations.py` recorded `cold_import_init_ms = 22101.71 ms` (`~22.1 s` cold Python module/sklearn load vs `19.222 ms` warm p50).

