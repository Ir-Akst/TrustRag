# TrustRAG Phase 11 — Step 5 Targeted Remediation Report (`DEF-08`, `DEF-09`)

**Worktree:** `/home/aditya/rags/TrustRag-phase11` | **Branch:** `phase-11` | **Starting HEAD:** `5481d6a88b8a9e2d5d7c7099a9692fd79e8ece46` (not committed)  
**Preserved Step 4 Evidence Checksums:** `reports/phase11/step5_evidence/step4_checksums.txt`

---

## 1. DEF-08 — G1 Paraphraser Attribute-Head Drift
- **File Changed:** `src/trustrag/guardrails/paraphraser.py`
- **Root Cause:** `_content_tokens()` stripped stopwords, leaving `{capital, france}` vs `{population, france}` (`ct_jaccard=0.3333 >= 0.30`), so attribute substitutions over the same entity passed `min_similarity=0.30`.
- **Fix:** Added `_has_attribute_head_drift()`, `_stem_token()`, and `_expand_with_synonyms()` to reject incompatible attribute/relation substitutions (`capital↔population`, `founded↔headquartered`, `largest↔oldest`, `cause↔consequence`, `birth↔death`, and disjoint non-entity content stems over a shared entity) while preserving `min_similarity=0.30` and equivalent paraphrases. Also replaced literal `’` with `\u2019` (eliminating `RUF001`).
- **Before / After:**
  - `validate_paraphrase("What is the capital of France?", "What is the population of France?", min_similarity=0.30)`: `accepted=True` -> **`accepted=False`** (`PARAPHRASE_ATTRIBUTE_DRIFT`).
  - **Step 5 Regression (`test_def08_bidirectional_attribute_drift_and_legitimate_paraphrases`):** `11/11` negative attribute-drift pairs rejected (`0` false acceptances); `5/5` positive paraphrases accepted (`0` false rejections).

---

## 2. DEF-09 — G3 Signed Negative-Number False-Support
- **Files Changed:** `src/trustrag/engine/text_utils.py`, `src/trustrag/verification/output_verifier.py`
- **Root Cause:** `NUMBER_UNIT_RE` did not capture leading `-` signs (`-10` was extracted as `10`), and `_evaluate_numbers_with_grounded_tokens()` lacked affine `°C ↔ °F` temperature conversion.
- **Fix:**
  - Updated `NUMBER_UNIT_RE` to preserve `-` only after start-of-string or boundary characters `[\s(\[:=><,]` (leaving hyphenated IDs like `AES-256` and dates like `2024-05-12` / `2018-2020` positive), and normalized `-0` -> `0`.
  - Added `_temp_to_celsius()` and Celsius-equivalence checking (`±0.05°C`) in `output_verifier.py`, plus `\u2013\u2014` in `_YEAR_RANGE_RE`.
- **Before / After:**
  - `"Temperature dropped to -10°C."` vs `"Temperature rose to 10°C."`: `SUPPORTED` -> **`CONTRADICTED`**.
  - `-40°C` vs `-40°F`, `-10°C` vs `14°F`, `0°C` vs `-0°C`: **`SUPPORTED`**.
  - `-5%` vs `5%`: **`CONTRADICTED`**; `AES-256` & `2018-2020`: positive numbers preserved.

