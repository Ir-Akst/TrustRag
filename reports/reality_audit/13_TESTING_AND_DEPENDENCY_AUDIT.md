# 13 — Testing, Quality Tooling & Dependency Audit

**AST Audit (`50` test files):** `665` `def test_*` functions | `42/50` use `0` mocks | `8/50` use `monkeypatch`/`MagicMock`/`patch` (`41` total hits)
**Verdict:** `RED` (**Readiness: `35%`**)

---

## 1. Executed Test & Tooling Matrix

| Check Command | Environment | Exit Code | Exact Measured Outcome | Root Cause / Details |
| :--- | :--- | :---: | :--- | :--- |
| `pytest` (ignoring 8 serving/API files & `-m "not integration"`) | System Python `3.13.14` (`PYTHONPATH=src`) | `1` | **`644 passed, 3 failed, 2 deselected`** (`54.87 s`) | Failures: (1–2) `test_logger_json_output`, `test_logger_filters_secret` (`capfd` ordering + `get_logger` handler cache); (3) `test_srm_ablation_and_perf_smoke` (`ModuleNotFoundError: resource` in `suites.py:1843`) |
| `pytest tests/unit/test_foundation.py -vv` | System Python `3.13.14` | `0` | **`9/9 passed`** (`4.72 s`) | Proves the two logger failures are state-pollution / test-order coupling |
| `pytest tests/` (full discovery) | Workspace `.venv313` | `2` | **`35` collection errors** | Missing `scikit-learn` and `aiohttp` inside `.venv313` |
| Un-ignored serving/API test collection (`8` files) | System Python `3.13.14` | `2` | **Collection Blocked** | `tests/test_api_and_integration.py`, `test_srm_and_serving.py`, `test_phase_06`, `test_phase_08_step10`, `test_phase_09_api`, `test_phase_09_fullstack`, etc. fail importing `resource` (`service.py:7`) |
| `python tools/spec_validation/run_all_validations.py` | System Python `3.13.14` | `0` | **`13/13` gates PASS** (`warm_p50=19.222 ms`, `cold_init=22101.71 ms`) | Validated G3 linguistic/unit/consistency rules; wrote timestamp updates to `reports/evaluation/g3_linguistic_suite_*` |
| `node --test frontend/tests/dashboard.test.mjs` | Node.js | `0` | **`5/5 passed`** (`857 ms`) | Verified DOM helpers & fetch wiring |
| `ruff check src tests tools` | `.venv313` | `1` | **`24,503` output lines** of lint issues | Significant formatting/import/unused-symbol technical debt |
| `mypy src` | `.venv313` | `1` | **`43` type errors in `6` files** | Errors in `data/quality.py`, `data/benchmarks/builder.py`, `data/cli.py`, `serving/service.py`, `evaluation/suites.py`, etc. |

---

## 2. Redundancy & Dependency Hygiene Findings

1. **Test Suite Duplication:** Untracked root consolidated files (`tests/test_foundation_and_pipeline.py`, `test_g2_msd_and_adaptive.py`, `test_g3_verification.py`, `test_api_and_integration.py`, `test_srm_and_serving.py`) duplicate assertions already maintained in `tests/unit/test_phase_*.py` without consolidating out the older files.
2. **Logger Handler Caching Defect (`src/trustrag/utils/logging.py`):** `get_logger()` binds `StreamHandler(sys.stdout)` once globally without resetting stream targets when pytest `capfd` captures file descriptors across multiple tests, breaking logging assertions during full-suite execution.
3. **Requirements vs Code Mismatch:** `requirements.txt` omits `scikit-learn` and `aiohttp`; `pyproject.toml` lists `fastapi`/`uvicorn` for `[dependency-groups] api` while `src/trustrag/api/` uses `aiohttp`. `wheelhouse/` contains `65` wheels (`numpy`, `pydantic`, `pytest`, etc.) but lacks `scikit-learn`, `aiohttp`, `torch`, `transformers`, and `faiss-cpu`.

