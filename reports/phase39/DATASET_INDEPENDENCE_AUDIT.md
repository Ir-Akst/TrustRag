# Dataset Provenance & Independence Audit

Executed via `reports/phase39/scripts/audit_dataset_independence.py` comparing normalized texts across Phase 37, Phase 38, and Phase 39.

| Dataset | P37 Count | P38 Count | P39 Count | Unique in P39 | Exact Overlap (P37/P38 vs P39) | Near-Dup Jaccard >= 0.85 |
|---|---|---|---|---|---|---|
| `g1` | 260 | 300 | 330 | **330** | 0 / 0 | 0 / 0 |
| `firewall` | 140 | 150 | 160 | **26** | 0 / 0 | 0 / 0 |
| `multilingual` | 270 | 270 | 360 | **180** | 0 / 0 | 0 / 0 |
| `evidence` | 100 | 100 | 140 | **30** | 0 / 0 | 0 / 0 |

**Honest Disclosure on Effective Sample Sizes:** While Phase 39 has **zero** overlap with Phase 37/38, the `firewall`, `multilingual`, and `evidence` generators cycled over 26, 180, and 30 unique base templates respectively. Both total $N$ and unique template counts are disclosed here to prevent overstated statistical power.
