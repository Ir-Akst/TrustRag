# TrustRAG Phase 11 — Independent Defect Report

Per Section 12, two new defects were discovered during independent red-team testing in `tests/unit/test_phase_11_independent_audit.py`. Their failing tests are preserved unfixed for explicit remediation approval.

---

## DEF-08: G1 Paraphraser Attribute-Head Drift False Acceptance
- **Severity:** **Medium**
- **Failing Test:** `tests/unit/test_phase_11_independent_audit.py::test_independent_def04_paraphrase_robustness_and_drift`
- **Reproduction:** `validate_paraphrase("What is the capital of France?", "What is the population of France?", min_similarity=0.30)` returns `accepted=True` (`semantic_similarity=0.3333`).
- **Root Cause:** `_content_tokens()` in `src/trustrag/guardrails/paraphraser.py` strips stopwords, leaving `{capital, france}` vs `{population, france}` (`ct_jaccard = 1/3 = 0.3333 >= 0.30`) without checking whether the interrogative target noun (`capital` vs `population`) changed.

---

## DEF-09: G3 Signed Negative Number False-Support
- **Severity:** **High**
- **Failing Test:** `tests/unit/test_phase_11_independent_audit.py::test_independent_def03_g3_comprehensive_contradictions_and_zero_fsr`
- **Reproduction:** `OutputEvidenceVerifier().verify("Temperature dropped to -10°C.", [EvidenceDocument(doc_id="d1", text="Temperature rose to 10°C.")])` returns **`SUPPORTED`** instead of `CONTRADICTED`.
- **Root Cause:** `extract_numbers_and_units()` in `src/trustrag/engine/text_utils.py` does not preserve the leading `-` sign on negative numbers (`"-10"` is extracted as `"10"`), causing `-10°C` and `10°C` to match as identical values.

---

## Ruff `+3` Investigation (`1345 -> 1348`)
- Verified via `ruff check --statistics`: the `+3` increase over Step 2 (`1345 -> 1348`) comes from `RUF001` (`ambiguous-unicode-character-string` for `’` in `paraphraser.py:118` and `–`/`—` in `output_verifier.py:_YEAR_RANGE_RE`) introduced during Step 3.

