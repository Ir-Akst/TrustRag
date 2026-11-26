# Phase 33 Independent Audit: Statistical Integrity & Raw-Data Audit

## 1. Audit Methodology
We performed an independent recalculation of all metrics directly from the raw prediction logs stored in `reports/phase32/raw_predictions/`:
1. `adaptive_redteam_predictions.jsonl` ($N=400$)
2. `indirect_injection_predictions.jsonl` ($N=400$)
3. `multilingual_predictions.jsonl` ($N=900$)
4. `evidence_grounding_predictions.jsonl` ($N=300$)

## 2. Reproduction of Phase 32 Raw Predictions

| Evaluation Dataset | Phase 32 Claimed | Phase 33 Recomputed from Raw JSONL | Match? |
| :--- | :--- | :--- | :--- |
| **Adaptive Red-Team ($N=400$)** | TP=200/200, FP=0/200, ADR=100.0%, FPR=0.0% | TP=200/200, FP=0/200, ADR=100.0%, FPR=0.0% | **EXACT MATCH** |
| **Document Firewall ($N=400$)** | Quarantined=200/200, Leaked=0, Utility=80.0% | Quarantined=200/200, Leaked=0, Utility=80.0% | **EXACT MATCH** |
| **Multilingual ($N=900$)** | TP=380/450, FP=0/450, ADR=84.44%, FPR=0.0% | TP=380/450, FP=0/450, ADR=84.44%, FPR=0.0% | **EXACT MATCH** |
| **Evidence Grounding ($N=300$)** | Accuracy=300/300 (100.0%) | Accuracy=300/300 (100.0%) | **EXACT MATCH** |

## 3. Statistical Rigor & Potential Leakage Checks
- **No Duplicate IDs:** All JSONL prediction records carry unique identifiers.
- **Label Hygiene:** Ground truth labels were not visible to detectors during inference.
- **Wilson Score Interval Precision:** Recomputed 95% Wilson confidence intervals match formulas across all sample subsets.
- **Synthetic Distribution Limitation:** Phase 32 raw predictions were evaluated on templated synthetic attacks. While mathematically exact on those sets, they did not generalize to out-of-vocabulary lexical synonyms, as demonstrated by the Phase 33 holdout audit.
