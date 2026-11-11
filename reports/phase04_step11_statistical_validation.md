# TrustRAG Phase 04 — Step 11: Statistical Validation Report

**Date:** 2026-11-11  
**Methodology:** Exact binomial McNemar's test (paired binary outcomes), Wilson score 95% CIs (binomial proportions), percentile bootstrap 95% CIs (`n_boot=2000`, `seed=42`), Mann-Whitney $U$ test (non-normal trust scores), paired permutation test (`n_perm=5000`) + Cohen's $d$ (continuous latencies), Holm-Bonferroni multiple-comparison adjustment ($\alpha = 0.05$), and multi-seed sensitivity (`seeds = [42, 123, 999]`).

---

## 1. 95% Confidence Intervals (Wilson Score & Bootstrap)

| Metric & Dataset | Source | $N$ | Point Estimate | 95% CI |
|---|---|---:|---:|---|
| Clean RAG `Recall@5` (Original RAG, BoolQ) | **Real** | 100 | `0.9000` | `[0.8256, 0.9448]` |
| Clean RAG `Recall@5` (TrustRAG, BoolQ) | **Real** | 100 | `0.8200` | `[0.7333, 0.8830]` |
| Threat Prevention (`E1` Original RAG) | **Synthetic** | 43 | `0.3721` | `[0.2438, 0.5214]` |
| Threat Prevention (`E7` Full TrustRAG) | **Synthetic** | 43 | **`0.9070`** | `[0.7840, 0.9632]` |
| G1 Recall (`custom_security` threat families) | **Synthetic** | 375 | `1.0000` | `[0.9899, 1.0000]` |
| G1 False Positive Rate (BoolQ real queries) | **Real** | 100 | `0.0000` | `[0.0000, 0.0370]` |
| G3 3-Class Accuracy (`hallucination`) | **Real Bench** | 11 | `0.2727` | `[0.0975, 0.5656]` |
| G3 False Support Rate (`hallucination` non-supported) | **Real Bench** | 6 | `0.0000` | `[0.0000, 0.3903]` |
| G3 Linguistic & Regression Pass Rate | **Spec Fixtures** | 25 | `1.0000` | `[0.8668, 1.0000]` |
| G2 Clean Trust Score Mean (`custom_security`) | **Synthetic** | 1,125 | `0.7774` | `[0.7718, 0.7833]` (Boot) |
| G2 Poisoned Trust Score Mean (`custom_security`) | **Synthetic** | 875 | `0.5442` | `[0.5300, 0.5581]` (Boot) |
| Latency Mean (`Original RAG`, BoolQ) | **Real** | 100 | `6.24 ms` | `[6.08, 6.38] ms` (Boot) |
| Latency Mean (`Full TrustRAG`, BoolQ) | **Real** | 100 | `23.90 ms` | `[22.02, 25.82] ms` (Boot) |

---

## 2. Paired Hypothesis Tests & Multiple-Comparison Control (Holm-Bonferroni)

| Hypothesis Test | Method | Test Statistic / Discordant Pairs | Raw $p$-value | Holm-Adjusted $p$ | Significant ($\alpha=0.05$)? |
|---|---|---|---:|---:|:---:|
| **Security Improvement (`E7` vs `E1`, $N=43$)** | McNemar (Exact Binomial) | $b=0, c=23$ ($23$ discordant) | $< 10^{-6}$ | $< 10^{-6}$ | **YES** |
| **G2 Clean > Poisoned Trust (`custom_security`, $N=2000$)** | Mann-Whitney $U$ | $U = 773,437.5$ | $1.12 \times 10^{-107}$ | $1.12 \times 10^{-107}$ | **YES** |
| **E2E Latency Increase (`TrustRAG` vs `Orig`, $N=100$)** | Paired Permutation ($5000$) | $\Delta = +17.67\text{ ms}$, Cohen's $d = 1.9492$ | `0.0002` | `0.0004` | **YES** |
| **Clean `Recall@5` Drop (`TrustRAG` vs `Orig`, $N=100$)** | McNemar (Exact Binomial) | $b=9, c=1$ ($10$ discordant) | `0.0215` | `0.0215` | **YES** |

---

## 3. Sample Size, Imbalance, and Seed Sensitivity Assessment

1. **Random Seed Sensitivity (`seeds = [42, 123, 999]`):** Identical metrics observed across all 3 seeds (`clean_rag` `P@1=0.7333`, `MRR=0.7667`; `knowledge_poisoning` `ASR=0.6667`), confirming 100% deterministic execution.
2. **Sample Size Constraints (Honest Disclosure):**
   - `data/benchmarks/hallucination` ($N=11$, non-supported $N=6$) yields wide Wilson 95% CIs (`[0.0975, 0.5656]` accuracy; `[0.0000, 0.3903]` FSR). Statistical claims on G3 must rely on the combined linguistic/spec suites rather than $N=11$ alone.
   - `data/benchmarks/` active `test` splits ($N=2\text{--}4$) are too small for standalone statistical significance; paired tests above used the larger preserved Phase 02 splits ($N=43$, $N=100$, $N=2,000$).
3. **Dataset Imbalance:** In `custom_security` G2 evaluation ($N=2,000$), `BENIGN_INSTRUCTION_LIKE` (250 items) are benign controls, creating a 1,125 clean vs. 875 poisoned ratio (`1.29:1`), handled appropriately via Mann-Whitney $U$ and PR-AUC/ROC-AUC alongside F1.
4. **Statistically Significant Utility Tradeoff:** The `-8.0 pp` `Recall@5` reduction (`0.90` $\rightarrow$ `0.82`) on 100 real BoolQ queries is statistically significant ($p=0.0215$) and reflects `trust_weight=0.45` re-ranking displacement rather than random noise.

---

## 4. Step 11 Acceptance Verdict

- [x] Appropriate paired and non-parametric statistical tests applied and justified.
- [x] Sample counts, 95% CIs, effect sizes, Holm-Bonferroni corrections, and seed sensitivity computed.
- [x] Small-sample limitations (`N=11` hallucination, `N=2-4` truncated active test splits) explicitly acknowledged.

**Step 11 Status:** **PASS** — Ready to proceed to Step 12 (Independent Phase 04 Acceptance Audit & Final Reports).

