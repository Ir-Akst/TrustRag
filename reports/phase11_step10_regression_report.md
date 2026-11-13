# TrustRAG Phase 11 — Step 10 Independent Regression & Benchmark Report

**Repository:** `/home/aditya/rags/TrustRag-phase11` (`phase-11` @ `8229aee01a0b6f7fd61a5e774da5bb707bd6a7c1`)  
**Benchmark Outputs Saved (Non-Overwriting):** [phase11_component_benchmarks.json](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step10_evidence/phase11_component_benchmarks.json), [phase11_fair_comparison.json](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step10_evidence/phase11_fair_comparison.json), [spec_validation_step10.json](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step10_evidence/spec_validation_step10.json)

---

## 1. Automated Test Suites & Static Validation (Fresh Execution)

| Check | Exact Command | Observed Result | Notes / Exclusions |
| :--- | :--- | :---: | :--- |
| Full default pytest | `/home/aditya/rags/.venv/bin/pytest -W error -q` | **423 passed, 0 failed (`17.29s`)** | `2` HF integration tests deselected per `addopts` |
| Integration test inventory | `/home/aditya/rags/.venv/bin/pytest --collect-only -m integration -q` | **2 collected (`BLOCKED` offline)** | `test_boolq_sample_acquisition`, `test_squad_sample_acquisition` |
| API & Phase 11 targeted run | `pytest -q tests/unit/test_phase_09_api.py ... test_phase_11_*` | **48 passed in `4.50s`** | Covers API, fullstack, and Steps 3/5/7/9 suites |
| Frontend JS tests | `cd frontend && npm test` | **5 pass, 0 fail (`46.31ms`)** | XSS text nodes, Bearer header, metric/signal guards |
| Bytecode compilation | `python -m compileall -q src tests` | **PASS (exit 0)** | Full `src/` and `tests/` tree |
| Spec Validation Suite | `python tools/spec_validation/run_all_validations.py` | **PASS (`13/13` gates, `10/10` validators)** | Validators `A_schemas`..`J_runtime_conformance` PASS |
| Type checking (`mypy`) | `mypy --follow-imports=silent` on 4 Step 9 files | **0 errors** | `paraphraser.py`, `text_utils.py`, `output_verifier.py`, `test_phase_11_step9_remediation.py` |
| Linting (`ruff`) | `ruff check` on Step 9 files & changed modules | **All checks passed** | Filtered `--select F,E,W --ignore E501` on legacy modules |

---

## 2. Fresh Phase 11 Component & Clean-Utility Benchmark Results (vs Phase 10)

Running the Phase 10 evaluation modules on the current Phase 11 codebase cleanly measures Phase 11 improvements without altering historical Phase 10 archives:

### 2.1 Component Experiments (`seed=42`, offline)
- **G1 Attack vs Benign (`n=6`):** `accuracy = 1.0000`, `FPR = 0.0000`, `hier_1 = BLOCK` *(improved from Phase 10 `0.8333`)*.
- **G1 Paraphrase & Drift (`n=6`):** `accuracy = 1.0000` (`6/6`, `para_eq = True`) *(improved from Phase 10 `5/6`)*.
- **G2 MSD + Ablation (`n=64`):** `ROC-AUC = 0.8315` (`F4` dominant: removal drops AUC to `0.5315`; `F6` keeps `FPR = 0.0` vs `0.2571` without `F6`; `F1`/`F2` remain `0.0` availability offline).
- **G3 Linguistic Suite (`n=25`) & Unseen Probes (`n=4`):**
  - Linguistic suite: `25/25` (`pass_rate = 1.0`, `false_support_count = 0`).
  - Unseen probes: **`4/4` (`claim_accuracy = 1.0`, `macro_f1 = 1.0`, `FSR = 0.0`, `FCR = 0.0`)** *(improved from Phase 10 `2/4`)*.
- **SRM & FilterRAG:** Deterministic SRM fallback latency `0.0779 ms`; `hf_local` neural SRM and FilterRAG SLM explicitly **`BLOCKED`** offline (`No module named 'torch'`). Extractive proxy FilterRAG harms clean retention (`0.20`).

### 2.2 Local Comparative Benchmarks (`data/benchmarks_backup/`, `test` split, `seed=42`)
| Dataset | Profile | Accuracy | ASR | Clean Utility Rate | Statistical Summary vs `original_rag` |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `clean_rag` (`n=15`) | All 7 profiles (incl. `adaptive_trustrag`) | **1.0000** | `N/A` | **1.0000** | Zero clean utility degradation (`diff=+0.0000`, `p=1.0`) |
| `adversarial_robustness` (`n=40`) | `original_rag` | `0.5000` | `1.0000` | `1.0000` | Baseline |
| `adversarial_robustness` (`n=40`) | `static_trustrag` | `0.7500` | `0.5000` | `1.0000` | `+0.2500`, `p=0.0020`, `adj_p=0.0117`, `d=0.5701` |
| `adversarial_robustness` (`n=40`) | `adaptive_trustrag` | **0.8250** | **0.3500** | **1.0000** | **`+0.3250`, `p=0.0002`, `adj_p=0.0017`, `d=0.6852`, `FPR=0.00`** |
| `knowledge_poisoning` (`n=24`) | `original_rag` / `static_trustrag` | `0.5000` | `1.0000` | `1.0000` | Single-doc corpus limits consensus signals |
| `knowledge_poisoning` (`n=24`) | `adaptive_trustrag` | `0.5000` | `0.3333` | **0.3333** | Negative/trade-off result: `FPR=0.6667`, `p=1.0` (disclosed) |

**External Benchmarks Status:** `HaluEval`, `LLM-AggreFact`, `RSB`, `Natural Questions`, `HotpotQA`, and `MS MARCO` remain **`BLOCKED`** offline (`0` local records; `RAGTruth` has `5`-record local smoke only).

