# 18 — Evidence & Execution Log

**Repository Head:** `713c54e2065b4cd37f63b2fb8c9a8bf3694ed831` (`main`)
**Audit Host:** `Windows-11-10.0.26200-SP0` | System Python `3.13.14` | `.venv313` | Node.js
**Audit Constraints Enforced:** Read-only across `src/`, `configs/`, `tests/`, `data/`, and Git history; outputs written strictly inside [reports/reality_audit/](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/) and scratch logs.

---

## 1. Executed Command & Forensic Script Ledger

| Step | Command / Script Run | Exit Code | Key Output / Evidence File |
| :---: | :--- | :---: | :--- |
| 1 | `pytest tests/ --ignore=...` (8 `resource`-blocked serving/API files, `-m "not integration"`) | `1` | `644 passed, 3 failed, 2 deselected` (`54.87 s`) — 2 logger `capfd` order bugs + 1 `resource` import at `suites.py:1843` (`pytest_sys_runnable.txt`) |
| 2 | `pytest tests/unit/test_foundation.py -vv` | `0` | `9/9 passed` (`4.72 s`), confirming `test_logger_json_output` & `test_logger_filters_secret` failures are test-order state pollution |
| 3 | `.venv313\Scripts\python.exe -m pytest tests/` | `2` | `35` collection errors (missing `scikit-learn`, `aiohttp` in `.venv313`; `pytest_venv313.txt`) |
| 4 | `python tools/spec_validation/run_all_validations.py` | `0` | `13/13` heuristic spec gates `PASS`; `cold_import_init_ms = 22101.71`, `warm_p50_ms = 19.222` (`spec_val_sys.txt`). *Side effect:* updated timestamps in 3 tracked files `reports/evaluation/g3_linguistic_suite_g3_linguistic_suite_eval_ed2dae3f96*` |
| 5 | `node --test frontend/tests/dashboard.test.mjs` | `0` | `5/5 passed` (`857 ms`, `frontend_test.txt`) |
| 6 | `.venv313\Scripts\ruff.exe check src tests tools` | `1` | `24,503` lines of lint findings (`ruff_out.txt`) |
| 7 | `.venv313\Scripts\mypy.exe src` | `1` | `43` type errors across `6` files (`mypy_out.txt`) |
| 8 | Forensic Probe Part 1 (`datasets`, SHA-256, leakage, weights, SRM, calibrators) | `0` | `71` data files hashed, 13 adapters probed (`7` hit HF retry despite `offline=True`), `0` neural weights (`part1_datasets_models.json`) |
| 9 | Forensic Probe Part 2 (G1, Retriever, G2, G3, Generator, Serving/API imports) | `0` | `G1` (`11` cases + `5` paraphrase), `G2` offline (`p_out=0.9283`, `3v1`), `G3` (`11` probes), Windows `resource` import errors (`part2_subsystems.json`) |
| 10 | Forensic Probe Part 3 (10 E2E traces, 6 controlled attacks, BoolQ `n=15`) | `0` | `2/6` security breaches (`atk_poisonedrag_stealth_factual`, `atk_duplicate_poison_3v1`), `12/15` BoolQ utility (`27.24 ms`) (`part3_e2e_attacks.json`) |
| 11 | Forensic Probe Part 4 (Phase 10 JSONL recomputation, external benchmarks, adaptive) | `0` | `100%` exact match on `phase11_remediated` & `canonical_v2` JSONLs; `6/7 BLOCKED`, `ragtruth n=5` (`part4_metrics_and_phase10.json`) |
| 12 | Forensic Probe Part 5 (Unit/neg G3 probes, re-answer, CLI subprocesses, 50-file AST, Wilson/McNemar) | `0` | `1000 mg per day` vs `1 g daily` (`0.60 < 0.65`), `cli_health exit 1`, `665` `test_*` AST scan, Wilson 95% CIs (`part5_extras.json`) |
| 13 | Deliverable JSON Builder (`build_json_deliverables.py`) | `0` | Generated & parsed all 5 JSON deliverables under `reports/reality_audit/` |

---

## 2. Deliverable Inventory (`reports/reality_audit/` — 24 Files)

- **Machine-Readable JSON Artifacts (`5`):**
  - [component_verdicts.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/component_verdicts.json)
  - [dataset_inventory.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/dataset_inventory.json)
  - [model_inventory.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/model_inventory.json)
  - [api_inventory.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/api_inventory.json)
  - [experiment_results.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/experiment_results.json)
- **Structured Markdown Reports (`19`):**
  - `00_EXECUTIVE_SUMMARY.md` through `18_EVIDENCE_AND_EXECUTION_LOG.md`

