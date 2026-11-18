# TrustRAG — Track 2, Step 3.19: Final Closure Audit
## 01 — Metric Provenance & Baseline Reconciliation

- **Audit Date:** 2026-11-14T18:05:00Z
- **Auditor:** Independent Research Auditor & Final Evidence-Governance Reviewer

---

### 1. Definitive Provenance of All Baseline Figures

An exhaustive audit of raw disk artifacts was performed to establish the mathematical and empirical origin of every metric reported across Track 2.

| Metric Identifier | Audited Value | Source File & Field | Numerator / Denominator | Category | Independently Reproducible? | Governance Ruling |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Step 3.8 Pre-Training Baseline** | **24.19%** (`0.241923`) | `reports/research_completion/track02_step03_8_nli_training/training_results.json`<br>`initial_metrics.accuracy` | 644 / 2,662 (All samples predicted as NEUTRAL: `[[0,0,1662],[0,0,356],[0,0,644]]`) | Empirically Observed | **Yes** (from confusion matrix) | **Authoritative Step 0 Baseline** |
| **Step 3.8 Post-Training Accuracy** | **24.12%** (`0.241172`) | `reports/research_completion/track02_step03_8_nli_training/training_results.json`<br>`final_metrics.accuracy` | 642 / 2,662 ($0 + 68 + 574 = 642$, `[[0,251,1411],[0,68,288],[0,70,574]]`) | Empirically Observed | **Yes** (from confusion matrix) | **Authoritative Step 3.8 Outcome** |
| **Step 3.16 Step 0 Baseline** | **24.19%** (`0.241923`) | `reports/training_runs/step03_16/training_results.json`<br>`initial_metrics.accuracy` | 644 / 2,662 (All samples predicted as NEUTRAL: `[[0,0,1662],[0,0,356],[0,0,644]]`) | Empirically Observed | **Yes** (from confusion matrix) | **Authoritative Step 0 Baseline** |
| **Step 3.16 Post-Training Accuracy** | **38.05%** (`0.380541`) | `reports/training_runs/step03_16/training_results.json`<br>`final_metrics.accuracy` | 1,013 / 2,662 ($557 + 16 + 440 = 1,013$, `[[557,143,962],[85,16,255],[151,53,440]]`) | Empirically Observed | **Yes** (from confusion matrix) | **Authoritative Step 3.16 Outcome** |
| **Draft Baseline Figure (43.88%)** | **43.88%** (`0.438768`) | Does **NOT** exist in any `training_results.json` on disk. Derived from draft confusion matrix `[[1021,641,0],[209,147,0],[378,266,0]]`. | 1,168 / 2,662 ($1021 + 147 + 0 = 1,168$) | Unverified / Narrative Artifact | **No** (No raw predictions exist) | **PROHIBITED FROM USE** |
| **ENTAILMENT Class Prevalence** | **62.43%** (`0.624343`) | Derived from validation split support: `data/processed/sft_v2/nli/validation.jsonl` | 1,662 / 2,662 | Mathematically Derived | **Yes** | **Trivial Majority-Class Ceiling** |
| **Uniform Random Expectation** | **33.33%** (`0.333333`) | Mathematical expectation for 3 equiprobable classes: $1 / 3$ | 1 / 3 | Mathematically Derived | **Yes** | **Theoretical Chance Baseline** |
| **Prior-Matched Random Expectation** | **46.62%** (`0.466209`) | Theoretical expectation matching validation class priors: $\sum_{i=1}^3 p_i^2 = (0.6243)^2 + (0.1337)^2 + (0.2419)^2$ | N/A ($0.3898 + 0.0179 + 0.0585 = 0.4662$) | Mathematically Derived | **Yes** | **Prior-Weighted Chance Baseline** |

---

### 2. Detailed Findings on Specific Metrics

#### The 43.88% Discrepancy
- In Step 3.16 report drafts and Step 3.17 discussions, a figure of **43.88%** was cited as a "random-head baseline" or "pre-training baseline."
- Inspection of the actual training logs (`training_results.json`) reveals that at Step 0, the model with random classifier head initialization produced a mechanical prediction of class `2` (`NEUTRAL`) for 100% of the 2,662 samples, yielding an actual accuracy of **24.19%** (644/2,662).
- The 43.88% figure matches a hypothetical evaluation table where 1,168 samples were labeled correct ($1021\text{ ENT} + 147\text{ CON} = 1168$). Because no raw prediction logs or checkpoint files substantiate this run, **43.88% is formally classified as unverified**, and its citation in research reports as an empirical baseline is prohibited.

#### The 62.43% vs. 24.12% Discrepancy in Step 3.8
- In earlier reports, Step 3.8 was mistakenly described as having achieved 62.43% accuracy.
- **Root Cause:** 62.43% ($1,662 / 2,662$) represents the proportion of `ENTAILMENT` examples in the validation set. If a model trivially collapsed to always predicting `ENTAILMENT`, it would achieve 62.43%.
- However, Step 3.8 did **not** collapse to `ENTAILMENT`. Due to severe tail-starvation and class imbalance, it collapsed in the opposite direction, predicting 0 `ENTAILMENT`, 389 `CONTRADICTION`, and 2,273 `NEUTRAL`.
- The actual measured accuracy of Step 3.8 was **24.12%** ($642 / 2,662$).

#### Step 3.16 Remediated Pilot Interpretation
- Step 3.16 post-training accuracy is **38.05%** (1,013 / 2,662 correct).
- Compared to the true Step 0 baseline (24.19%), the model gained **+13.86 percentage points**.
- Compared to the collapsed Step 3.8 run (24.12%), the model gained **+13.93 percentage points**.
- Compared to uniform random guessing (33.33%), the model gained **+4.72 percentage points**.
- Compared to prior-matched random guessing (46.62%) and majority-class guessing (62.43%), the model remains **below trivial heuristics**.
- This demonstrates that while the class-balanced sampler prevented degenerative single-class collapse, the 1,000-step pilot was insufficient to achieve functional 3-way NLI discrimination.

