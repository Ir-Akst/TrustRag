# TrustRAG Phase 11 — Step 5 Full Regression Report

| Check | Step 4 Baseline | Step 5 Post-Fix | Status |
| :--- | :--- | :--- | :---: |
| **Complete Pytest (`pytest -W error -q`)** | `392 passed, 2 failed, 2 deselected` | **`396 passed, 2 deselected`** (`15.78s`) | **PASS** |
| **Frontend (`cd frontend && npm test`)** | `5 passed, 0 failed` | **`5 passed, 0 failed`** (`48.26ms`) | **PASS** |
| **Spec Validators (`run_all_validations.py`)** | `10/10` validators, `13/13` gates | **`10/10` validators, `13/13` gates** | **PASS** |
| **Python Compilation (`compileall`)** | Exit `0` | **Exit `0`** | **PASS** |
| **Ruff (`tests/unit/test_phase_11_step5_remediation.py`)** | `—` | **All checks passed (`0` errors)** | **PASS** |
| **Ruff (repo-wide `src tests tools`)** | `1348` findings | `1348` findings (`0` new findings added) | **LEGACY ONLY** |
| **Mypy (`paraphraser`, `text_utils`, `output_verifier`, `step5` test)** | `27` pre-existing in `data/quality.py` & `data/benchmarks/builder.py` | `27` pre-existing (`0` in changed files) | **LEGACY ONLY** |

