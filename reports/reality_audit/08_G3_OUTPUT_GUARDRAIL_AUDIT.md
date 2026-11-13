# 08 — G3 Output Evidence Verifier Audit

**Module:** [output_verifier.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/verification/output_verifier.py), [query_consistency.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/verification/query_consistency.py), [generalization.py](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/verification/generalization.py)
**Verdict:** `YELLOW` (**Readiness: `62%`**)

---

## 1. Linguistic, Numeric, Temporal & Unit Probe Results (`part2` + `part5`)

G3 passes `25/25` (`100%`) internal Phase 08 linguistic regression probes (`mean=4.21 ms`, `0` false support) and fixes `DEF-09` (`-10 C` sign preservation). Direct probing reveals clear boundary behaviors:

| Probe | Claim / Answer Tested | Expected | Observed Verdict | Query Consistent | Observed Coverage / Explanation |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `exact_support` | `"Water boils at 100 degrees Celsius at sea level."` | `SUPPORTED` | `SUPPORTED` (`VERIFIED`) | `True` | `conf=0.99` |
| `passive_voice` | `"Hamlet was written by William Shakespeare."` | `SUPPORTED` | `SUPPORTED` (`VERIFIED`) | `True` | `conf=0.75` |
| `numeric_contra` | `"Water boils at 85 degrees Celsius at sea level."` | `CONTRADICTED` | `CONTRADICTED` | `True` | Temperature conflict caught |
| `def09_negative_temp` | `"The solution freezes at -10 degrees Celsius."` (vs `10`) | `CONTRADICTED` | `CONTRADICTED` | `False` | `-10` vs `[10.0]` caught cleanly |
| `neg_vs_neg_exact` | `"-10"` claim matching `"-10"` evidence (non-matching synthetic query in probe) | `SUPPORTED` (claim) | Claim `SUPPORTED`, **Answer `INSUFFICIENT_EVIDENCE`** | `False` | Demonstrates query-consistency override gating final verdict |
| `temporal_contra` | `"The institute was founded in 2018."` | `CONTRADICTED` | `CONTRADICTED` | `True` | Temporal year conflict (`conf=0.65`) |
| `negation_contra` | `"Drug X is not safe for pediatric patients."` | `CONTRADICTED` | `CONTRADICTED` | `True` | Polarity flip caught |
| `unmentioned_insufficient` | `"Team Beta won the 2030 championship."` | `INSUFFICIENT` | `INSUFFICIENT_EVIDENCE` | `True` | Correctly abstains |
| `compound_partial` | True capital + false `99 million` population | `CONTRADICTED` / `INSUFFICIENT` | `INSUFFICIENT_EVIDENCE` | `True` | Avoids false support (`conf=0.5714`) |
| `unit_1000mg_vs_1g_exact` | `"The daily dose is 1000 mg."` vs `"The daily dose is 1 g."` | `SUPPORTED` | **`SUPPORTED`** | `True` | Unit normalizer succeeds (`coverage=1.00`) |
| `unit_1000mg_vs_1g_phrased` | `"The dosage is 1000 mg per day."` vs `"The daily dosage is 1 g daily."` | `SUPPORTED` | **`INSUFFICIENT_EVIDENCE`** | `True`/`False` | **Fails threshold: lexical coverage `0.60 < 0.65`** |
| `query_dos_refusal` | `"I cannot answer this question as an AI."` | `INSUFFICIENT` | `INSUFFICIENT_EVIDENCE` | `False` | Guard catches AI refusal |
| `query_topic_hijack` | `"Bananas are yellow tropical fruits..."` | `INSUFFICIENT` | `INSUFFICIENT_EVIDENCE` | `False` | Topic hijack caught |

---

## 2. Failure Modes Observed in E2E & Phase 10 Artifacts

1. **Phrased Unit Equivalence Failure (`coverage 0.60 < 0.65`):** Numeric/unit canonicalization only unlocks `SUPPORTED` when lexical unigram overlap already reaches `>= 0.65`; minor wording shifts (`"per day"` vs `"daily"`) fail verification.
2. **Coordinated Predicate Over-Conflict (`01_clean_factual`):** Splitting `"reaches its boiling point at 100 C and freezes at 0 C"` compares the extracted freezing clause against a NIST boiling-only doc (`doc_boil_nist`), falsely flagging a cross-doc contradiction (`UNCERTAIN` -> `UNVERIFIED`) on an accurate clean answer.
3. **Extractive Vague Evidence Self-Verification (`09_low_quality_ambiguous`):** Because extractive generation copies `"Maybe water boils at some variable temperature depending on vague factors. [lq_1]"`, G3 measures `coverage=1.00` against `lq_1` and returns **`SUPPORTED` (`TRUSTED`)** on hedge/low-quality content.
4. **Re-Answering Disabled by Default:** Re-answering works when enabled (`enable_reanswer=True` triggered attempt 1 in `08_hallucination` and `reanswer_recovery`, abstaining safely), but defaults to `False` in `configs/base.yaml`.
5. **Phase 10 Unseen Probes Discrepancy:** In `phase10_canonical_v2`, G3 scored **`0.50` claim accuracy (`2/4`, Macro F1 `0.50`)**, missing `unseen_num_contra` and `unseen_temp_contra` as `INSUFFICIENT_EVIDENCE`, while `phase11_remediated` tuned heuristics to reach `4/4` on those 4 specific probes. No large-scale NLI/DeBERTa verifier is present (`RAGTruth` evaluation covers only `n=5`, `acc=0.60`).

