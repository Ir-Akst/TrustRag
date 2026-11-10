# TrustRAG Phase 03 Step 4 — G3 Round 5 Remediation Report

**Date:** 2026-11-10  
**Basis:** [phase03_g3_round4_final_independent_acceptance_audit.md](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/reports/phase03_g3_round4_final_independent_acceptance_audit.md)  
**Target:** Resolve `NEW-R4-HIGH-01`, `NEW-R4-HIGH-02`, `NEW-R4-HIGH-03`, and `NEW-R4-MEDIUM-01` while preserving G1, G2, SRM, public redaction guarantees, and prior Round 1–4 fixes.  
**Status:** `REMEDIATION COMPLETE — READY FOR ROUND 5 INDEPENDENT AUDIT`

---

## 1. Summary of Round 4 Audit Findings & Round 5 Remediation

| Finding ID | Root Cause in Baseline | Remediation Implemented | Before -> After Outcome |
| :--- | :--- | :--- | :--- |
| `NEW-R4-HIGH-01` | [`_VP_CONJUNCTION_RE`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/verification/output_verifier.py#L354), [`_extract_conjunct_segments`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/verification/output_verifier.py#L760), and [`_expand_coordinated_predicates_with_bodies`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/verification/output_verifier.py#L813) handled `and` / `but` only; coordinated predicates introduced by `or`, `as well as`, or participial `while + V-ing` remained unsplit and inherited `SUPPORTED` from shared prefix overlap. | Extended coordination regex and splitting/body expansion to cover `or`, `as well as`, and participial/finite `while` clauses using [`_is_leading_participle`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/verification/output_verifier.py#L740) and [`_NOMINAL_ING_NOUNS`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/verification/output_verifier.py#L358) so every factual predicate is independently verified. | `SUPPORTED` -> `INSUFFICIENT_EVIDENCE` on all 4 mandatory probes (`or cures cancer`, `or is toxic`, `while causing coma`, `as well as triggering paralysis`) and nested 4+ predicate mixes; positive controls remain `SUPPORTED`. |
| `NEW-R4-HIGH-02` | Comma-separated past predicates (`froze vessels`, `bled gums`, `swept debris`, `shrank lesions`) bypassed comma predicate detection in [`_extract_conjunct_segments`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/verification/output_verifier.py#L760) when the trailing verb was not in a closed past-verb set. | Generalized post-verbal comma splitting (`m.start() >= fv_end`) across multi-token post-verbal segments while excluding single capitalized title/place tokens (e.g., `Dr. Smith, PhD`, `Paris, France`), numeric commas (`50,000`), and non-verb nominal items (`fever, pain, and swelling`). | `SUPPORTED` -> `INSUFFICIENT_EVIDENCE` on all unseen irregular past tails; positive comma series and non-predicate comma controls remain `SUPPORTED`. |
| `NEW-R4-HIGH-03` | (A) In [`_evaluate_numbers_with_grounded_tokens`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/verification/output_verifier.py#L957), subject mismatch rejection ran only for single-schedule evidence (`len == 1`), letting equal-rate multi-subject evidence (`Renal labs ... hepatic panels ... prior to potassium fasting`) endorse unrelated claim subjects (`Potassium is checked monthly.`).<br>(B) [`_split_clause_subject_predicate`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/engine/text_utils.py#L388) lacked bare active plural verb splitting after plural/collective subjects and initially blocked verbs like `check` present in `_FREQ_NOMINAL_HEADS`. | (A) Weighted subject overlap (`3.0 * subj_ov`) in schedule matching, applied subject compatibility uniformly to both single- and multi-entry `target_entries`, and blocked cross-clause subject-action transfer.<br>(B) Added bare active plural verb splitting via [`_is_plural_subject_head`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/engine/text_utils.py#L369), [`_PURE_NOMINAL_FREQ_HEADS`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/engine/text_utils.py#L382), and [`_PLURAL_NON_VERB_OBJECTS`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/engine/text_utils.py#L287), plus semicolon `prior_subject` isolation in [`_extract_schedule_components`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/engine/text_utils.py#L467). | Equal-rate multi-subject probe (`Potassium is checked monthly.`), bare plural different-subject probe (`Doctors check vitals daily.`), and cross-clause swap (`Pharmacists check vitals weekly.`) all moved from `SUPPORTED` to `INSUFFICIENT_EVIDENCE`; passive and active positive controls remain `SUPPORTED`. |
| `NEW-R4-MEDIUM-01` | [`ZERO_WIDTH_OR_CONTROL_RE`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/engine/text_utils.py#L48) omitted Unicode Tag characters (`U+E0001–U+E007F`) and Variation Selectors (`U+FE00–U+FE0F`), and [`evaluate_instruction_content_signal`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/detection/signals.py#L382) only scanned raw text, missing obfuscated prompt injections. | Added `\ufe00-\ufe0f` and `\U000e0001-\U000e007f` to `ZERO_WIDTH_OR_CONTROL_RE` and evaluated threat patterns and hidden HTML directives over both raw `doc.text` and stripped text from `detect_obfuscation(doc.text)` while preserving benign multilingual Unicode text. | Tag- and variation-selector-obfuscated instructions are now flagged (`DOC_OBFUSCATION`, `DOC_PROMPT_INJECTION`) and quarantined before Generation, G3, and SRM; benign `es`/`de`/`fr`/`ja`/`ru` documents stay `CLEAN` (`G2_CLEAN`). |

---

## 2. Modified Repository Files

1. [src/trustrag/verification/output_verifier.py](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/verification/output_verifier.py)
   - Extended coordination regex, participial guard, post-verbal comma predicate extraction, predicate body expansion (`or`, `as well as`, `while + V-ing`, irregular past comma tails), and uniform multi-clause / cross-clause schedule subject verification.
2. [src/trustrag/engine/text_utils.py](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/engine/text_utils.py)
   - Extended `ZERO_WIDTH_OR_CONTROL_RE` for Unicode Tags (`\U000e0001-\U000e007f`) and Variation Selectors (`\ufe00-\ufe0f`), added bare active plural verb subject-predicate splitting for schedule assertions, and prevented semicolon-delimited clauses from inheriting `prior_subject`.
3. [src/trustrag/detection/signals.py](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/detection/signals.py)
   - Updated [`evaluate_instruction_content_signal`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/detection/signals.py#L382) to inspect obfuscation-cleaned text alongside raw text with deduplicated threat rule matches.
4. [tests/unit/test_phase_03_g3_verification.py](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/tests/unit/test_phase_03_g3_verification.py)
   - Added [`TestRound5Remediation`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/tests/unit/test_phase_03_g3_verification.py#L2069) (7 regression test methods covering all 4 Round 4 findings, positive controls, spy downstream containment, and multilingual Unicode controls).
5. [reports/phase03_g3_round5_remediation_report.md](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/reports/phase03_g3_round5_remediation_report.md) and [reports/phase03_g3_round5_test_report.md](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/reports/phase03_g3_round5_test_report.md)
   - Round 5 remediation and verification reports.

*(Prior independent audit reports and Phase 01/02/G1/SRM contracts remain untouched.)*

---

## 3. Known Limitations & Edge Notes

1. **Cross-Inflection Participial Paraphrasing:** When evidence uses a finite verb without a progressive form (e.g., `"aids recovery, and improves hydration"`) and a compound claim rewrites that predicate into a participial form (`"while aiding recovery as well as improving hydration"`), the extracted participle fragment (`"The medicine aiding recovery"`) can fail single-proposition token alignment and conservatively return `INSUFFICIENT_EVIDENCE` instead of `SUPPORTED`. This fails closed without producing false `SUPPORTED`.
2. **Pre-existing Non-False-Supported Audit Probe Variances:** In `audit_round3_independent.py`, `2D_ctrl_conditional_medical` returns `INSUFFICIENT_EVIDENCE` (conservative positive control) and `3_nom_max_daily_limit` returns `CONTRADICTED` (`expected=INSUFFICIENT_EVIDENCE`, `false_supported=False`). Both match Round 4 baseline behavior.
3. **Lint / Static Type Tool Availability:** `ruff` and `mypy` are not installed in the active Python 3.12 environment (`No module named ruff`, `No module named mypy`); syntax integrity across `src/` and `tests/` was verified via `python -m compileall -q src tests`.

---

**Final Status:** `REMEDIATION COMPLETE — READY FOR ROUND 5 INDEPENDENT AUDIT`

