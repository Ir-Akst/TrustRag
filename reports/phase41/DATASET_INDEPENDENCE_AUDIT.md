# Dataset Independence & Effective Sample Size Audit

Audited `Phase 40` vs `Phase 40.1` vs `Phase 41` normalized texts:

| Dataset | P40 / P40.1 / P41 Total | P40 / P40.1 / P41 Unique | Exact Overlap (P40 vs P41) | Exact Overlap (P40.1 vs P41) |
|---|---|---|---|---|
| `g1` | 280 / 300 / 250 | **280 / 300 / 250** | 0 | 0 |
| `firewall` | 150 / 150 / 140 | **21 / 21 / 11** | 0 | 0 |
| `multilingual` | 360 / 360 / 270 | **72 / 72 / 54** | 53 | 53 |
| `g3` | 120 / 140 / 120 | **12 / 12 / 10** | 10 | 10 |

**Critical Audit Finding:** While `g1` and `firewall` have zero cross-phase overlap, `firewall`, `multilingual`, and `g3` exhibit **template cycling** (10–72 unique base prompts cycled to $N=120$–$360$) and `multilingual`/`g3` reuse base prompts across phases. Nominal $N$ overstates independent degrees of freedom.
