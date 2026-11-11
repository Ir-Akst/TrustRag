# TrustRAG Phase 04 — Step 7: G3 Output Evidence Verification Evaluation

**Date:** 2026-11-11  
**Component Evaluated:** `OutputEvidenceVerifier` (`src/trustrag/verification/output_verifier.py`) & `TrustRAGPipeline` Stage 7/8 Governance  
**Datasets Evaluated:**
- **Real/Benchmark Hallucination Corpus:** `data/benchmarks/hallucination/` (`test` $N=3$, `train` $N=7$, `val` $N=1$, `all` $N=11$ across `ragtruth`, `wice`, `expertqa`)
- **Linguistic & Adversarial Regression Suite (`g3_linguistic_suite`):** $N=25$ cases (`historical_regression_cases.json` + partial support, conflicting evidence, dosage discrepancy, restrictive scope, explicit negation, and Stage 7 Unicode answer obfuscation)

---

## 1. Hallucination Benchmark Results (`data/benchmarks/hallucination`)

| Split | $N$ | Answer Acc | Answer Macro-F1 | Claim Acc | Claim Macro-F1 | Unsupported Bin. (P / R / F1) | Contradiction Det. Rate | False-Support Rate (FSR) | Traceable Evidence Refs | Mean Lat (ms) |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| `test` | 3 | 0.6667 | 0.5556 | 0.6667 | 0.5556 | 0.6667 / **1.0000** / 0.8000 | **1.0000** (1/1) | **0.0000** (0) | **100%** | 2.78 |
| `train` | 7 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.5714 / **1.0000** / 0.7273 | 0.0000 (0/3) | **0.0000** (0) | **100%** | — |
| `all` (`train+val+test`) | 11 | 0.2727 | 0.2889 | 0.2727 | 0.2889 | 0.6000 / **1.0000** / 0.7500 | 0.2500 (1/4) | **0.0000** (0) | **100%** | 1.52 |

### Per-Class Breakdown (`all`, $N=11$)
- `SUPPORTED` (`support=5`): `TP=1, FP=0, FN=4` (`Precision=1.0000`, `Recall=0.2000`, `F1=0.3333`)
- `CONTRADICTED` (`support=4`): `TP=1, FP=1, FN=3` (`Precision=0.5000`, `Recall=0.2500`, `F1=0.3333`)
- `NOT_ENOUGH_EVIDENCE` (`support=2`): `TP=1, FP=7, FN=1` (`Precision=0.1250`, `Recall=0.5000`, `F1=0.2000`)

---

## 2. Linguistic, Structural & Unicode Probe Suite (`g3_linguistic_suite`, $N=25$)

| Metric | Observed Result |
|---|---|
| **Total Cases Passed** | **25 / 25 (`100.0%`)** |
| **False-Support Count** | **0** |
| **Categories Verified** | Coordinated predicates (`or`, `while`, `as well as`, `nor`, `yet`), irregular past comma-splices, `ScheduleAssertion` subject-binding, partial support (`PARTIALLY_SUPPORTED`), conflicting evidence, numeric/dosage mismatches (`500 mg` vs `5000 mg`), restrictive scope (`Only` vs `All`), explicit negation, benign emoji/ZWNJ controls, Unicode Tags/Hangul Filler/VS-Supplement quarantine, Stage 7 generated-answer obfuscation quarantine |
| **Latency** | `mean=3.77 ms`, `p50=1.97 ms`, `p95=11.76 ms` |

---

## 3. End-to-End Pipeline Output Governance (`hallucination`, $N=11$)

Passing each benchmark claim as `answer_override` through `TrustRAGPipeline`:
- **Unsupported / Contradicted Claims Released (`safe_to_display=True`):** **0 / 6 (`0.0%` false release)** — 2 marked `CONTRADICTED`, 4 marked `UNVERIFIED` (`safe_to_display=False`).
- **Supported Claims Released:** 1 / 5 (`ragtruth_qa_001` $\rightarrow$ `TRUSTED`, `safe_to_display=True`), while 4 paraphrased/tabular claims were conservatively withheld as `UNVERIFIED` (`safe_to_display=False`).

---

## 4. Error Analysis & Documented Findings

1. **Zero False Support (`FSR = 0.0`):** G3 strictly enforces predicate coverage (`>= 0.65`), entity matching, polarity, and numeric checks—never endorsing claims via cosine similarity alone.
2. **Paraphrase & Structured-Table Recall Deficit (`4/5` `SUPPORTED` routed to `INSUFFICIENT_EVIDENCE`):** Without an NLI cross-encoder, G3's lexical verifier rejects cross-acronym/paraphrase equivalents (`"ECB"` vs `"European Central Bank"` in `ragtruth_sum_003`; `"World War II"` vs `"Second World War"` in `wice_001`; `"CRISPR-Cas9"` vs `"Cas9 endonuclease"` in `expertqa_001`) and pipe-delimited tabular contexts (`ragtruth_d2t_005`).
3. **Un-united / Bare Number Conflicts Classified as `INSUFFICIENT_EVIDENCE` (`wice_002`, `ragtruth_sum_004`):** `"50 degrees Celsius"` vs `"100 degrees Celsius"` (`wice_002`) and `"1985"` vs `"1928"` (`ragtruth_sum_004`) were flagged for numeric mismatch and routed to `INSUFFICIENT_EVIDENCE` rather than `CONTRADICTED`, preserving safety (`0` false support) at the expense of 3-class `CONTRADICTED` recall.
4. **Over-Strict `%` Tolerance (`expertqa_003`):** `"84.7%"` vs `"roughly 85%"` was classified `CONTRADICTED` rather than `NOT_ENOUGH_EVIDENCE` because strict numeric mismatch fires on exact `%` disparity alongside `"baryonic"` vs `"non-baryonic"`.

---

## 5. Step 7 Acceptance Verdict

- [x] Claim-level and answer-level metrics reported separately.
- [x] Evidence attribution and traceability (`100%` refs with `doc_id` + `matched_span`) verified.
- [x] Contradictions, unsupported claims, linguistic edge cases, and Stage 7 Unicode quarantine evaluated (`25/25` linguistic pass, `0` false support).
- [x] Honest error analysis documented without exaggerating paraphrase recall.

**Step 7 Status:** **PASS** — Ready to proceed to Step 8 (SRM Evaluation).

