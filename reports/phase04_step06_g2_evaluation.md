# TrustRAG Phase 04 — Step 6: G2 Multi-Signal Detector (MSD) Evaluation

**Date:** 2026-11-11  
**Component Evaluated:** `MultiSignalDetector` (`src/trustrag/detection/msd.py`, `src/trustrag/detection/signals.py`)  
**Datasets Evaluated (SYNTHETIC):**
- Active `data/benchmarks/adversarial_robustness/test.jsonl` ($N=4$)
- Backup `data/benchmarks_backup/adversarial_robustness/test.jsonl` ($N=40$) & `val.jsonl` ($N=36$, used exclusively for threshold sensitivity & signal ablation)
- Backup `data/benchmarks_backup/knowledge_poisoning/test.jsonl` ($N=24$)
- Full `data/raw/custom_security/raw_train.jsonl` ($N=2,000$)

---

## 1. Combined 6-Signal Detector Performance (Synthetic Benchmarks)

| Dataset / Split | Docs | Decision Dist. (`CLEAN`/`POISONED`/`UNCERTAIN`) | Strict `POISONED` (P / R / F1 / FPR / FNR) | `POISONED \| UNCERTAIN` (P / R / F1 / FPR) | ROC-AUC | PR-AUC | Brier | ECE | Non-Amp. Violations |
|---|---:|---|---|---|---:|---:|---:|---:|---:|
| Active `adv_test` | 4 | 0 / 0 / 4 | 0.000 / 0.000 / 0.000 / 0.000 / 1.000 | 0.500 / 1.000 / 0.667 / 1.000 | 0.3750 | 0.5000 | 0.3139 | 0.2434 | **0** |
| Backup `adv_test` | 40 | 10 / 10 / 20 | **1.000 / 0.588 / 0.741 / 0.000** / 0.412 | 0.567 / 1.000 / 0.723 / 0.565 | **0.8951** | **0.9000** | **0.1466** | **0.1410** | **0** |
| Backup `kp_test` | 24 | 4 / 4 / 16 | **1.000 / 0.333 / 0.500 / 0.000** / 0.667 | 0.600 / 1.000 / 0.750 / 0.667 | 0.6528 | 0.7354 | — | — | **0** |
| `custom_security` (`raw_train`) | 2,000 | 375 / 375 / 1,250 | **1.000 / 0.429 / 0.600 / 0.000** / 0.571 | 0.538 / 1.000 / 0.700 / 0.667 | **0.7857** | **0.7852** | 0.1822 | 0.1465 | **0** |

### Clean vs. Poisoned Trust Score Distributions
- **Backup `adv_test` ($N=40$):** Clean (`n=23`, incl. `BENIGN_INSTRUCTION_LIKE`) `mean=0.8046` (`std=0.0893`, `p50=0.7539`, `[0.6729, 0.9032]`) vs Poisoned (`n=17`) `mean=0.4818` (`std=0.2246`, `p50=0.3074`, `[0.2648, 0.7838]`).
- **`custom_security` ($N=2,000$):** Clean (`n=1,125`) `mean=0.7774` (`std=0.0989`, `p50=0.7434`) vs Poisoned (`n=875`) `mean=0.5442` (`std=0.2099`, `p50=0.6795`).
- **Clean-Document Rejection:** Across all **1,125 clean & benign-control documents** in `custom_security`, **0** were misclassified as `POISONED` (**0.0000 FPR**). Clean documents with symmetric factual conflicts or benign imperative instructions are routed to `UNCERTAIN` rather than `POISONED`.

---

## 2. Individual Signal Behavior, Heuristic Attribution & FilterRAG Check

| Signal ID | Name | Heuristic? | Availability | Behavior on `backup_adv_test` ($N=40$) | Single-Signal ROC-AUC |
|---|---|---|---:|---|---:|
| **F1** | `perplexity` | No | **0.0%** | Unavailable (`perplexity_backend="disabled"`); never fabricated | — |
| **F2** | `embedding_norm` | No | **0.0%** | Raw L2 norm measured, kept unavailable (`require_configured` baseline policy) | — |
| **F3** | `query_match` | No | 100.0% | `clean_mean=0.3440`, `poisoned_mean=0.3454` | 0.6573 |
| **F4** | `instruction_content` | **Yes (Heuristic)** | 100.0% | `clean_mean=1.0000`, `poisoned_mean=0.4118` | **0.7941** |
| **F5** | `consensus_deviation` | **Yes (Heuristic)** | 100.0% | `clean_mean=0.4978`, `poisoned_mean=0.6206` (penalizes symmetric ties equally) | 0.4233 |
| **F6** | `provenance` | No (Metadata/Priors) | 100.0% | Uniform `0.7500` across synthetic provenance strings (**not** verified source reputation) | 0.5000 |
| **Supp.** | FilterRAG `freq_density` | **Yes (Heuristic)** | 100.0% | When enabled with extractive answer callable: `clean=1.0000`, `poisoned=0.8315` | **0.7059** |

### Leave-One-Signal-Out Ablation (`backup_adv_val`, Validation Split Only, $N=36$)
- Baseline (all active signals F3–F6): `ROC-AUC = 0.7238`, `F1 = 0.5714`
- Drop `F3 (query_match)`: `ROC-AUC = 0.7857`
- Drop `F4 (instruction_content)`: `ROC-AUC = 0.4254` (**-0.2984 drop — dominant threat detector**)
- Drop `F5 (consensus_deviation)`: `ROC-AUC = 0.5651` (**-0.1587 drop — adds separation when paired with F4**)
- Drop `F6 (provenance)`: `ROC-AUC = 0.7238` (0 change under uniform synthetic metadata)

---

## 3. Validation-Only Threshold Sensitivity & Non-Amplifying Invariants

- **Threshold Sweep (`backup_adv_val`, $N=36$, zero `test` tuning):** Varying `poison_threshold` $\in [0.25, 0.75]$ and `trust_threshold` $\in [0.55, 0.85]$ produced identical decisions (`CLEAN=6, POISONED=6, UNCERTAIN=24`, `Strict P/R/F1=(1.0/0.4/0.5714)`) because hard-gate triggers (`instruction_poison_threshold=0.55` and `conflict_detected` / `instruction_flag`) govern decision boundaries on these threat categories. Frozen baseline thresholds (`0.38 / 0.60`) were retained unmodified.
- **Non-Amplifying Missing-Signal Policy Verified:** Across all 2,000+ assessments with F1 & F2 missing, `effective_weight <= configured_weight` and `available_weight_ratio <= 1.0` held with **0 violations**.

---

## 4. Step 6 Acceptance Verdict

- [x] All 6 signals + optional FilterRAG `freq_density` evaluated and heuristic signals explicitly identified.
- [x] Individual signal contributions, combined metrics, calibration (`Brier`, `ECE`), and trust-score distributions computed.
- [x] Threshold sensitivity conducted strictly on validation split (zero test-set tuning).
- [x] Non-amplifying weight scaling and removal cap invariants verified (`0` violations).

**Step 6 Status:** **PASS** — Ready to proceed to Step 7 (G3 Output Evidence Verification Evaluation).

