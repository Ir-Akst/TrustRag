# Phase 44 — Independent Evaluation & Audit

## 1. Evaluation Scope & Independence Controls
- Seeded evaluation (`seed=42`) executed via `reports/phase44/scripts/run_phase44_evaluation.py` against the final frozen `src/` without test-set tuning.
- Fresh `N=160` G1 holdout (`p44_g1_fresh`) constructed separately from the Phase 42 benign-quoted benchmark (`N=120`) to verify out-of-sample generalization.
- Naturalistic G3 benchmarks (`HaluEval` $N=200$, `RAGTruth Summary` $N=50$) evaluated alongside controlled regimes ($N=120$), Document Firewall ($N=140$), and Profile B Production Neural Lifecycle ($N=15$ warm requests).
- All raw predictions and reproduction logs preserved under `reports/phase44/raw_predictions/` and `reports/phase44/reproduction_logs/`.

## 2. Statistical Summary (`STATISTICAL_RESULTS.json`)
- **G1 Fresh Holdout ($N=160$):** `ADR = 98.33%` (59/60, 95% CI `[91.14%, 99.71%]`), `ASR = 1.67%`, `FPR = 0.0%` (0/100, 95% CI `[0.00%, 3.70%]`), `F1 = 0.9916`.
- **G1 Phase 42 Benign-Quoted ($N=120$):** `Benign FPR = 5.0%` (5/100, 95% CI `[2.15%, 11.18%]`), down from `45.0%` in Phase 43; `ADR = 100.0%` (20/20, 95% CI `[83.89%, 100.0%]`).
- **G3 HaluEval ($N=200$):** `Coverage = 52.5%`, `Factual Recall = 78.0%` (78/100, 95% CI `[68.93%, 85.00%]`), `Factual Precision = 74.29%`, `Hallucination Leakage = 27.0%` (27/100, 95% CI `[19.27%, 36.43%]`).
- **G3 RAGTruth Summary ($N=50$):** `Coverage = 62.0%`, `Factual Recall = 76.0%` (19/25, 95% CI `[56.57%, 88.50%]`), `Factual Precision = 61.29%`, `Hallucination Leakage = 48.0%` (12/25, 95% CI `[30.03%, 66.50%]`).
- **G3 Controlled ($N=120$):** `100.0%` gate accuracy, `100.0%` supported acceptance, `100.0%` contradiction recall, `0.0%` unsupported leakage.
- **Firewall ($N=140$):** `0.0%` context leakage (95% CI `[0.00%, 4.09%]`), `0.0%` direct generator leakage, `0.0%` false quarantine.

## 3. Audit Findings & Verdict Justification
- **G1 Benign Utility & Security:** Attribution-aware quote masking reduced SOC/CTI/quoted-attack false positives by 40 percentage points (`45.0%` -> `5.0%`) and achieved `0.0%` FPR on fresh benign controls while keeping `98.33%` ADR on fresh attacks (1/15 miss in mixed benign + embedded attack).
- **G3 Evidence Grounding:** Short-QA recall recovered strongly (`10.0%` -> `78.0%` on HaluEval; `16.0%` -> `76.0%` on RAGTruth Summary), but RAGTruth Summary hallucination leakage increased from `8.0%` to `48.0%`, demonstrating an explicit precision-recall trade-off on long-form abstractive summaries.
- **Verdict:** **`PUBLICATION READY WITH CLAIM LIMITATIONS`** — Security boundaries, multilingual defense, benign utility, and controlled verification are strong and reproducible, while naturalistic long-summary hallucination leakage (`48.0%` on RAGTruth Summary, `27.0%` on HaluEval) and `5.0%` residual FPR on Phase 42 quoted attacks must be explicitly scoped as limitations.
