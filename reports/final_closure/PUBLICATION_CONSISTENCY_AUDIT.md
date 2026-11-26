# Publication Consistency Audit

## 1. Audit Scope
Audited all Phase 44 reports (`PHASE44_FINAL_REPORT.md`, `G3_REMEDIATION_RESULTS.md`, `G1_BENIGN_UTILITY_RESULTS.md`, `SECURITY_REGRESSION_RESULTS.md`, `INDEPENDENT_EVALUATION.md`, `PUBLICATION_CLAIM_MATRIX.md`, `REPRODUCIBILITY_GUIDE.md`) and `FINAL_RESEARCH_PAPER.md` against `reports/phase44/STATISTICAL_RESULTS.json`, `reports/phase43/STATISTICAL_RESULTS.json`, and `reports/phase44/scripts/run_phase44_evaluation.py`.

## 2. Checklist Verification
| Audit Criterion | Status | Evidence / Notes |
| --- | --- | --- |
| **All denominators are correct** | **PASS** | `p44_g1_fresh`: 60 attacks / 100 controls (`160`); `p42_quoted_after`: 20 attacks / 100 benign (`120`); `halueval_200`: 100 factual / 100 hallucinated (`200`); `ragtruth_summary_50`: 25 factual / 25 hallucinated (`50`); `controlled_120`: `120`; `firewall`: 90 malicious / 50 benign (`140`); `production_neural`: `15` warm requests. |
| **Baselines use comparable evaluation protocols** | **PASS** | Phase 43 vs. Phase 44 comparisons use identical datasets, splits, and seeds (`seed=42` on `data/processed/halueval/test.jsonl` and `data/processed/ragtruth/test.jsonl`; identical Phase 42 `N=120` quoted benchmark). |
| **Confidence intervals are correctly reported** | **PASS** | All primary rates report Wilson 95% CIs matching `STATISTICAL_RESULTS.json` exactly. |
| **G1 fresh holdout and quoted benchmark remain separate** | **PASS** | Reported in separate tables (`p44_g1_fresh` $N=160$ vs. `g1_p42_quoted_fpr_120_after` $N=120$) without pooling. |
| **G3 coverage, precision, recall, and leakage all reported** | **PASS** | All four metrics are reported for both `HaluEval` (`52.5%` cov, `74.29%` prec, `78.0%` rec, `27.0%` leak) and `RAGTruth Summary` (`62.0%` cov, `61.29%` prec, `76.0%` rec, `48.0%` leak). |
| **RAGTruth 48% leakage is prominently disclosed** | **PASS** | Explicitly highlighted in `PHASE44_FINAL_REPORT.md`, `G3_REMEDIATION_RESULTS.md`, `INDEPENDENT_EVALUATION.md`, `PUBLICATION_CLAIM_MATRIX.md`, and `FINAL_RESEARCH_PAPER.md` (Sections 13, 17, 20), and fully diagnosed in `reports/final_closure/RAGTRUTH_ERROR_ANALYSIS.md`. |
| **Two failed unit tests are disclosed accurately** | **PASS** | Both `test_suspicious_inputs_flagged_and_original_preserved` and `test_temperature_calibrator_preserves_zero_clean_fpr` are accurately disclosed (`819 passed, 2 skipped, 2 failed`) and proven pre-existing via parent commit `9d6874e7ca65d5eb5e1440ab1205a7dffdf36cc1`. |
| **No unsupported state-of-the-art claims** | **PASS** | No SOTA claims made; verdict is scoped to `READY WITH CLAIM LIMITATIONS`. |
