# Phase 08 — Step 04: G1 Query Paraphrasing Report

**Branch:** `phase-8`  
**Added / Modified Modules:** `src/trustrag/guardrails/{paraphraser.py,input_guardrail.py,__init__.py}`, `src/trustrag/engine/schemas.py`, `src/trustrag/config/engine_config.py`  
**Tests:** `tests/unit/test_phase_08_step04_g1_paraphrasing.py`

---

## 1. Controlled Paraphrasing Implementation

1. **Authoritative Original Query:** `G1Assessment.original_input` and `normalized_input` always govern G1 safety decisions and authoritative intent.
2. **Strict Semantic & Security Validator (`validate_paraphrase`):** Every candidate paraphrase is screened for:
   - Numeric/unit preservation (`extract_numbers_and_units`),
   - Negation polarity parity (`has_strict_negation`),
   - Year/month/temporal marker parity,
   - Conditional clause markers (`if`, `unless`, `only if/when/after`, `except`, `without`, `provided`, `assuming`),
   - Named-entity & acronym retention,
   - Combined lexical + TF-IDF semantic similarity floor (`min_paraphrase_similarity=0.30`),
   - Structural sanity (no JSON/think/newline injection), Unicode obfuscation/confusables, and threat patterns (`match_threat_patterns`).
3. **Security Invariant:** Inputs classified `G1Decision.BLOCK` are never paraphrased; malicious paraphrases injected by untrusted callables are explicitly rejected (`paraphrase_accepted=False`, `paraphrased_query=None`).
4. **Deterministic Backend:** Supports `paraphrase_backend="deterministic"` (`deterministic_safe_paraphrase`) and `"callable"` behind `GuardrailsConfig.enable_paraphrasing` (off by default to protect clean baseline compatibility).

## 2. Verification Results

- `mypy` (`6 / 6` files): **`0` errors**.
- `ruff check` (`paraphraser.py`, `__init__.py`, `test_phase_08_step04_g1_paraphrasing.py`): **`0` errors**.
- `pytest`: all tests in `test_phase_08_step04_g1_paraphrasing.py` + `test_phase_03_defense.py` passed cleanly, explicitly validating all `9` violation classes (negation, numeric, entity, temporal, conditional, Unicode, prompt injection, semantic drift, malformed structure) plus bypass prevention.
