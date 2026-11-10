# TrustRAG — Phase 03 Step 4: Round 2 Remediation Test & Verification Report

**Execution Date:** 2026-11-10  
**Environment:** Windows, Python 3.12.4 (`C:\Users\aksha\AppData\Local\Programs\Python\Python312\python.exe`), `pytest-9.1.1`  
**Overall Result:** **239 passed, 0 failed, 2 deselected (`-m 'not integration'`)**

---

## 1. Executed Test Suites vs Executed Scratch Probes (Clear Distinction)

All 239 pytest cases below were **executed and observed passing** (not merely authored on disk), alongside separate out-of-suite scratch verification runs ([`final_audit_probe.py`](file:///C:/Users/aksha/.gemini/antigravity/brain/e71318da-b62e-4318-bf6b-822944a58136/scratch/final_audit_probe.py) and `round2_probe.py`). No existing tests were removed, skipped, or weakened.

| Suite / Check | Exact Command (`$env:PYTHONPATH="src"`) | Exit Code | Executed Result | Delta vs Pre-Round 2 |
|---|---|---:|---|---|
| **G3 Output Verification Suite** | `python -m pytest tests/unit/test_phase_03_g3_verification.py -v` | `0` | **`82 passed in 10.44s`** | **+50 new tests** (`17` baseline + `15` Round 1 + `50` Round 2) |
| **G1 Input Guardrail** | `python -m pytest tests/unit/test_phase_03_defense.py -k TestG1InputGuardrail -v` | `0` | **`4 passed, 20 deselected in 7.90s`** | Unchanged (`0` regressions) |
| **G2 MSD & Retrieval** | `python -m pytest tests/unit/test_phase_03_g2_msd.py -v` | `0` | **`32 passed in 7.80s`** | Unchanged (`0` regressions) |
| **Phase 01 / 02 Data Engineering** | `python -m pytest tests/unit/data/ -q` | `0` | **`92 passed in 5.01s`** | Unchanged (`0` regressions) |
| **Complete Default Suite** | `python -m pytest -v` | `0` | **`239 passed, 2 deselected in 13.99s`** | **+50** (`2` live network integration tests deselected per `pyproject.toml`) |
| **Syntax Compilation** | `python -m compileall -q src tests` | `0` | Exit code `0` (`COMPILE_EC=0`) | Clean |
| **Core Package Imports** | `import trustrag`, `InputGuardrail`, `MultiSignalDetector`, `TrustAwareRetriever`, `OutputEvidenceVerifier`, `TrustRAGPipeline`, `extract_numbers_and_units`, `extract_frequency_expressions` | `0` | `CORE_IMPORTS_OK` | Clean |
| **Ruff / Mypy Checks** | `python -m ruff --version`; `python -m mypy --version` | `1` / `1` | Not installed in runtime (`RUFF_EC=1`, `MYPY_EC=1`) | Unavailable (explicitly not claimed as passed) |

---

## 2. Adversarial Coverage Breakdown (50 New Executed Tests + Scratch Audit Reproduction)

| Requirement Category | Minimum Required | Executed Permanent Tests | Covered Scenarios & Verified Outcomes |
|---|---:|---:|---|
| **Dosage Quantities (`HIGH-01`)** | 10 | **10** (`test_r2_dosage_01`..`10`) | `one tablet` vs `two tablets` padded -> `CONTRADICTED`; reverse; `one` vs `two capsules`; `1 tablet` <-> `one tablet` -> `SUPPORTED`; `two` <-> `2 doses` -> `SUPPORTED`; `three` vs `four drops` -> `CONTRADICTED`; `puffs`/`teaspoons`/`injections`; `capsule` vs `tablet` / `teaspoon` vs `tablespoon` isolated; freq + qty checked independently; unrelated word numbers safe. |
| **Antonyms, Clauses & Scope (`HIGH-02`)** | 10 | **10** (`test_r2_polarity_01`..`10`) | Bidirectional `approved/rejected` (passive/active), `accepted/denied`, `took/avoided` (relative clause), `received/refused`, `allowed/prohibited`, `increased/decreased` + mixed-clause safety; `only when` / `only after` / `except if` omitted -> `INSUFFICIENT_EVIDENCE`; multi-sentence and mid-sentence `although` negation isolation. |
| **Entities, Initial Nouns & Acronyms (`MEDIUM-01`)** | 8 | **8** (`test_r2_entity_01`..`08`) | `Ottawa` vs `Toronto serves as` -> `CONTRADICTED`; `acts as` & `remains`; `US` vs `UK` regulator; `IV` vs `PO` passive/active; word-boundary collision check (`positive`/`used`); bidirectional `mRNA` <-> `DNA`; `FDA`/`EMA` passive vs active org attribution; initial proper noun (`Berlin`/`Munich`) vs ordinary starters (`Adults`). |
| **Coordinated Predicates (`MEDIUM-02`)** | 8 | **8** (`test_r2_coord_01`..`08`) | Mandatory `reduces high hospital fever quickly, lowers blood pressure, and prevents cancer` -> `INSUFFICIENT_EVIDENCE` (supported ref preserved & both unverified predicates named); mixed 2-sentence answer -> `PARTIALLY_SUPPORTED`; `A, B and C`; `A, B, C`; `A and B` long-prefix sneak blocked; all-3 supported across 1 & 3 docs; repeated subjects; `Paris, France` / `50,000` / parenthetical preserved. |
| **G2 `UNCERTAIN` Pipeline Boundaries (`MEDIUM-03`)** | 6 | **6** (`test_r2_uncertain_01`..`06`) | Sole obfuscated doc (`\u200b`, `G2=UNCERTAIN`) tested under permissive SRM `TRUSTWORTHY`, `DISABLED`, `TIMEOUT`, `UNAVAILABLE`, `fallback_on_error=False` (`RuntimeError`), explicit distinction vs low-trust non-security `UNCERTAIN` (`"UNVERIFIED"`) and `CONTRADICTED`/`ABSTAINED`. |
| **Cross-Period Frequencies (`MEDIUM-04`)** | 5 | **5** (`test_r2_freq_01`..`05`) | `twice daily` <-> `twice per week` (`CONTRADICTED`), `once daily` <-> `once weekly` (`CONTRADICTED`), `every 6h` <-> `four times daily` (`SUPPORTED`), `twice daily` <-> `every 12h` & `three times daily` <-> `every 8h` (`SUPPORTED`), unrelated `monthly` clinic context alongside `twice daily` (`SUPPORTED`). |
| **Unsafe Output Quarantine (`LOW`)** | 3 | **3** (`test_r2_quarantine_01`..`03`) | Extractive surviving `POISONED` doc quarantines unsafe `answer`/`evidence`, sets `safe_to_display=False`, `unsafe_output_quarantined=True`, preserves raw payload in `quarantined_answer`/`quarantined_evidence` and `trust_report`, separates clean vs poisoned survivors (`top_k=3`), leaves clean outputs displayable (`safe_to_display=True`). |

---

## 3. G1 / G2 / Schema / Pipeline Compatibility Matrix (Executed Scratch Audit Reproduction)

Re-running the full Section 2/3/4 independent audit probe script after Round 2 remediation confirmed every single previously failed probe resolved:

- **Previous Audit Failures Eliminated (`0` false `SUPPORTED` / `0` false `TRUSTED`):**
  - `B4b_one_tablet_vs_two_tablets_padded`: Prior `SUPPORTED` (`cov=0.71`) -> Now **`CONTRADICTED`**
  - `C2b_passive_vs_active_neg` (`FDA approved` vs `rejected by FDA`): Prior `SUPPORTED` -> Now **`CONTRADICTED`**
  - `C3a_nested_subordinate_only_when`: Prior `SUPPORTED` (`cov=1.00`) -> Now **`INSUFFICIENT_EVIDENCE`**
  - `C3b_nested_subordinate_rel_clause` (`took` vs `avoided`): Prior `SUPPORTED` (`cov=0.80`) -> Now **`CONTRADICTED`**
  - `D1b_capital_canada_serves_as` (`Ottawa` vs `Toronto`): Prior `SUPPORTED` (`cov=0.75`) -> Now **`CONTRADICTED`**
  - `D3c_two_letter_acronym_US_vs_UK`: Prior `SUPPORTED` (`cov=0.83`) -> Now **`INSUFFICIENT_EVIDENCE`**
  - `rev_mRNA_claim` (`DNA` vs `mRNA`): Prior `SUPPORTED` (`cov=0.83`) -> Now **`INSUFFICIENT_EVIDENCE`**
  - `two_letter_AC_swap` (`IV` vs `PO`): Prior `SUPPORTED` (`cov=0.80`) -> Now **`CONTRADICTED`** (passive) / **`INSUFFICIENT_EVIDENCE`** (active)
  - `B3_twice_week_vs_twice_daily`: Prior `INSUFFICIENT_EVIDENCE` -> Now **`CONTRADICTED`**
  - `Sec4_G2_UNCERTAIN_obf_with_permissive_SRM`: Prior `overall=TRUSTED` -> Now **`overall=FLAGGED` (`safe_to_display=False`)**
  - `F_sec4_extractive_on_poison`: Now `overall=FLAGGED`, `safe_to_display=False`, `unsafe_output_quarantined=True`, public `evidence=[]`, raw diagnostic answer & `p1` preserved in `quarantined_answer` / `quarantined_evidence`.
- **Non-Regression Invariants Confirmed:** G1 `original_input` byte-preserved, G2 `coverage_attenuated` (`ratio=0.6061`, `score=0.8647` vs unattenuated `0.9552`), F2 `require_configured` default (`available=False`, `status="UNAVAILABLE"`), Retrieval cap (`top_k=3`, `candidate_multiplier=3` -> `cap_limit=1`, `removed=['d2']`, `trusted=['d3','d4','d1']`), and `G1 -> G2 -> Generation -> G3 -> SRM -> Final` order preserved.

