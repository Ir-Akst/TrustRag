# TrustRAG Phase 11 — Step 9 Remediation Report (`DEF-13`, `DEF-14`, `DEF-15`, `DEF-16`)

## 1. Starting State & Integrity Preservation

- **Repository:** `/home/aditya/rags/TrustRag-phase11`
- **Branch:** `phase-11`
- **Base HEAD:** `5481d6a88b8a9e2d5d7c7099a9692fd79e8ece46`
- **Parent Commit:** `e65bcc80aac634900d1f8e343880fddf66cec168`
- **Original Phase 10 Worktree (`/home/aditya/rags/TrustRag`):** Untouched (`HEAD e65bcc80aac634900d1f8e343880fddf66cec168`, `27` pre-existing status entries).
- **Historical Evidence Checksums Verified (`OK`):**
  - Step 6 (`6/6 OK`): [step6_checksums.txt](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step7_evidence/step6_checksums.txt)
  - Step 7 (`6/6 OK`): [step7_checksums.txt](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step8_evidence/step7_checksums.txt)
  - Step 8 (`9/9 OK`, including `independent_probes.json`, `reproduce_step8_findings.py`, `spec_validation_step8.json`): [step8_checksums.txt](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step9_evidence/step8_checksums.txt)
- **Step 9 Evidence Directory:** [step9_evidence/](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step9_evidence/)

---

## 2. Remediated Defects & Root Causes

### `DEF-13` — G1 Paraphrase Stopword & Shared-Anchor Drift (Low)
- **Root Cause:** Shared grammatical bridges (`between`, `and`, `about`, `regarding`, etc.) remained in `_content_tokens()` during `_has_attribute_head_drift()`, creating spurious shared stems that masked substituted question attributes (e.g., `"distance between London and Paris"` ↔ `"flight time between London and Paris"`, `"law about copyright"` ↔ `"history about copyright"`). Multi-word subjects after `between <NP1> and <NP2>` were not captured by `_ATTR_PREP_SUBJ_RE`, and opposing prepositions (`inside` ↔ `outside`, `before` ↔ `after`, `above` ↔ `below`, `with` ↔ `without`) were not flagged.
- **Fix ([paraphraser.py](file:///home/aditya/rags/TrustRag-phase11/src/trustrag/guardrails/paraphraser.py)):**
  - Expanded `_ATTR_PREP_SUBJ_RE` (1–3 token subjects across `of|for|about|in|regarding|concerning|via|against|toward|towards`) and added `_BETWEEN_SUBJ_RE` for paired `between <NP1> and <NP2>` anchors.
  - Added `_SHARED_BRIDGE_WORDS` stripped exclusively inside `_has_attribute_head_drift()` when shared cleanly by both sides (leaving `_PARAPHRASE_STOPWORDS` untouched so `ct_jaccard` similarity calibration stays intact).
  - Added opposing spatial/relational prepositions (`inside`/`within` vs `outside`/`beyond`, `above`/`over` vs `below`/`under`/`beneath`, `before`/`prior` vs `after`/`following`, `with` vs `without`) to `_INCOMPATIBLE_ATTRIBUTE_GROUPS`.

### `DEF-14` — G1 Anchorless Lowercase Verb/Predicate Drift (Low)
- **Root Cause:** Short anchorless lowercase WH-questions (e.g., `"What treats malaria?"` ↔ `"What prevents malaria?"`) contain no capitalized named entities and no prepositional/possessive anchor markers, leaving `anchor_tokens` empty in `_has_attribute_head_drift()` so unrelated predicate swaps passed if cosine/char overlap met `0.30`.
- **Fix ([paraphraser.py](file:///home/aditya/rags/TrustRag-phase11/src/trustrag/guardrails/paraphraser.py)):**
  - Added `_WH_AUX_SUBJ_RE` and `_WH_POST_VERB_TARGET_RE` via `_extract_wh_target_tokens()` as fallback anchor extraction when `anchor_tokens` is empty, capturing shared grammatical targets/subjects (`malaria`, `inflammation`, `blood sugar`).
  - Added clinical/causal incompatible groups (`treat`/`treatment`/`cure` vs `prevent`/`prevention`, `treat`/`prevent` vs `cause`/`trigger`/`induce`, `treat` vs `diagnose`/`detect`) to `_INCOMPATIBLE_ATTRIBUTE_GROUPS`.
  - Added `_IRREGULAR_VERB_LEMMAS` (`wrote->write`, `built->build`, etc.) and genuine predicate synonym groups (`reduce/decrease/lower`, `treat/cure/remedy`, `prevent/block`, etc.) to `_SYNONYM_GROUPS` so legitimate verb inflections, passive forms, irregular past tenses, and synonyms stay accepted.

### `DEF-15` — G3 Temporal & Short Entity-Slot False Contradiction (Medium)
- **Root Cause:**
  1. `DEF-15a` (temporal change): `_evaluate_numbers_with_grounded_tokens()` evaluated temperature/unit conflicts without testing whether explicit temporal anchors (years, ranges, ISO dates, month markers) were disjoint (`"5°C in 2020"` vs `"0°C in 2024"`), while `single_topic_num_shared` in `_verify_single_proposition()` dropped all digit-containing tokens (including 4-digit years).
  2. `DEF-15b` (short entity slot labels): `_extract_proper_entities()` rejected tokens shorter than 3 characters, ignoring multi-token slot identifiers like `"Sensor A"` vs `"Sensor B"` or `"Device 1"` vs `"Device 2"`, and missing designators were not enforced by `entities_ok`.
- **Fix ([output_verifier.py](file:///home/aditya/rags/TrustRag-phase11/src/trustrag/verification/output_verifier.py)):**
  - Added `_extract_designated_identifiers()` capturing `<noun>=3+ chars + [A-Z]` (excluding verbs/articles/temperature scale heads via `_DESIGNATOR_EXCLUDED_HEADS`) and `<explicit designator noun> + <code 1-3 chars>` (`_EXPLICIT_DESIGNATOR_HEADS`) while preventing unit misparsing (e.g. `50 mg`). Enforced disjoint identifier separation in `_evaluate_numbers_with_grounded_tokens()`, `_find_temporal_or_unitless_numeric_contradiction()`, and `entities_ok` inside `_verify_single_proposition()`.
  - Added `_extract_temporal_context()` and `_temporal_contexts_disjoint()` covering years, ranges, ISO dates (`YYYY-MM-DD`), and context-qualified months. Prevented measurement conflicts across disjoint temporal anchors while preserving pure event-year contradictions (e.g. `"completed in 1899"` vs `"1889"`) and preserving 4-digit years in `non_num_claim_tokens` for `single_topic_num_shared`.

### `DEF-16` — G3 Incompatible Measurement-Unit Comparison (Low)
- **Root Cause:** `NUMBER_UNIT_RE` did not parse length/pressure/speed/frequency units (`mm`, `cm`, `km`, `kpa`, `kmh`, etc.) or `°`-prefixed temperature symbols (`10°C`), causing `"London recorded 10°C."` vs `"London recorded 50 mm rainfall."` to fall back to unitless numeric comparison (`10` vs `50`) and return `CONTRADICTED`.
- **Fix ([text_utils.py](file:///home/aditya/rags/TrustRag-phase11/src/trustrag/engine/text_utils.py), [output_verifier.py](file:///home/aditya/rags/TrustRag-phase11/src/trustrag/verification/output_verifier.py)):**
  - Extended `NUMBER_UNIT_RE` to parse length (`mm`, `cm`, `km`, `meter`, `inch`, `ft`, `yard`, `mile`, etc.), speed (`mph`, `kmh`, `kph`), pressure (`pa`, `hpa`, `kpa`, `mpa`, `bar`, `psi`, `mmhg`), frequency (`hz`, `khz`, `mhz`, `ghz`), and optional `°\s*(celsius|fahrenheit|c|f)` (normalizing `°` in `extract_numbers_and_units()`), deliberately omitting bare `m` so population shorthand like `"14M"` does not parse as meters.
  - Added matching `_UNIT_DIMENSIONS` entries so incompatible physical dimensions (`temp_c` vs `length`, `speed` vs `pressure_si`) evaluate to `INSUFFICIENT_EVIDENCE` rather than `CONTRADICTED`, while same-dimension cross-scale pairs (`50 mm` vs `5 cm` supported; `50 mm` vs `8 cm` contradicted) are compared in canonical base units.

---

## 3. Modified & Created Files

- Modified source files (cumulative Phase 11 uncommitted diff vs base HEAD `5481d6a88b8a9e2d5d7c7099a9692fd79e8ece46`: `3 files changed, 506 insertions(+), 26 deletions(-)` across Steps 5, 7, and 9):
  - [text_utils.py](file:///home/aditya/rags/TrustRag-phase11/src/trustrag/engine/text_utils.py)
  - [output_verifier.py](file:///home/aditya/rags/TrustRag-phase11/src/trustrag/verification/output_verifier.py)
  - [paraphraser.py](file:///home/aditya/rags/TrustRag-phase11/src/trustrag/guardrails/paraphraser.py)
- Created Step 9 test & evidence files:
  - [test_phase_11_step9_remediation.py](file:///home/aditya/rags/TrustRag-phase11/tests/unit/test_phase_11_step9_remediation.py) (`24` unit tests)
  - [verify_step9_probes.py](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step9_evidence/verify_step9_probes.py)
  - [step9_probe_verification.json](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step9_evidence/step9_probe_verification.json)
  - [step8_repro_after_step9.txt](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step9_evidence/step8_repro_after_step9.txt)
  - [spec_validation_step9.json](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step9_evidence/spec_validation_step9.json)

