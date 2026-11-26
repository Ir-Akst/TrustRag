# G3 Evidence Verification Reliability Report

**Holdout Dataset:** `reports/phase40/datasets/holdout_g3.jsonl` ($N=120$).

- **Overall Gate Accuracy:** **100.00%** (120/120) [95% CI: 96.90%, 100.00%]
- **Supported Acceptance:** **100.00%** (30/30) [95% CI: 88.65%, 100.00%]
- **False Abstention:** **0.00%** (0/30) [95% CI: 0.00%, 11.35%]
- **Contradiction Recall:** **100.00%** (55/55) [95% CI: 93.47%, 100.00%]
- **Unsupported Leakage:** **0.00%** (0/20) [95% CI: 0.00%, 16.11%]
- **Partially Supported Leakage:** **0.00%** (0/15)

Hardcoded `_GEO_COMPAT` and entity literals (`toronto`, `newton`, `venus`, `jefferson`) were completely removed and replaced with general functional-role, polarity, and tolerance-aware numerical reasoning.
