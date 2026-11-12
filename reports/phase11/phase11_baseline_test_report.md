# TrustRAG Phase 11 — Baseline Test Report

**Worktree:** `/home/aditya/rags/TrustRag-phase11` | **Branch:** `phase-11` | **Commit:** `e65bcc80aac634900d1f8e343880fddf66cec168`

---

## 1. Automated Verification Baseline

| Check | Exact Command | Exit Code | Observed Result |
| :--- | :--- | :---: | :--- |
| **Full Python Test Suite** | `/home/aditya/rags/.venv/bin/pytest -W error -q` | `0` | **382 passed, 2 deselected** in 13.79s |
| **Scoped Mypy (Ph09+Ph10)** | `mypy src/trustrag/api ... tests/evaluation/test_phase_10_harness.py tools/run_phase10_benchmarks.py` | `1` | **29 errors in 3 imported legacy files** (`data/quality.py`, `data/benchmarks/builder.py`, `evaluation/suites.py`) |
| **Full Mypy (`src/trustrag`)** | `/home/aditya/rags/.venv/bin/mypy src/trustrag` | `1` | **35 errors in 4 files** (110 files checked; adds `data/cli.py`) |
| **Full Ruff Check** | `/home/aditya/rags/.venv/bin/ruff check src tests tools` | `1` | **1345 errors** (all in pre-Phase 09 legacy files; Phase 09+10 files clean) |
| **Python Compilation** | `/home/aditya/rags/.venv/bin/python -m compileall -q src tests tools` | `0` | **Passed** |
| **Frontend Tests** | `cd frontend && npm test` | `0` | **5 passed, 0 failed** in 53.40ms |
| **Specification Validators** | `/home/aditya/rags/.venv/bin/python tools/spec_validation/run_all_validations.py` | `0` | **PASS** — 10/10 validators, 13/13 gates (`3.41 ms` core, `4459.67 ms` runtime conformance) |

---

## 2. Blocked Baseline Items (Environment)
* **Neural SRM (`hf_local`):** `BLOCKED` (`torch`, `transformers`, `peft`, `trl` not installed).
* **External Benchmarks:** `HaluEval`, `LLM-AggreFact`, `RSB`, `Natural Questions`, `HotpotQA`, `MS MARCO` (`BLOCKED` — 0 local records offline); `RAGTruth` (`PARTIALLY_READY` — 10 local smoke records vs 18,000 target).

