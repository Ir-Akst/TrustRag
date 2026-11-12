# TrustRAG Phase 10 — Statistical Analysis Report

**Methods:** Paired bootstrap 95% CIs (`n_resamples=2000`, `seed=42`), exact two-sided McNemar test (`scipy.stats.binomtest`), paired Cohen's `d`, Holm-Bonferroni multiple-comparison adjustment, and `exploratory` flag for `n < 30`.

---

## 1. Adversarial Robustness (`n=40`, Non-Exploratory)

| Comparison | Abs Diff | 95% Bootstrap CI | Raw `p` (McNemar) | Holm-Bonferroni `adj_p` | Cohen's `d` | Interpretation |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `static_trustrag_vs_original_rag` | **+0.2500** | `[0.1250, 0.4000]` | `0.001953` | **0.011718** | `0.5701` | Statistically significant improvement |
| `adaptive_trustrag_vs_original_rag` | **+0.3250** | `[0.1750, 0.4750]` | `0.000244` | **0.001708** | `0.6852` | Statistically significant improvement |
| `trustrag_no_g1_vs_original_rag` | +0.2500 | `[0.1250, 0.4000]` | `0.001953` | `0.011718` | `0.5701` | Significant; G1 not needed for doc attacks |
| `trustrag_no_g2_vs_original_rag` | `0.0000` | `[0.0000, 0.0000]` | `1.000000` | `1.000000` | `0.0000` | No gain without G2 |
| `trustrag_no_g3_vs_original_rag` | +0.2500 | `[0.1250, 0.4000]` | `0.001953` | `0.011718` | `0.5701` | Significant; G2 drives doc detection |
| `trustrag_no_srm_vs_original_rag` | +0.2500 | `[0.1250, 0.4000]` | `0.001953` | `0.011718` | `0.5701` | Significant; fallback SRM not driving G2 |
| `adaptive_vs_static_trustrag` | +0.0750 | `[0.0000, 0.1506]` | `0.250000` | `0.500000` | `0.2812` | Not statistically significant at `n=40` |

---

## 2. Knowledge Poisoning (`n=24`) & Clean RAG (`n=15`) — Exploratory
- **`knowledge_poisoning` (`n=24`, `exploratory=True`):** All comparisons vs `original_rag` yield `diff=0.0000`, `adj_p=1.0` (`adaptive_trustrag` CI `[-0.3333, 0.3333]`).
- **`clean_rag` (`n=15`, `exploratory=True`):** All profiles achieve `1.0000` accuracy (`diff=0.0000`, `adj_p=1.0`).
