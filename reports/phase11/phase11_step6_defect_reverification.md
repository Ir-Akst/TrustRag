# TrustRAG Phase 11 — Step 6 Independent Defect Re-Verification

**Artifact:** `reports/phase11/step6_evidence/independent_probes.json`

## 1. DEF-08 — Paraphraser Attribute-Head Drift (`paraphraser.py`)
- **Negative Probes (`n=20`, 10 attribute pairs × 2 directions):** `18/20` rejected; **`2` False Acceptances**:
  - `Who is the inventor of penicillin?` <-> `Who is the discoverer of penicillin?` (`accepted=True`, `sim=0.3333`)
  - **Root Cause (`DEF-10`, Medium):** `_has_attribute_head_drift()` only checks general disjoint non-entity stems when `orig_ents & cand_ents` (capitalized entities) is non-empty; lowercase subjects like `"penicillin"` bypass it, and `inventor`/`discoverer` was absent from `_INCOMPATIBLE_ATTRIBUTE_GROUPS`.
- **Positive Probes (`n=7`):** `5/7` accepted; **`2` False Rejections** due to low lexical overlap (`sim=0.2500` on `symptoms -> symptom ... cause`; `sim=0.2667` on `author and publisher -> wrote and published`).

## 2. DEF-09 — Signed Numeric & Temperature Reasoning (`text_utils.py`, `output_verifier.py`)
- **Probes (`n=17`):** `15/17` passed; **`2` Failures**:
  1. `diff_entity_neg` (`London recorded -10°C.` vs `Paris recorded 10°C.`): returned **`CONTRADICTED`** instead of **`INSUFFICIENT_EVIDENCE`** (**False Contradiction**, **Medium `DEF-11`**). Root cause: `_evaluate_numbers_with_grounded_tokens()` returns `(False, True, ...)` on temperature mismatch before verifying subject-entity alignment (`London` != `Paris`).
  2. `pos_vs_zero` (`Temperature is 5°C.` vs `Temperature is 0°C.`): returned `INSUFFICIENT_EVIDENCE` instead of `CONTRADICTED` (**Missed Contradiction**, **Low `DEF-12`**).
- **Zero False-Support Verified:** `0` false-supported verdicts observed across all `17` probes; `-10°C vs 10°C`, `-40°C vs -40°F`, `-10°C vs 14°F`, `0°C vs -0°C`, `-5% vs 5%`, `AES-256`, and `2024-05-12` all passed.

