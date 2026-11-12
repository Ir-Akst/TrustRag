# TrustRAG Phase 11 — Full Regression Report

**Worktree:** `/home/aditya/rags/TrustRag-phase11` | **Branch:** `phase-11`

| Check | Phase 11 Baseline | Phase 11 Post-Remediation | Status |
| :--- | :--- | :--- | :---: |
| **Full Python Suite (`pytest -W error -q`)** | `382 passed, 2 deselected` | **`388 passed, 2 deselected`** | **PASS** |
| **Phase 11 Remediation Suite (`test_phase_11_remediation.py`)** | `—` | **`6 passed`** | **PASS** |
| **Frontend Node Tests (`npm test`)** | `5 passed, 0 failed` | **`5 passed, 0 failed`** | **PASS** |
| **Spec Validation (`run_all_validations.py`)** | `10/10` validators, `13/13` gates | **`10/10` validators, `13/13` gates** | **PASS** |
| **Python Compilation (`compileall`)** | Exit `0` | **Exit `0`** | **PASS** |
| **Mypy (`src/trustrag`, 110 files)** | `35` legacy errors (4 files) | `35` legacy errors (4 untouched files); **0 errors in Phase 11 edits** | **LEGACY ONLY** |
| **Ruff (`src tests tools`)** | `1345` legacy lints | `1348` legacy lints; **0 errors in `audit.py`, `security.py`, `phase10_runner.py`, `test_phase_11_remediation.py`** | **LEGACY ONLY** |
