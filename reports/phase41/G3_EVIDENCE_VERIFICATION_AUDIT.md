# Independent G3 Evidence-Grounded Verification Audit

**Dataset:** `reports/phase41/datasets/p41_g3_holdout.jsonl` ($N=120$: 30 `SUPPORTED`, 20 `PARTIALLY_SUPPORTED`, 25 `INSUFFICIENT_EVIDENCE`, 45 `CONTRADICTED`).

- **Release-Gate Accuracy:** **100.00%** (120/120) [95% CI: 96.90%, 100.00%]
- **Exact 4-Class Status Accuracy:** **90.00%** (108/120) [95% CI: 83.33%, 94.19%]
- **Supported Acceptance:** **100.00%** (30/30) | **False Abstention:** **0.00%** (0/30)
- **Contradiction Recall:** **100.00%** (45/45) [95% CI: 92.13%, 100.00%]
- **Unsupported Leakage:** **0.00%** (0/25) [95% CI: 0.00%, 13.32%]
- **4-Class Breakdown:** `supported` 30/30, `partially_supported` 20/20, `geo/entity/numerical/implicit` contradictions 45/45, `unsupported` 13/25 `INSUFFICIENT_EVIDENCE` (12/25 still classified `CONTRADICTED`).
