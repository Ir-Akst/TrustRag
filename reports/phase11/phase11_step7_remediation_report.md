# TrustRAG Phase 11 — Step 7 Targeted Remediation Report (`DEF-10`, `DEF-11`, `DEF-12`)

**Worktree:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**Base HEAD:** `5481d6a88b8a9e2d5d7c7099a9692fd79e8ece46` (uncommitted working-tree remediation; no commit/push/merge performed)  
**Original Phase 10 Directory:** `/home/aditya/rags/TrustRag` confirmed untouched (`HEAD e65bcc80aac634900d1f8e343880fddf66cec168`, `27` status entries preserved)  
**Preserved Step 6 Evidence Checksums:** `reports/phase11/step7_evidence/step6_checksums.txt` (all `6` files verified `OK`)

---

## 1. DEF-10 — G1 Paraphraser Lowercase-Subject Attribute Drift
- **File Changed:** `src/trustrag/guardrails/paraphraser.py`
- **Root Cause:** `_has_attribute_head_drift()` only ran the disjoint non-entity stem check when `orig_ents & cand_ents` (capitalized entities) was non-empty, and `inventor`/`discoverer` (as well as other common attribute-head pairs) was absent from `_INCOMPATIBLE_ATTRIBUTE_GROUPS`. Lowercase subjects like `penicillin` bypassed the anchor check and remained in `orig_ct & cand_ct`, masking `inventor ↔ discoverer` substitutions.
- **Fix:**
  - Added `_extract_attribute_subject_tokens()` (extracting prepositional `of/for/about/in <subject>` and possessive `<subject>'s` anchors) and merged shared syntactic subject anchors (`shared_subj_toks`) with `orig_ents & cand_ents` inside `_has_attribute_head_drift()`.
  - Expanded `_INCOMPATIBLE_ATTRIBUTE_GROUPS` (including `inventor ↔ discoverer`, `founder ↔ owner/ceo`, `melting ↔ boiling/freezing`, `author ↔ publisher/editor/translator`, `height ↔ weight/mass/age`, `minimum ↔ maximum`, `revenue/income/profit ↔ cost/expense/debt/loss`, `import ↔ export`) and `_SYNONYM_GROUPS` (`price ↔ cost`, `vulnerable ↔ susceptible`, `begin ↔ start`, `author ↔ wrote/writer`, `publisher ↔ published`).
  - Preserved `min_similarity=0.30` intact.
- **Verification (`reports/phase11/step7_evidence/step7_probe_verification.json`):**
  - `11/11` negative attribute-drift probes (including `inventor ↔ discoverer` of `penicillin`, `founder ↔ owner` of `linux`, `diameter ↔ mass` of `earth`, `melting ↔ boiling` of `iron`, `price ↔ weight` of `gold`, `capital ↔ population` of `france`, `creator ↔ maintainer` of `python`, and possessive `penicillin's inventor ↔ discoverer`) rejected with `PARAPHRASE_ATTRIBUTE_DRIFT` (`0` false acceptances).
  - `6/6` positive paraphrase probes accepted (`0` false rejections).

---

## 2. DEF-11 — G3 Cross-Entity Temperature & Unit False Contradiction
- **File Changed:** `src/trustrag/verification/output_verifier.py`
- **Root Cause:**
  1. `_evaluate_numbers_with_grounded_tokens()` evaluated `c_temps` vs `s_temps` (and unit-bearing values) and returned `num_conflict=True` before checking whether claim and evidence proper entities were disjoint (`London` vs `Paris`).
  2. `_find_temporal_or_unitless_numeric_contradiction()` checked temperature-unit conflicts before entity alignment and sliced `claim[1:]` when extracting capitalized entities, missing sentence-initial proper nouns like `London`.
  3. `_evaluate_entity_slot_conflict()` Direction 2 fired on numeric/measurement right-hand predicates (e.g., `In London, temperature was -10°C.` vs `In Paris, temperature was 10°C.`) because `tokenize_content_words()` stripped `-`, causing `_tok_jaccard("-10°C", "10°C")` to return `1.0`.
- **Fix:**
  - Added `"temperature"` to `_COMMON_INITIAL_NON_PROPER_WORDS` and defined `_NON_ENTITY_TEMP_SCALE_WORDS` (`celsius`, `fahrenheit`, `kelvin`, `centigrade`) so scale names are never treated as conflicting proper entities.
  - Checked `_extract_proper_entities(claim, context_texts=[span]) - _NON_ENTITY_TEMP_SCALE_WORDS` vs `_extract_proper_entities(span, context_texts=[claim]) - _NON_ENTITY_TEMP_SCALE_WORDS` before returning temperature or unit contradictions in `_evaluate_numbers_with_grounded_tokens()` and before section 1 of `_find_temporal_or_unitless_numeric_contradiction()`.
  - Excluded numeric/measurement right-hand clauses (`extract_numbers_and_units(...)`) from Direction 2 of `_evaluate_entity_slot_conflict()`.
- **Verification:**
  - `London recorded -10°C.` vs `Paris recorded 10°C.` -> **`INSUFFICIENT_EVIDENCE`**.
  - `In London, temperature was -10°C.` vs `In Paris, temperature was 10°C.` -> **`INSUFFICIENT_EVIDENCE`**.
  - `London recorded 50 mm rainfall.` vs `Paris recorded 100 mm rainfall.` -> **`INSUFFICIENT_EVIDENCE`**.
  - Same-entity temperature checks (`London recorded -10°C.` vs `London recorded 10°C.` -> `CONTRADICTED`; `London recorded -10°C.` vs `London recorded 14°F.` -> `SUPPORTED`; `Water boils at 212 degrees Fahrenheit.` vs `100 degrees Celsius` -> `SUPPORTED`) all pass.

---

## 3. DEF-12 — G3 Short Numeric Claim Classification (`5°C` vs `0°C`)
- **File Changed:** `src/trustrag/verification/output_verifier.py`
- **Root Cause:** `_evaluate_numbers_with_grounded_tokens()` correctly flagged `Temperature is 5°C.` vs `Temperature is 0°C.` as `num_conflict=True`, but `_verify_single_proposition()` required `len(matched_tokens) >= 2` for `topic_shared`. Short single-topic numeric claims (`claim_tokens = {"temperature", "5"}`, `"dose", "500mg"`, `"weight", "70kg"`) only have `1` non-numeric topic token (`matched_tokens = {"temperature"}`), causing `topic_shared` to evaluate to `False` and downgrading the contradiction to `INSUFFICIENT_EVIDENCE`. In addition, line 1372 added `cv_str.lower()` (`"-10"`) instead of tokenized digits (`"10"`) to `grounded_tokens`, causing short negative cross-unit claims (`Temperature is -10°C.` vs `Temperature is 14°F.`) to fall below `min_support_coverage`.
- **Fix:**
  - Updated `topic_shared` in `_verify_single_proposition()` to accept `single_topic_num_shared` when `num_conflict` is `True`, `entities_ok` is `True`, and 100% of non-numeric claim content tokens (`non_num_claim_tokens`) appear in `grounded_union`.
  - Updated Celsius-matched `grounded_tokens` population to use `re.findall(r"[a-z0-9]+", cv_str.lower())` (consistent with `TOKEN_RE`).
- **Verification:**
  - `Temperature is 5°C.` vs `Temperature is 0°C.` -> **`CONTRADICTED`**.
  - `Temperature is 5°C.` vs `Temperature is 5°C.` / `41°F` -> **`SUPPORTED`**.
  - `Temperature is -10°C.` vs `Temperature is 14°F.` -> **`SUPPORTED`**.
  - `Dose is 500mg.` vs `Dose is 100mg.` -> **`CONTRADICTED`**; `Weight is 70kg.` vs `Weight is 50kg.` -> **`CONTRADICTED`**.
  - Unrelated short claims (`Temperature is 5°C.` vs `Humidity is 0°C.`, `The bridge was built in 2018.` vs `The house was built in 1998.`) remain **`INSUFFICIENT_EVIDENCE`**.

