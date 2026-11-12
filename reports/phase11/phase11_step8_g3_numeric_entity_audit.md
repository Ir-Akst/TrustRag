# TrustRAG Phase 11 — Step 8 G3 Numeric & Entity Audit (`DEF-11`, `DEF-12`)

**Target Modules:** `src/trustrag/verification/output_verifier.py`, `src/trustrag/engine/text_utils.py`  
**Probe Artifact:** `reports/phase11/step8_evidence/independent_probes.json`  
**Preserved Reproduction:** `reports/phase11/step8_evidence/reproduce_step8_findings.py`

---

## 1. Implementation Inspection
- **Entity Alignment (`DEF-11`):** Verified `_evaluate_numbers_with_grounded_tokens()` and `_find_temporal_or_unitless_numeric_contradiction()` extract `_extract_proper_entities(..., context_texts=[...]) - _NON_ENTITY_TEMP_SCALE_WORDS` (`celsius`, `fahrenheit`, `kelvin`, `centigrade`) before checking temperature or unit contradictions, preventing sentence-initial proper-noun loss (`claim[1:]` removed) and preventing scale names (`Fahrenheit` vs `Celsius`) from falsely splitting entities.
- **Entity-Slot Direction 2:** Confirmed `_evaluate_entity_slot_conflict()` excludes numeric RHS expressions (`not extract_numbers_and_units(c_right) and not extract_numbers_and_units(s_right)`), eliminating false slot conflicts on `In London, temperature was -10°C.` vs `In Paris, temperature was 10°C.` while retaining `Toronto serves as the capital of Canada.` vs `Ottawa ...` -> `CONTRADICTED`.
- **Single-Topic Numeric Classification (`DEF-12`):** Verified `single_topic_num_shared` in `_verify_single_proposition()` (`num_conflict and entities_ok and bool(non_num_claim_tokens) and non_num_claim_tokens.issubset(grounded_union)`) and tokenized Celsius `grounded_tokens` (`re.findall(r"[a-z0-9]+", cv_str.lower())`).

---

## 2. Independent Probe Results (`n = 36` G3 probes)

### A. DEF-11 Entity Alignment Probes (`16` probes: `13` matched expected, `3` edge mismatches)
- **Passed (`13/16`):**
  - `London recorded -10°C.` vs `Paris recorded 10°C.` -> `INSUFFICIENT_EVIDENCE`
  - `In London, temperature was -10°C.` vs `In Paris, temperature was 10°C.` -> `INSUFFICIENT_EVIDENCE`
  - `London recorded 50 mm rainfall.` vs `Paris recorded 100 mm rainfall.` -> `INSUFFICIENT_EVIDENCE`
  - `London recorded -10°C.` vs `London recorded 10°C.` -> `CONTRADICTED`; vs `London recorded 14°F.` -> `SUPPORTED`
  - Multi-city passages (`Paris recorded 10°C. London recorded 5°C.` -> `CONTRADICTED`; `... London recorded -10°C.` -> `SUPPORTED`; single-sentence `Paris recorded 10°C and London recorded -10°C.` -> `SUPPORTED`)
  - Reordered (`Temperature in London was -10°C.` vs `London recorded -10°C.` -> `SUPPORTED`)
  - City alias (`NYC` vs `New York City` -> `INSUFFICIENT_EVIDENCE`)
  - Non-numeric entity slots (`Toronto` vs `Ottawa`, `Geneva` vs `Vienna`, `capital of France is Lyon` vs `Paris` -> all `CONTRADICTED`)
- **Edge Mismatches / False Contradictions (`3/16`):**
  1. `diff_prop_same_entity` (**`DEF-16`**, Low): `London recorded 50 mm rainfall.` vs `London recorded 10°C.` -> `CONTRADICTED` (`mm` omitted from `NUMBER_UNIT_RE`, `10°C` also treated as unitless `'10'`).
  2. `lowercase_entity_cities` (**`DEF-11` residual**, Low): `london recorded -10°C.` vs `paris recorded 10°C.` -> `CONTRADICTED` (`_extract_proper_entities` requires capitalization).
  3. `missing_entity_in_claim` (**`DEF-11` residual**, Low): `Temperature recorded -10°C.` vs `Paris recorded 10°C.` -> `CONTRADICTED` (claim omits entity, so `c_ents` is empty).

### B. DEF-12 Single-Topic & Numeric Classification Probes (`20` probes: `17` matched expected, `3` edge mismatches)
- **Passed (`17/20`):**
  - `Temperature is 5°C.` vs `Temperature is 0°C.` -> `CONTRADICTED`; vs `5°C` / `41°F` -> `SUPPORTED`
  - `Temperature is -5°C.` vs `5°C` -> `CONTRADICTED`; vs `-5°C` -> `SUPPORTED`
  - `Temperature is -10°C.` vs `14°F` -> `SUPPORTED`; `-0°C` vs `0°C` -> `SUPPORTED`
  - Tolerance boundaries: `20.04°C` vs `20.00°C` -> `SUPPORTED`; `20.10°C` vs `20.00°C` -> `CONTRADICTED`; `68.05°F` vs `20°C` -> `SUPPORTED`; `68.2°F` vs `20°C` -> `CONTRADICTED`
  - Multi-measurement (`5°C and 100 kPa` vs `0°C and 100 kPa` -> `CONTRADICTED`), different properties (`Temperature is 5°C.` vs `Humidity is 5%.` -> `INSUFFICIENT_EVIDENCE`), ambiguous short claim (`It is 5°C.` vs `Temperature is 0°C.` -> `INSUFFICIENT_EVIDENCE`), decimal (`37.5°C` vs `36.6°C` -> `CONTRADICTED`), short dosage (`500mg` vs `100mg` -> `CONTRADICTED`), short weight (`70kg` vs `50kg` -> `CONTRADICTED`).
- **Edge Mismatches (`3/20`):**
  1. `temporal_change_meas` (**`DEF-15a`**, Medium): `Temperature was 5°C in 2020.` vs `Temperature is 0°C in 2024.` -> `CONTRADICTED` (`non_num_claim_tokens` strips `'2020'`).
  2. `diff_ent_diff_meas` (**`DEF-15b`**, Medium): `Sensor A is 5°C.` vs `Sensor B is 0°C.` -> `CONTRADICTED` (1-char entity labels `A`/`B` ignored).
  3. `missing_unit_claim` (Low): `Temperature is 5.` vs `Temperature is 5°C.` -> `SUPPORTED` (both extract `[('5', '')]`; unitless `'5'` matches `5°C`).

---

## 3. Error Rate Summary (`n = 36` G3 probes)
- **False Support (wrong `SUPPORTED` on non-entailed pair):** `0/36` (`1/36` unitless `5` vs `5°C` flagged above as edge mismatch; **`0` contradiction-to-support errors**).
- **False Contradiction:** `5/36` (`lowercase_entity_cities`, `missing_entity_in_claim`, `diff_prop_same_entity` [`DEF-16`], `temporal_change_meas` [`DEF-15a`], `diff_ent_diff_meas` [`DEF-15b`]).
- **Unnecessary `INSUFFICIENT_EVIDENCE`:** `0/36`.

