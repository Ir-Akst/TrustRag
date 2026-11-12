# TrustRAG Phase 11 — Step 6 Regression & Deselected-Test Audit

## 1. Test Selection & Deselected Tests (`pytest -W error -q`)
- **Command:** `/home/aditya/rags/.venv/bin/pytest -W error -q` -> `396 passed, 2 deselected` (`15.78s`).
- **Deselection Mechanism (`pyproject.toml:37-40`):** `addopts = "-m 'not integration'"`.
- **Exact 2 Deselected Tests:**
  1. `tests/integration/test_data_acquisition.py::test_boolq_sample_acquisition`
  2. `tests/integration/test_data_acquisition.py::test_squad_sample_acquisition`
- **Assessment:** Both are `@pytest.mark.integration` online Hugging Face Hub download tests (`google/boolq`, `rajpurkar/squad`). Explicit `pytest -W error -v -m integration` execution confirmed `2 failed` (`AcquisitionError` due to offline DNS/network isolation), so their deselection in `pyproject.toml` is justified and both are recorded as **`BLOCKED`** (never `PASS`).

## 2. Full Verification Matrix
- `pytest -W error -q`: **`396 passed, 2 deselected`**
- `cd frontend && npm test`: **`5 passed, 0 failed`**
- `python -m compileall -q src tests`: **Exit `0`**
- `python tools/spec_validation/run_all_validations.py`: **`PASS`** (`10/10` validators, `13/13` gates)
- `ruff check` on Step 5 test: **`0` errors**; repo-wide: `1348` legacy findings
- `mypy` on Step 5 files: `27` pre-existing errors in `data/quality.py` & `data/benchmarks/builder.py`; **`0` errors** in changed files.
