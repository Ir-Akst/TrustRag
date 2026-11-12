# TrustRAG Phase 11 — Step 8 G1 Paraphraser Audit (`DEF-10`)

**Target Module:** `src/trustrag/guardrails/paraphraser.py`  
**Probe Artifact:** `reports/phase11/step8_evidence/independent_probes.json`  
**Preserved Reproduction:** `reports/phase11/step8_evidence/reproduce_step8_findings.py`

---

## 1. Implementation Inspection
Inspected:
- `_extract_attribute_subject_tokens()` (lines 153–161): uses `_ATTR_PREP_SUBJ_RE` (`of|for|about|in <1-2 words>`) and `_POSSESSIVE_SUBJ_RE` (`<word>'s`), filtering `_PARAPHRASE_STOPWORDS` and digits.
- `_has_attribute_head_drift()` (lines 180–210): checks `_INCOMPATIBLE_ATTRIBUTE_GROUPS` bidirectionally with exception guard when the same group appears on the candidate side, then unions `orig_ents & cand_ents` with `shared_subj_toks = (orig_subj_toks & cand_raw) | (cand_subj_toks & orig_raw)` and checks overlap of `_expand_with_synonyms({_stem_token(t) ...})`.
- `_stem_token()` (lines 164–169) and `_expand_with_synonyms()` (lines 172–177): single-pass suffix stripping (`ation`, `ment`, `ing`, `ed`, `es`, `ly`, `s`) and `_SYNONYM_GROUPS` expansion.
- `min_similarity=0.30` threshold in `validate_paraphrase()` remains unchanged.

---

## 2. Independent Probe Results (`n = 42` probes: `29` drift, `13` preservation)

### A. Adversarial Attribute Drift (`n = 29`)
- **Rejected (`25/29`):**
  - `inventor ↔ discoverer` across lowercase (`penicillin`), uppercase (`PENICILLIN`), title case (`Penicillin`), mixed case (`mRNA`), verb (`invented/discovered`), and possessive (`penicillin's`).
  - `founder ↔ owner`, `founder ↔ CEO`, `melting ↔ boiling`, `melting ↔ freezing`, `capital ↔ population` (lowercase `france`), `largest ↔ oldest` (lowercase `japan`), `cause ↔ consequence` (lowercase `inflation`), `birth ↔ death` (lowercase `darwin`).
  - Prepositional anchors `for` (`treatment for diabetes` ↔ `cause for diabetes`), `in` (`temperature in mars` ↔ `pressure in mars`), multiword lowercase subjects (`climate change`, `stainless steel`), subject-initial (`When was linux founded?` ↔ `Where is linux headquartered?`).
  - Unseen attribute pairs (`diameter ↔ mass` of `earth`, `creator ↔ maintainer` of `python`, `ceo ↔ cto` of `stripe`, `dosage ↔ toxicity` of `aspirin`, `How tall is mount everest?` ↔ `How old is mount everest?`).
- **False Acceptances (`4/29` — `13.79%`, documented as `DEF-13` and `DEF-14`):**
  1. `anchor_about`: `"What is the law about copyright?"` -> `"What is the history about copyright?"` (`accepted=True`, `sim=0.50`) — `"about"` not in `_PARAPHRASE_STOPWORDS`, masking `law` vs `history`.
  2. `multi_entity_between` (lowercase): `"What is the distance between london and paris?"` -> `"What is the flight time between london and paris?"` (`accepted=True`, `sim=0.5357`) — `"between"` and `"and"` not in `_PARAPHRASE_STOPWORDS`.
  3. `multi_entity_cap` (capitalized): `"What is the distance between London and Paris?"` -> `"What is the flight time between London and Paris?"` (`accepted=True`, `sim=0.5357`) — same root cause (`"between"` and `"and"` leak into `orig_ct & cand_ct`).
  4. `unseen_no_prep_verb`: `"What treats malaria?"` -> `"What prevents malaria?"` (`accepted=True`, `sim=0.3333`) — anchorless lowercase verb pair absent from `_INCOMPATIBLE_ATTRIBUTE_GROUPS`.

### B. Paraphrase Preservation (`n = 13`)
- **Accepted (`10/13`):** Syntactic reordering (`photosynthesis convert sunlight`), equivalent synonyms (`built ↔ constructed`, `price ↔ cost`, `vulnerable ↔ susceptible`), possessive normalization (`France's capital`, `Tokyo's population`, `water's boiling point`), plural/verb shift (`symptoms of diabetes` ↔ `symptoms does diabetes have`), harmless context (`capital city of France, please`), and `deterministic_safe_paraphrase` (`maximum safe daily dose of Paracetamol in 2026`).
- **False Rejections (`3/13` — `0` from `_has_attribute_head_drift()`):**
  - `"When was the bridge built?"` -> `"When did someone build the bridge?"` (`PARAPHRASE_SEMANTIC_DRIFT(sim=0.2500<0.30)`)
  - `"What are the symptoms of diabetes?"` -> `"What symptom does diabetes cause?"` (`PARAPHRASE_SEMANTIC_DRIFT(sim=0.2500<0.30)`)
  - `"Who is the author and publisher of Dune?"` -> `"Who wrote and published Dune?"` (`PARAPHRASE_SEMANTIC_DRIFT(sim=0.2667<0.30)`)
- **Over-Reliance / Entity Masking Check:** Prepositional/possessive anchor stripping prevents single shared lowercase subjects from masking attribute substitutions in `of`/`for`/`in`/`'s` constructions; however, unremoved prepositions/conjunctions (`about`, `between`, `and`) in `_PARAPHRASE_STOPWORDS` currently allow multi-entity `between X and Y` queries to mask attribute changes (`DEF-13`).

