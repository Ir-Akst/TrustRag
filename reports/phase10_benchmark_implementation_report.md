# TrustRAG Phase 10 — Benchmark & Harness Implementation Report

## 1. Implemented Architecture (`src/trustrag/evaluation/`)
Phase 10 extends the Phase 04–08 evaluation layer without breaking any existing contracts:

- **Dataset Inventory (`src/trustrag/evaluation/datasets/inventory.py`):** Audits all 7 external benchmark targets and local corpora, recording SHA-256 hashes, licenses, access types, split counts, and `AVAILABLE / PARTIALLY_READY / BLOCKED` status.
- **Extended Metrics Library (`src/trustrag/evaluation/metrics_extended.py`):**
  - Security: ASR, FPR, TPR, Precision, Recall, F1, Specificity, ROC-AUC, PR-AUC (with single-class `None` guard).
  - Retrieval: `Recall@1`, `Recall@5`, `Recall@10`, `MRR`, `nDCG@10`, `supporting_fact_recall`.
  - Verification: Claim accuracy, macro-F1, supported/contradicted precision, `false_supported_rate`, `false_contradicted_rate`, `unsupported_claim_recall`, evidence alignment, citation correctness.
  - Operational: `p50`/`p95`/`p99` (gated on `>= 5` samples), throughput RPS, error rate, timeout rate.
- **Statistical Validation (`src/trustrag/evaluation/statistics/validation.py`):** Wilson score CIs, paired bootstrap 95% CIs (`n=2000`, `seed=42`), exact McNemar test (`scipy.stats.binomtest`), paired Cohen's `d`, Holm-Bonferroni correction, and `exploratory` flag (`n < 30`).
- **Fair Baseline Runners (`src/trustrag/evaluation/baselines/runners.py`):** Evaluates `original_rag`, `static_trustrag`, `adaptive_trustrag` (train-only calibration), `trustrag_no_g1`, `trustrag_no_g2`, `trustrag_no_g3`, and `trustrag_no_srm` on identical records, corpus, and seed.
- **Experiment Harness & CLI (`src/trustrag/evaluation/experiments/phase10_runner.py`, `tools/run_phase10_benchmarks.py`):** Saves immutable `bundle.json`, `summary.md`, and per-example `*.jsonl` files under `reports/phase10_experiments/<experiment_id>/`.
- **Dashboard Integration Decision:** Kept out of scope for Phase 10 to preserve the accepted Phase 09 application and test suite untouched.
