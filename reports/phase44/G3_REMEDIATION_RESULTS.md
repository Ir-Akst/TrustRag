# Phase 44 — G3 Evidence Verification Remediation Results

## 1. Objective & Root Causes Addressed
Phase 43 identified two primary causes of low factual recall on naturalistic benchmarks (`HaluEval` raw QA: `10.0%` recall; `RAGTruth Summary`: `16.0%` recall):
1. **Short-claim exclusion (`< 3` words):** `EvidenceGroundedVerifier.extract_atomic_claims` dropped claims shorter than 3 words, causing 70/200 `HaluEval` short QA answers (entities, dates, yes/no, numbers) to abstain before NLI verification.
2. **Single-sentence & uncontextualized NLI:** Isolated 1–3 word QA answers lacked predicate context when scored against long documents, and multi-sentence evidence synthesis failed when facts spanned adjacent sentences.

## 2. Targeted Remediation (`src/trustrag/verification/grounded_verifier.py`)
- **Removed `< 3` word exclusion** in `extract_atomic_claims` (retaining 1–2 word QA answers; skipping only empty or trivial filler).
- **Adjacent 2-sentence sliding windows** added to `evidence_spans` and `full_evidence_text` for cross-sentence synthesis.
- **Short QA contextualization:** For 1–3 word claims with a query, evaluates `f"The answer to '{query.strip()}' is {claim}."` alongside the raw claim.
- **Full-document entity & numerical fallback:** Added numerical fallback and entity check when `best_ent >= 0.45`, plus `short_span_match`.
- **Contradiction precedence:** `best_con >= 0.55` or (`best_con >= contradiction_threshold` and `best_con > best_ent + 0.05`).
- **Bounded CPU latency:** Top-16 lexical-overlap candidate span pre-filtering (`if len(evidence_spans) > 16`) bounds NLI forward passes on long documents.

## 3. Before vs. After Results

### 3.1 HaluEval ($N=200$, 100 Factual / 100 Hallucinated)
| Metric | Phase 43 Baseline (Raw) | Phase 44 Remediated | Delta | Wilson 95% CI (Phase 44) |
| --- | --- | --- | --- | --- |
| Coverage | 17.0% | **52.5%** | +35.5 pp | — |
| Abstention Rate | 83.0% | **47.5%** | -35.5 pp | — |
| Factual Recall | 10.0% (10/100) | **78.0%** (78/100) | +68.0 pp | [68.93%, 85.00%] |
| Factual Precision | 29.41% | **74.29%** | +44.88 pp | — |
| Hallucination Leakage | 24.0% (24/100) | **27.0%** (27/100) | +3.0 pp | [19.27%, 36.43%] |
| Confusion Matrix | TP=10, FP=24, TN=76, FN=90 | **TP=78, FP=27, TN=73, FN=22** | — | — |

### 3.2 RAGTruth Summary ($N=50$, 25 Factual / 25 Hallucinated)
| Metric | Phase 43 Baseline | Phase 44 Remediated | Delta | Wilson 95% CI (Phase 44) |
| --- | --- | --- | --- | --- |
| Coverage | 12.0% | **62.0%** | +50.0 pp | — |
| Abstention Rate | 88.0% | **38.0%** | -50.0 pp | — |
| Factual Recall | 16.0% (4/25) | **76.0%** (19/25) | +60.0 pp | [56.57%, 88.50%] |
| Factual Precision | 66.67% | **61.29%** | -5.38 pp | — |
| Hallucination Leakage | 8.0% (2/25) | **48.0%** (12/25) | +40.0 pp | [30.03%, 66.50%] |
| Confusion Matrix | TP=4, FP=2, TN=23, FN=21 | **TP=19, FP=12, TN=13, FN=6** | — | — |

### 3.3 Controlled Verification Regimes ($N=120$)
| Metric | Phase 44 Result |
| --- | --- |
| Gate Accuracy | **100.0%** |
| Supported Acceptance | **100.0%** |
| Contradiction Recall | **100.0%** |
| Unsupported Leakage | **0.0%** |

## 4. Honest Limitations & Operating Trade-off
- On `HaluEval` ($N=200$), removing `< 3` word exclusion and adding query-contextualized NLI lifted factual recall from `10.0%` to `78.0%` and factual precision from `29.41%` to `74.29%` with only a `+3.0 pp` shift in hallucination leakage (`24.0%` to `27.0%`).
- On `RAGTruth Summary` ($N=50$), lifting coverage from `12.0%` to `62.0%` and recall from `16.0%` to `76.0%` introduced a clear precision/leakage trade-off: hallucination leakage rose from `8.0%` (2/25, mostly abstained) to `48.0%` (12/25). Long-form abstractive summaries with subtle entity/relation distortions remain challenging for a small 141M-parameter DeBERTa-v3-small NLI model without abstaining heavily.
