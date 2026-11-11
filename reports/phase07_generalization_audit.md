# Phase 07 — Step 06: Cross-Domain Generalization Audit

**Execution Date:** 2026-11-12  
**Branch:** `phase-7` (`cc1961e`)  
**Machine-Readable Artifact:** `reports/evaluation/phase07_step06_generalization.json`

---

## 1. Per-Domain Evaluation on Cached Splits

All locally cached splits were evaluated individually without inflating results by mixing synthetic security with natural-language QA/claim verification. **Critical Sample-Size Caveat:** Locally cached non-BoolQ real-world verification splits hold `n=3..11` records; percentages below are exact counts over tiny smoke fixtures and **do not establish statistical generalization**.

| Domain / Dataset | Split (`n`) | Verdicts Emitted | False `SUPPORTED` on Non-Supported | Supported Recall (`TP / Pos`) | Supported Accuracy | Mean Latency (ms) | Research Validity Note |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| **Hallucination (internal)** | `train+val+test` (`n=11`) | `INSUFF=8, CONTR=2, SUPP=1` | **0 / 6** | `1 / 5` (**0.2000**) | 0.6364 (`7/11`) | 5.73 | Tiny synthetic/curated claim pool (`test n=3`). |
| **ExpertQA** (multi-domain expert) | `test` (`n=3`) | `INSUFF=1, CONTR=2` | **0 / 2** | `0 / 1` (**0.0000**) | 0.6667 (`2/3`) | 6.23 | Fails to recover positive expert paraphrase (`0%` recall, `n=3`). |
| **WiCE** (Wikipedia fine-grained) | `test` (`n=3`) | `INSUFF=3` | **0 / 2** | `0 / 1` (**0.0000**) | 0.6667 (`2/3`) | 4.88 | Conservative `INSUFFICIENT` on all 3 records (`n=3`). |
| **RAGTruth** (LLM hallucinations) | `test` (`n=5`) | `SUPP=1, INSUFF=4` | **0 / 2** | `1 / 3` (**0.3333**) | 0.6000 (`3/5`) | 5.31 | Missing remaining ~984+ full RAGTruth test cases (`BLOCKED`). |
| **BoolQ Clean Retrieval** (uncontaminated) | `test` (`n=15` over `N=100`) | Static/Adaptive `R@5 = 0.7333` (`11/15`) vs Orig `0.8000` (`12/15`) | 0% false block | Grounding `0.3333` | N/A (extractive) | 71.84 / 107.17 | Tiny `N=100` distractor corpus; McNemar `p=1.0`. |
| **Security: `knowledge_poisoning`** | `test` (`n=24`) | Static G2 stops DoS (`4/4`); misses `8/8` factual flips | — | — | — | — | Templated over `3` shared target queries. |
| **Security: `adversarial_robustness`** | `test` (`n=40`) | Static G2 stops all `PROMPT_INJECTION` & `MALICIOUS_INSTRUCTION` (`10/10`); misses `CONFLICTING_EVIDENCE` (`7/7`) | — | — | — | — | Contains `BENIGN_INSTRUCTION_LIKE` controls (`6/40`). |

---

## 2. Ten-Axis Controlled Linguistic & Adversarial Probe Audit (`13` Probes)

Direct execution of `OutputEvidenceVerifier` (`VerificationConfig(enabled=True)`) + `verification/generalization.py` across all 10 required generalization axes yielded **`3 / 13` strict exact matches**, uncovering five concrete algorithmic weaknesses:

| # | Audit Dimension / Probe | Expected Verdict | Observed Verdict | Match | Root-Cause Analysis (`output_verifier.py` / `generalization.py`) |
| :-: | --- | --- | --- | :-: | --- |
| 1 | **Domain transfer** (medical phrasal upper bound: `"safe daily max ... 4000 mg"` vs `"should not exceed 4,000 mg"`) | `SUPPORTED` | **`CONTRADICTED`** | **FAIL** | Naive negation trigger (`"not"` in `"should not exceed"`) fires `_evaluate_polarity` conflict on an affirmative upper-limit phrasing! |
| 2 | **Paraphrase (synonym)** (`"serves as the national capital"` vs `"capital city is"`) | `SUPPORTED` | `SUPPORTED` | PASS | Matched via `_PARAPHRASE_REPLACEMENTS` dictionary (`generalization.py:L31-40`). |
| 3 | **Paraphrase adversarial passive/active swap** (`"firewall blocked malicious packet"` vs `"malicious packet blocked firewall"`) | `INSUFFICIENT_EVIDENCE` | **`SUPPORTED`** | **CRITICAL FAIL** | **Bag-of-words / TF-IDF symmetry bug:** identical lemmas regardless of subject–object syntactic role cause false `SUPPORTED`! |
| 4 | **Unicode variation** (`ＡＥＳ－２５６` fullwidth + `256\u200b-bit` zero-width in raw doc passed directly to G3) | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | Conserv. (Safe) | G1 & Pipeline normalize query/answer Unicode, whereas `OutputEvidenceVerifier` evaluated raw doc tokens without NFKC folding. |
| 5 | **Markdown & structured content** (Markdown table `\| Tokyo \| 14M \|` vs claim `"population of 14000000"`) | `SUPPORTED` | **`INSUFFICIENT_EVIDENCE`** | **FAIL** | `_linearize_markdown_tables` expands `14M` to `"14 million"` string, which fails numeric literal alignment against `"14000000"`. |
| 6 | **Multi-hop evidence (2-hop)** (`Alice->Paris`, `Paris->France` => `Alice->France`) | `SUPPORTED` | `SUPPORTED` | PASS | Solved by `_check_synonym_or_bridge_via_verifier` strict 2-hop capitalized bridge (`generalization.py:L366-400`). |
| 7 | **Multi-hop evidence (3-hop)** (`Alice->Paris->France->Europe` => `Alice->Europe`) | `SUPPORTED` | **`INSUFFICIENT_EVIDENCE`** | **FAIL** | 2-hop cap leaves 3+ hop chains unsupported. |
| 8 | **Numerical reasoning mismatch** (`500 patients` vs `50 patients`) | `CONTRADICTED` | `INSUFFICIENT_EVIDENCE` | Partial Safe | Fails cleanly (does not falsely support), though classifies as `INSUFFICIENT_EVIDENCE` instead of `CONTRADICTED`. |
| 9 | **Temporal contradiction** (`currently serves in 2026` vs `served in 2019 before retiring in 2021`) | `CONTRADICTED` | `INSUFFICIENT_EVIDENCE` | Partial Safe | Temporal check only triggers under exact matching anchor patterns; fails safely as `INSUFFICIENT_EVIDENCE`. |
| 10 | **Conditional / deontic claims** (`"receive immediately"` vs `"may qualify only after review unless custom"`) | `CONTRADICTED` | `INSUFFICIENT_EVIDENCE` | Partial Safe | Safety guard prevents false `SUPPORTED` (`_check_deontic_only_guard`), returning `INSUFFICIENT_EVIDENCE` instead of `CONTRADICTED`. |
| 11 | **Intra-document conflict** (`Section 1: supports ... However, Section 4 confirms ... completely unsupported`) | `UNCERTAIN` | **`SUPPORTED`** | **CRITICAL FAIL** | `_check_intra_doc_conflict` misses morphological negation (`supports` vs `unsupported`) across sections, falsely emitting **`SUPPORTED`**! |
| 12 | **Unit conversion (supported: `km` <-> `meters`)** (`5000 meters` vs `5 km`) | `SUPPORTED` | `SUPPORTED` | PASS | Handled cleanly by `_UNIT_FACTORS` in `generalization.py:L42-63`. |
| 13 | **Unit conversion (unsupported: `Fahrenheit` <-> `Celsius`)** (`212 F` vs `100 C`) | `SUPPORTED` | **`INSUFFICIENT_EVIDENCE`** | **FAIL** | Affine/non-multiplicative temperature scales (`C/F/K`) and currency/time units are not implemented. |

---

## 3. Cross-Domain Generalization Verdict

TrustRAG's deterministic heuristic G3 verifier enforces strong conservative precision on clean-vs-unmentioned boundary checks (**0 false `SUPPORTED` on `hallucination`, `expertqa`, `ragtruth`, `wice` small sets**), **but** exhibits low positive recall (`0.00–0.33`), fails 10 of 13 strict generalization probes, and harbors **3 high-severity logical bugs** (role-swap passive/active `SUPPORTED`, `supports`/`unsupported` intra-doc conflict miss, and `"should not exceed"` upper-limit false contradiction) that cannot be closed with regex rules alone without an NLI / Small Reasoning Model.
