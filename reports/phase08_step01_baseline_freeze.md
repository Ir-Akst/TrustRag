# Phase 08 — Step 01: Baseline Freeze & Architecture Review

**Freeze Date:** 2026-11-12  
**Branch:** `phase-8` (created cleanly from `phase-7 @ 1feb66fc4bf4ba557cac165387f8186f1fa6e1b8`)  
**Preserved Historical References:** `main` (`ed576a1`), `phase-4` (`3e2da49`), `phase-5` (`2873484`), `phase-6` (`cc1961e`), `phase-7` (`1feb66f`).

---

## 1. Immutable Environment & Dependency Baseline

| Property | Verified State |
| --- | --- |
| **Git Commit (`HEAD`)** | `1feb66fc4bf4ba557cac165387f8186f1fa6e1b8` |
| **Python Runtime** | `Python 3.14.9` (`/home/aditya/rags/.venv/bin/python`) |
| **Hardware & OS** | Linux `x86_64`, 12 CPU cores, CPU-only (`16029896 kB` MemTotal, ~`3.8 GB` MemAvailable), offline sandbox |
| **Random Seed** | `42` (`configs/base.yaml: app.random_seed`) |
| **Core Installed Dependencies** | `numpy==2.5.4`, `scipy==1.18.1`, `scikit-learn==1.9.1`, `pandas==3.1.1`, `pydantic==2.14.3`, `pydantic-settings==2.16.2`, `httpx==0.28.1`, `requests==2.34.2`, `PyYAML==6.0.3`, `datasets==5.1.0`, `tenacity==9.2.1` |
| **Unavailable Optional DL / Local LLM** | `torch`, `transformers`, `sentence-transformers`, `peft`, `trl`, `faiss`, `xgboost` **NOT INSTALLED**; `/usr/local/bin/ollama` daemon stopped (`could not connect to ollama server`) |

---

## 2. Baseline Verification & Artifact Checksums

| Check / Artifact | Result / SHA-256 |
| --- | --- |
| `pytest -W error -q` | **`341 passed, 2 deselected`** (`9.35s`; `tests/integration/test_data_acquisition.py` deselected via `pyproject.toml`) |
| `mypy` (core + serving + Phase 07 scope) | **`33 / 33` source files passed** (`35` legacy errors persist in `data/` & `evaluation/suites.py`) |
| `ruff` (Phase 05/06/07 audited scope) | **`0` errors** (`358` legacy warnings remain in Phase 03/04 source files) |
| `tools/spec_validation/run_all_validations.py` | **`PASS` (`10 / 10` validators, `13 / 13` gates)** (`warm p50 = 5.004 ms`) |
| `configs/base.yaml` | `2631ac3b7389fbc91d8b999091760a332d38d5bac331077e9221fe6ee5c4a6cc` |
| `configs/adaptive/platt_calibrator_v1.json` | `57b02fd300dc278e94250de78505ebb426b4ac5e698443114615e7ab13948c9e` |
| `reports/evaluation/phase07_step04_benchmarks.json` | `330760da9e7034b03fd39e4504fa6d945f95fe853480e2e132a0edd53df55504` |
| `reports/evaluation/phase07_step05_msd_ablation.json` | `d1e5929123ab40e1b511b6611bb5e441322e0ce1e490f6c6b4f6f1907a0835df` |
| `reports/evaluation/phase07_step06_generalization.json` | `c92a4c17e24b399924e846557c3c334b0430c21574eabe724d939439b63104ad` |

---

## 3. Phase 07 Architecture Review & Known Baseline Limitations

| Subsystem | Inspected Status at Freeze (`1feb66f`) | Known Limitations Entering Phase 08 |
| --- | --- | --- |
| **G1 Input Guardrail** (`src/trustrag/guardrails/input_guardrail.py`) | Canonicalizes (`NFKC`), flags obfuscation, regex threat payloads, flood, and meta-patterns (`ALLOW`/`FLAG`/`BLOCK`). | **No controlled query paraphrasing (`q'`)**; no semantic-drift/constraint preservation validator. |
| **G2 Multi-Signal Detector & Calibration** (`src/trustrag/detection/`, `src/trustrag/adaptive/calibration.py`) | Active-4 MSD reaches `ROC-AUC = 0.8315`, `F1 = 0.6512`, `FPR = 0.0000` on `n=64`; misses `15/29` (`51.7%` FNR) factual substitutions (`ASR = 0.4286`). | `F1_perplexity` `disabled`; `F2_embedding_norm` inactive by default (`TF-IDF` norms hurt AUC `-0.0276`); `F6` constant `0.75`; `platt-mixed-v1` adds `FPR` (`0.0 -> 0.1714` raw / `0.2571` adaptive). |
| **Adaptation Policy & Controller** (`src/trustrag/adaptive/{policy_engine,controller}.py`) | Phase 07 fixed cap clamping (`<= 0.5`), removed-doc reporting, pre-indexed candidate caching, and policy-engine initialization. | Full pre-ret uncalibrated MSD + adapted MSD still incurs `+48.36 ms` on BoolQ `N=100`; no cluster trust ranking. |
| **G3 Verifier & Generalization** (`src/trustrag/verification/{output_verifier,generalization}.py`) | Phase 07 added active role-swap guard, upper-bound polarity handling, and intra-doc antonym conflict downgrade (`6/13` strict probes). | Heuristic TF-IDF/regex verifier lacks model-backed entailment, query-consistency verification, `re-answer` from high-trust `Ê`, multi-doc claim aggregation, `3+` hop reasoning, and affine units (`C/F`). |
| **SRM Integration** (`src/trustrag/srm/{client,backends}.py`) | HTTP stubs (`local_ollama`, `openai_compatible`) + `DeterministicFallbackBackend`. | Silent `DISABLED`/fallback routing; no pluggable lifecycle (`init/health/shutdown`), no `5`-class HalluGuard judgment mapping (`GROUNDED`/`INTRINSIC_HALLUCINATION`/`EXTRINSIC_HALLUCINATION`/`INSUFFICIENT_EVIDENCE`/`CONTRADICTED`), no `<think>` parser, no live weights/GPU offline. |
| **Serving Layer** (`src/trustrag/serving/service.py`) | Single-process thread-safe (`threading.RLock`) `TrustRAGService`. | Lacks per-request timeout guard, structured health detail on SRM backend/memory, graceful shutdown lifecycle, and bounded concurrency testing. |
| **Datasets & Benchmarks** (`data/benchmarks*`, `data/raw/`, `src/trustrag/data/`) | Verified `n=64` backup security pool & `n=15` BoolQ test; external corpora absent (`RSB`, `HaluEval-QA`, `NQ`, `HotpotQA`, `MS-MARCO`, `LLM-AggreFact`, full `RAGTruth` = `BLOCKED`). | `data/benchmarks/` shrunk with `33.3%` duplicates (`adv`), `benchmarks_backup` has query leakage across splits, and live SLM FilterRAG remains `BLOCKED`. |
