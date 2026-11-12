# TrustRAG Phase 10 — Baseline Freeze & Environment Manifest

**Branch:** `phase-10`  
**Branched From:** `phase-9` @ `1ceb29c6c428d27a325f8d2bf750e0a6da6d75bb`  
**Historical Lineage:** `phase-9` (`1ceb29c`) -> `phase-8` (`9d01f19`) -> `phase-7` (`1feb66f`) -> `phase-6` (`cc1961e`) -> `phase-5` (`2873484`) -> `phase-4` (`3e2da49`) -> `main` (`ed576a1`)  
**Timestamp:** 2026-11-12T12:53:45+05:30

---

## 1. Git Isolation Verification
- Uncommitted `+1` trailing-newline working-tree edits on `phase-9` were restored (`git restore .`) without modifying any historical commits.
- Created isolated branch `phase-10` from `1ceb29c`.
- Historical branches (`main`, `phase-4`..`phase-9`) remain untouched and unpushed unless explicitly authorized.

---

## 2. Hardware & Software Environment
- **OS / Architecture:** Linux x86_64, CPU-only offline environment
- **CPU Cores:** 12
- **Memory:** 15 GiB RAM (6.0 GiB available at freeze)
- **Disk Free:** 47.35 GiB
- **Python:** 3.14.9 (`/home/aditya/rags/.venv/bin/python`)
- **Installed Core Packages:**
  - `numpy==2.5.4`
  - `scipy==1.18.1`
  - `scikit-learn==1.9.1`
  - `datasets==5.1.0`
  - `pydantic==2.14.3`
  - `aiohttp==3.14.5`
  - `pytest==9.2.0`
- **Unavailable Optional ML Dependencies:**
  - `torch`: NOT INSTALLED
  - `transformers`: NOT INSTALLED
  - `peft`: NOT INSTALLED
  - `trl`: NOT INSTALLED
- **Random Seed:** `42`

---

## 3. Frozen Phase 09 Baseline Verification
Verified prior to Phase 10 implementation:
- `pytest -W error -q`: **377 passed, 2 deselected** in 12.36s
- `mypy src/trustrag/api tests/unit/test_phase_09_*.py`: **Success: no issues found in 10 source files**
- `ruff check src/trustrag/api tests/unit/test_phase_09_*.py`: **All checks passed!**
- `python -m compileall -q src tests tools`: **Passed (exit 0)**
- `cd frontend && npm test`: **5 passed, 0 failed** (47.76ms)
- `python tools/spec_validation/run_all_validations.py`: **PASS** (10/10 validators, 13/13 gates)

---

## 4. Existing Evaluation & Dataset Baseline
- **Registered Dataset Adapters (`src/trustrag/data/registry.py`):** 13 adapters (`natural_questions`, `hotpotqa`, `ms_marco`, `squad`, `boolq`, `halueval`, `ragtruth`, `llm_aggrefact`, `wice`, `expertqa`, `rsb`, `custom_security`, `fineweb`).
- **Existing Evaluation Modules (`src/trustrag/evaluation/`):** `loader.py`, `metrics.py`, `runner.py`, `schemas.py`, `suites.py`, `external_benchmarks.py`, `filterrag_experiment.py`.
- **Available Local Data Files:**
  - `data/benchmarks_backup/{adversarial_robustness,clean_rag,hallucination,knowledge_poisoning}/{train,val,test}.jsonl`
  - `data/processed/boolq/custom_splits/custom_{train,val,test}.jsonl` (100 records)
  - `data/raw/ragtruth/test.jsonl` (6 smoke records), `data/raw/wice/test.jsonl` (4 smoke records), `data/raw/expertqa/test.jsonl` (4 smoke records)
- **Known Blocked External Corpora at Freeze:** `llm_aggrefact`, `rsb`, `halueval`, `natural_questions`, `hotpotqa`, `ms_marco`, and full `ragtruth` (`~18,000` records).
