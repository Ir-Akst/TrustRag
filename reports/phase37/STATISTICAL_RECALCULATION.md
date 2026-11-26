# Statistical Recalculation & Discrepancy Resolution

## 1. Resolution of Utility Retention Discrepancy (Phase 35 vs Phase 36)
- **Investigated Discrepancy:** Phase 35 reported 77.78% utility retention while Phase 36 scorecard reported 50.0%.
- **Mathematical Audit Findings:**
  - In Phase 35, the 77.78% figure was the mean retention across ALL 120 documents (80 attacks [mean=66.67%] + 40 benign [mean=100.0%]).
  - In Phase 36, the 61.11% reported in text was the mean across ALL 120 documents (80 attacks [mean=41.67%] + 40 benign [mean=100.0%]).
  - The 50.0% baseline on the Phase 36 scorecard was an erroneous denominator shortcut.
  - In Phase 37 independent evaluation, mean utility retention is **78.61% on attacks (N=90)** and **86.25% across all documents (N=140)**.

## 2. Statistical Confidence Intervals
All proportions are evaluated using 95% two-sided Wilson score intervals. Finite test sample sizes preclude claims of 100% security or 0% leakage in open deployment environments.
