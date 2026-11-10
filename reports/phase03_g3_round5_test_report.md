# TrustRAG Phase 03 Step 4 — G3 Round 5 Verification & Test Report

**Date:** 2026-11-10  
**Environment:** Windows 11, Python 3.12.4 (`C:\Users\aksha\AppData\Local\Programs\Python\Python312\python.exe`), `pytest 9.1.1`  
**Status:** `REMEDIATION COMPLETE — READY FOR ROUND 5 INDEPENDENT AUDIT`

---

## 1. Automated Pytest Suite Results (Post-Final Code/Test Edit)

| Check Scope | Exact Command | Result | Duration | Exit Code |
| :--- | :--- | :--- | :--- | :--- |
| G3 Verification (incl. `TestRound5Remediation`) | `python -m pytest tests/unit/test_phase_03_g3_verification.py -q` | **141 passed** | 12.32s | 0 |
| G1 Input Guardrail | `python -m pytest tests/unit/test_phase_03_defense.py -k TestG1InputGuardrail -q` | **4 passed, 20 deselected** | 7.83s | 0 |
| G2 Multi-Signal Detector | `python -m pytest tests/unit/test_phase_03_g2_msd.py -q` | **32 passed** | 8.11s | 0 |
| Phase 03 Defense Integration | `python -m pytest tests/unit/test_phase_03_defense.py -q` | **24 passed** | 9.91s | 0 |
| Foundation & Phase 01/02 Data Pipeline | `python -m pytest tests/unit/test_foundation.py tests/unit/data -q` | **101 passed** | 4.75s | 0 |
| Full Default Test Suite | `python -m pytest -v` | **298 passed, 2 deselected** (300 collected; 2 live-network/service tests deselected per `pyproject.toml`) | 16.54s | 0 |

---

## 2. Static & Import Smoke Checks

| Check | Exact Command | Result | Exit Code |
| :--- | :--- | :--- | :--- |
| Bytecode Compilation | `python -m compileall -q src tests` | Clean pass (no errors) | 0 |
| Module Import Smoke Test | `python -c "import sys; sys.path.insert(0, 'src'); import trustrag; from trustrag.pipeline.trustrag_pipeline import TrustRAGPipeline; from trustrag.verification.output_verifier import OutputEvidenceVerifier; from trustrag.detection.msd import MultiSignalDetector; from trustrag.engine.text_utils import detect_obfuscation, extract_schedule_assertions; print('IMPORT_SMOKE_OK')"` | `IMPORT_SMOKE_OK` | 0 |
| Static Lint (`ruff`) | `python -m ruff --version` | Not installed (`No module named ruff`) | 1 |
| Static Type Check (`mypy`) | `python -m mypy --version` | Not installed (`No module named mypy`) | 1 |

---

## 3. Adversarial Audit & Regression Probe Execution

All independent scratch probe scripts were executed against the final Round 5 codebase (prior to report writing, with no subsequent source changes):

1. **Round 4 Independent Probe Suite (`audit_round4_independent_probes.py`):** Exit code `0`.
   - `3A` coordinated/comma predicate probes: `false_sup: []`, `fn: []`.
   - `3B` clinical schedule probes (`3B_adv_two_wrong_subjects_same_rate_lower_third`, `3B_adv_active_plural_no_aux_diff_subj`, `3B_adv_active_plural_cross_obj`, `3B_adv_3coord_*`, etc.): `false_sup: []`, `fn: []`.
   - `3C` containment & spy isolation: `poison_only`, `obf_only`, `html_hidden_only`, `mixed_clean_poison_obf`, `custom_sec_unc_and_unassessed` all returned `decision="FLAGGED"`, `quarantined=True`, with poisoned/obfuscated/unassessed docs absent from Generation, G3, SRM requests, and public `evidence`.
   - `3D` public serialization & log redaction: `any_public_or_log_leak=False`, `cli_rcs=[0, 0]`, `denied_default=True`, `sr_leaks=[]`.
   - `3E_extra` Unicode Tag (`\U000e0020`), Variation Selector (`\ufe00`), and mixed injection probes: `tag=True`, `var=True`, `reason_codes=['DOC_PROMPT_INJECTION', 'DOC_OBFUSCATION', 'G2_SUSPICIOUS_INSTRUCTION']`, `decision='FLAGGED'`, `quarantined=True`, `gen_seen=[[]]`.
   - `4` G1/G2/cap regression checks: `g1_orig_exact=True`, `g2_policy='coverage_attenuated'`, `g2_f2_unavailable_by_default=True`, `cap_limit=2`, `cap_removed_count=2`.
2. **Round 3 Independent Probe Suite (`audit_round3_independent.py`):** Exit code `0`.
   - Section 2 (`43` probes): `false_supported=0`, `ok=42` (only `2D_ctrl_conditional_medical` conservative `INSUFFICIENT_EVIDENCE`, `false_sup=False`).
   - Section 3 (`30` probes): `false_supported=0`, `exact=29` (only `3_nom_max_daily_limit` `CONTRADICTED`, `false_sup=False`).
3. **CLI & LLM Integration Audit (`audit_cli_llm.py`):** Exit code `0`.
   - `CLI_RC=0 0`, `CLI_JSON_LEAK=False`, `REVEAL_JSON_LEAK=False`, `CLI_TXT_LEAK=False`, `REVEAL_TXT_LEAK=False`, `LLM_CALLED=0`, `LLM_DECISION=FLAGGED`.

---

## 4. Round 5 Test Cases Added in `TestRound5Remediation`

Located in [`tests/unit/test_phase_03_g3_verification.py`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/tests/unit/test_phase_03_g3_verification.py#L2069):

1. `test_high01_or_and_copular_predicates_require_independent_grounding`
2. `test_high01_nested_and_three_plus_predicates_and_positive_controls`
3. `test_high02_comma_separated_irregular_past_predicates_blocked`
4. `test_high02_positive_and_non_predicate_comma_controls`
5. `test_high03_equal_rate_multi_subject_and_bare_plural_active_verbs`
6. `test_medium01_unicode_tag_and_variation_selectors_quarantined_pre_downstream`
7. `test_medium01_benign_multilingual_unicode_not_flagged`

---

**Final Status:** `REMEDIATION COMPLETE — READY FOR ROUND 5 INDEPENDENT AUDIT`

