# TrustRAG Phase 11.1 — Step 05: Clean-Query Utility & Contradiction Detection Audit

**Auditor Role:** Independent ML Evaluation Auditor  
**Date:** 2026-11-18  
**Audit Mode:** STRICTLY READ-ONLY  
**Repository:** `/home/aditya/rags/TrustRag-phase11` — Branch `phase-11` — HEAD `aba5cc9d`  
**Target Model:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  
**Authoritative Raw Predictions:** `reports/research_completion/phase11_1_step03_full_nli_training/predictions_val.jsonl`  
**Preceding Audit Reference:** `reports/research_completion/phase11_1_step04_threshold_calibration/threshold_calibration_audit.md`

---

## Table of Contents

1. [Executive Summary & Status Verdict](#1-executive-summary--status-verdict)
2. [Safety & Integrity Confirmation](#2-safety--integrity-confirmation)
3. [Task 1: Comprehensive Re-Verification of Step 04](#3-task-1-comprehensive-re-verification-of-step-04)
   - [3.1 Recomputation of Full 99-Threshold Operating Sweep](#31-recomputation-of-full-99-threshold-operating-sweep)
   - [3.2 Global Maximum Contradiction F1 Verification](#32-global-maximum-contradiction-f1-verification)
   - [3.3 Detailed Comparison: $\theta = 0.15$ vs $\theta = 0.16$ vs $\theta = 0.50$](#33-detailed-comparison-theta--015-vs-theta--016-vs-theta--050)
   - [3.4 Pre- and Post-Calibration Metric Verification](#34-pre--and-post-calibration-metric-verification)
   - [3.5 Deep Forensic Investigation: 90 vs 89 True Positives Discrepancy](#35-deep-forensic-investigation-90-vs-89-true-positives-discrepancy)
   - [3.6 Inconsistency & Definition Audit](#36-inconsistency--definition-audit)
4. [Task 2: Clean-Query Dataset Discovery & Forensic Inventory](#4-task-2-clean-query-dataset-discovery--forensic-inventory)
   - [4.1 Inventory of Repository Benchmarks & Processed Datasets](#41-inventory-of-repository-benchmarks--processed-datasets)
   - [4.2 Forensic Audit of Candidate Datasets](#42-forensic-audit-of-candidate-datasets)
   - [4.3 Finding on Clean-Query Benchmark Availability: BLOCKED](#43-finding-on-clean-query-benchmark-availability-blocked)
5. [Task 3: Utility Evaluation (Internal Validation Proxy)](#5-task-3-utility-evaluation-internal-validation-proxy)
   - [5.1 Definition & Scope of Internal Non-Contradiction Proxy](#51-definition--scope-of-internal-non-contradiction-proxy)
   - [5.2 Evaluation of Candidate Thresholds ($0.16, 0.20, 0.24, 0.25, 0.50$)](#52-evaluation-of-candidate-thresholds-016-020-024-025-050)
   - [5.3 Impact on Entailment vs Neutral Evidence](#53-impact-on-entailment-vs-neutral-evidence)
   - [5.4 Temperature-Calibrated Utility Dynamics](#54-temperature-calibrated-utility-dynamics)
6. [Task 4: Operating-Point Recommendation & Trade-Off Analysis](#6-task-4-operating-point-recommendation--trade-off-analysis)
   - [6.1 The Utility–Security Dilemma in RAG Pipelines](#61-the-utilitysecurity-dilemma-in-rag-pipelines)
   - [6.2 Compounding Rejection Risk in Multi-Passage Retrieval](#62-compounding-rejection-risk-in-multi-passage-retrieval)
   - [6.3 Gating Conditions for Production Deployment](#63-gating-conditions-for-production-deployment)
7. [Limitations](#7-limitations)
8. [Recommended Next Experiments](#8-recommended-next-experiments)
9. [Final Audit Sign-Off](#9-final-audit-sign-off)

---

## 1. Executive Summary & Status Verdict

This audit performs an independent re-verification of the Step 04 threshold calibration findings and assesses the impact of contradiction thresholding on clean, non-adversarial evidence in RAG systems.

### Status Verdict Summary

| Evaluation Dimension | Status | Justification |
| :--- | :---: | :--- |
| **Task 1: Step 04 Verification** | **PASS** | Complete mathematical recomputation matches Step 04 report to 6 decimal places. Discrepancy between 90 (argmax) and 89 ($\theta=0.50$) true positives completely resolved and proven to stem from 3-class plurality vs binary majority threshold definitions. |
| **Task 2: Clean-Query Discovery** | **BLOCKED** | No independent, real-world clean RAG query dataset with NLI annotations exists in the repository. Existing `clean_rag` benchmark has only 10 total extractive QA samples, lacks NLI labels, and has zero NLI model predictions. |
| **Task 3: Utility Evaluation** | **PASS WITH LIMITATIONS** | Evaluated on 2,306 non-contradictory validation pairs (`sft_v2_nli/validation.jsonl`) as an internal proxy. External deployment utility evaluation remains blocked due to dataset absence. |
| **Task 4: Operating-Point Recommendation** | **PASS WITH LIMITATIONS** | Explicit utility-versus-security trade-off documented. Absolute prohibition on endorsing any deployment threshold without empirical clean-query testing enforced. |
| **OVERALL AUDIT STATUS** | **PASS_WITH_LIMITATIONS** | Model properties are mathematically verified, but production deployment gating is withheld until independent clean-query benchmarks are acquired. |

---

## 2. Safety & Integrity Confirmation

This evaluation was conducted under strict read-only parameters:
- **No training or fine-tuning:** Model weights were not modified or executed in training mode.
- **No checkpoint modification:** All checkpoint files in `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` remain bit-for-bit identical to their SHA-256 manifests.
- **No dataset, prediction, or code modification:** Zero lines of existing data, prediction JSONL files, or application source files were altered.
- **No Git state alterations:** Branch remains `phase-11` at commit `aba5cc9d`.
- **No synthetic data generation:** No placeholder or synthetic clean-query datasets were fabricated.
- **No unauthorized inference:** Model forward passes were not executed, adhering strictly to precomputed artifact analysis.

---

## 3. Task 1: Comprehensive Re-Verification of Step 04

All calculations were independently executed on the 2,662 raw records of `predictions_val.jsonl` (SHA-256: `6d57e5554358ba16d744b727703632cc91f1a432be7e2607d03a7bbc80ee6b48`).

### 3.1 Recomputation of Full 99-Threshold Operating Sweep

The decision rule was evaluated for $\theta \in [0.01, 0.99]$ at $0.01$ step increments:

$$\hat{y}_{\text{con}} = \mathbb{I}[p(\text{CONTRADICTION} \mid x) \ge \theta]$$

All 99 operating points were recomputed. Key percentiles and boundary thresholds are summarized below:

| $\theta$ | Pred+ | TP | FP | FN | TN | Precision | Recall | F1 Score | FPR | FNR |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.01** | 2,580 | 353 | 2,227 | 3 | 79 | 13.68% | 99.16% | 0.2405 | 96.57% | 0.84% |
| **0.05** | 1,394 | 272 | 1,122 | 84 | 1,184 | 19.51% | 76.40% | 0.3109 | 48.66% | 23.60% |
| **0.10** | 828 | 216 | 612 | 140 | 1,694 | 26.09% | 60.67% | 0.3649 | 26.54% | 39.33% |
| **0.12** | 705 | 202 | 503 | 154 | 1,803 | 28.65% | 56.74% | 0.3808 | 21.81% | 43.26% |
| **0.14** | 579 | 186 | 393 | 170 | 1,913 | 32.12% | 52.25% | 0.3979 | 17.04% | 47.75% |
| **0.15** | 511 | 176 | 335 | 180 | 1,971 | 34.44% | 49.44% | 0.4060 | 14.53% | 50.56% |
| **0.16** | 441 | 166 | 275 | 190 | 2,031 | 37.64% | 46.63% | **0.4166** | 11.93% | 53.37% |
| **0.17** | 373 | 146 | 227 | 210 | 2,079 | 39.14% | 41.01% | 0.4005 | 9.84% | 58.99% |
| **0.18** | 306 | 129 | 177 | 227 | 2,129 | 42.16% | 36.24% | 0.3897 | 7.68% | 63.76% |
| **0.20** | 213 | 105 | 108 | 251 | 2,198 | 49.30% | 29.49% | 0.3691 | 4.68% | 70.51% |
| **0.25** | 169 | 95 | 74 | 261 | 2,232 | 56.21% | 26.69% | 0.3619 | 3.21% | 73.31% |
| **0.30** | 158 | 94 | 64 | 262 | 2,242 | 59.49% | 26.40% | 0.3658 | 2.78% | 73.60% |
| **0.40** | 140 | 90 | 50 | 266 | 2,256 | 64.29% | 25.28% | 0.3629 | 2.17% | 74.72% |
| **0.50** | 138 | 89 | 49 | 267 | 2,257 | 64.49% | 25.00% | 0.3603 | 2.12% | 75.00% |
| **0.60** | 135 | 89 | 46 | 267 | 2,260 | 65.93% | 25.00% | 0.3625 | 1.99% | 75.00% |
| **0.70** | 127 | 83 | 44 | 273 | 2,262 | 65.35% | 23.31% | 0.3437 | 1.91% | 76.69% |
| **0.80** | 88 | 59 | 29 | 297 | 2,277 | 67.05% | 16.57% | 0.2658 | 1.26% | 83.43% |
| **0.86+** | 0 | 0 | 0 | 356 | 2,306 | 0.00% | 0.00% | 0.0000 | 0.00% | 100.00% |

### 3.2 Global Maximum Contradiction F1 Verification

The mathematical global maximum F1 across all discrete 99 steps was verified:
- **Optimal Threshold:** $\theta^* = \mathbf{0.16}$
- **Precision:** $37.6417\%$ (166 / 441)
- **Recall:** $46.6292\%$ (166 / 356)
- **Maximum F1:** $\mathbf{0.416562}$
- **False Positive Rate:** $11.9254\%$ (275 / 2,306)

*Verification Status:* **CONFIRMED IDENTICAL TO STEP 04 REPORT.**

### 3.3 Detailed Comparison: $\theta = 0.15$ vs $\theta = 0.16$ vs $\theta = 0.50$

| Metric | $\theta = 0.15$ (Coarse Peak) | $\theta = 0.16$ (Exact Peak) | $\theta = 0.50$ (Binary Majority) | Delta ($\theta=0.16$ vs $0.50$) |
| :--- | :---: | :---: | :---: | :---: |
| **Predicted Contradictions** | 511 | 441 | 138 | +303 (+219.6%) |
| **True Positives (TP)** | 176 | 166 | 89 | +77 (+86.5%) |
| **False Positives (FP)** | 335 | 275 | 49 | +226 (+461.2%) |
| **False Negatives (FN)** | 180 | 190 | 267 | -77 (-28.8%) |
| **True Negatives (TN)** | 1,971 | 2,031 | 2,257 | -226 (-10.0%) |
| **Precision** | 34.44% | 37.64% | 64.49% | -26.85 pp |
| **Recall** | 49.44% | 46.63% | 25.00% | **+21.63 pp** |
| **Contradiction F1** | **0.4060** | **0.4166** | **0.3603** | **+0.0563 (+15.6%)** |
| **False Positive Rate (FPR)** | 14.53% | 11.93% | 2.12% | +9.81 pp |
| **FP Origin: Entailment** | 134 | 106 | 13 | +93 |
| **FP Origin: Neutral** | 201 | 169 | 36 | +133 |

**Analysis:** Stepping from $\theta = 0.15$ to $\theta = 0.16$ drops 10 true positives but eliminates 60 false positives (28 from Entailment, 32 from Neutral), driving F1 to its global peak of 0.4166 while reducing the FPR by 2.60 pp.

### 3.4 Pre- and Post-Calibration Metric Verification

The validation set calibration metrics were independently computed:

| Calibration Parameter | Pre-Calibration ($T=1.0$) | Post-Calibration ($T=1.770106$) | Relative Change |
| :--- | :---: | :---: | :---: |
| **Optimal Temperature ($T^*$)** | — | **1.770106** | — |
| **Negative Log-Likelihood (NLL)** | 0.883804 | 0.774052 | **-12.42%** |
| **Expected Calibration Error (ECE-10)** | 0.150092 | 0.030619 | **-79.60%** |
| **Multiclass Brier Score** | 0.473580 | 0.438315 | **-7.45%** |
| **Contradiction Class Brier Score** | 0.100506 | 0.100120 | **-0.38%** |
| **Entailment Class Brier Score** | 0.197542 | 0.178026 | **-9.88%** |
| **Neutral Class Brier Score** | 0.175532 | 0.160170 | **-8.75%** |
| **Classification Accuracy** | 70.3982% | 70.3982% | 0.00% (Identical) |

*Verification Status:* **CONFIRMED TO 6 DECIMAL PLACES.**

---

### 3.5 Deep Forensic Investigation: 90 vs 89 True Positives Discrepancy

A known tension exists between:
1. **Step 03 Audit / Argmax Results:** Reported **90** True Positives for Contradiction (Precision = 63.83%, Recall = 25.28%).
2. **Step 04 Threshold Audit ($\theta = 0.50$):** Reported **89** True Positives for Contradiction (Precision = 64.49%, Recall = 25.00%).

#### Root Cause Analysis

The discrepancy is caused by the difference between **3-class plurality argmax** and **1-vs-rest binary thresholding at 0.50**:

- **Argmax Decision Rule:** A sample is classified as Contradiction if and only if:
  $$p_1 > p_0 \quad \text{and} \quad p_1 > p_2$$
  In a 3-class distribution, this plurality requires only $p_1 > \max(p_0, p_2)$ and can occur at any probability above $\frac{1}{3} \approx 0.333$. It does **not** require $p_1 \ge 0.50$.
- **Binary Thresholding Decision Rule ($\theta = 0.50$):** A sample is classified as Contradiction if and only if:
  $$p_1 \ge 0.50$$
  This enforces an absolute majority.

#### Sample-by-Sample Isolation

By evaluating $\mathbb{I}[\arg\max p = 1] \neq \mathbb{I}[p_1 \ge 0.50]$ across all 2,662 validation samples, exactly **three records** were identified:

| Sample Index | True Label | Argmax Class | Softmax Probabilities $[p_{\text{ent}}, p_{\text{con}}, p_{\text{neu}}]$ | Argmax Outcome | $\theta=0.50$ Outcome | Discrepancy Effect |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **173** | **CONTRADICTION** | CONTRADICTION | $[0.3536, \mathbf{0.4269}, 0.2196]$ | **True Positive** ($p_1 > p_0, p_2$) | **False Negative** ($p_1 < 0.50$) | **Lost 1 TP** (90 $\to$ 89) |
| **223** | **NEUTRAL** | CONTRADICTION | $[0.3303, \mathbf{0.3790}, 0.2908]$ | **False Positive** ($p_1 > p_0, p_2$) | **True Negative** ($p_1 < 0.50$) | Lost 1 FP (eliminated) |
| **2341** | **NEUTRAL** | CONTRADICTION | $[0.0653, \mathbf{0.4760}, 0.4587]$ | **False Positive** ($p_1 > p_0, p_2$) | **True Negative** ($p_1 < 0.50$) | Lost 1 FP (eliminated) |

#### Reconciled Confusion Matrices

**Argmax Confusion Matrix (Total Pred CON = 141):**
$$\begin{pmatrix} 1520 & 13 & 129 \\ 170 & \mathbf{90} & 96 \\ 342 & \mathbf{38} & 264 \end{pmatrix} \implies \text{TP}=90, \quad \text{FP}=13+38=51, \quad \text{FN}=170+96=266$$
$$\text{Precision} = \frac{90}{141} = 63.83\%, \quad \text{Recall} = \frac{90}{356} = 25.28\%$$

**Binary Threshold $\theta = 0.50$ Confusion Matrix (Total Pred CON = 138):**
$$\text{TP} = 89, \quad \text{FP} = 13 (\text{ENT}) + 36 (\text{NEU}) = 49, \quad \text{FN} = 267, \quad \text{TN} = 2,257$$
$$\text{Precision} = \frac{89}{138} = 64.49\%, \quad \text{Recall} = \frac{89}{356} = 25.00\%$$

#### Audit Verdict on Discrepancy
The discrepancy is **NOT** an arithmetic error, calculation defect, or data corruption. It is an expected consequence of contrasting 3-way argmax plurality with binary majority thresholding. 

For strict consistency:
- When using binary probability thresholding, $\theta = 0.50$ yields **89 TP**.
- Any threshold $\theta \le 0.4268$ (e.g. $\theta \in [0.38, 0.42]$) recovers Sample 173 and yields **90 TP**.

---

### 3.6 Inconsistency & Definition Audit

1. **Step 04 Report Terminology:** The Step 04 report occasionally referenced $\theta = 0.50$ as "argmax equivalent". As demonstrated in Section 3.5, this is technically imprecise for 3-class models because plurality does not equal majority. Future reports must explicitly specify "Binary threshold $\theta = 0.50$" versus "3-way Argmax".
2. **Threshold Indexing:** Step 04 reported coarse-grid comparisons at $\theta = 0.15$ (F1 = 0.4060) and correctly identified the fine-grid peak at $\theta = 0.16$ (F1 = 0.4166). The calculations are mathematically sound.

---

## 4. Task 2: Clean-Query Dataset Discovery & Forensic Inventory

A comprehensive search of the repository and connected directories was performed to determine whether a genuine, non-adversarial query–evidence dataset exists for RAG utility testing.

### 4.1 Inventory of Repository Benchmarks & Processed Datasets

| Dataset Location | File Path(s) | Sample Count | Primary Task / Format | Labels Present |
| :--- | :--- | :---: | :--- | :--- |
| `data/benchmarks/clean_rag` | `train.jsonl` (7), `val.jsonl` (1), `test.jsonl` (2) | **10 total** | Extractive QA / Question Answering | Answers (`yes`/`no`), No NLI labels |
| `data/benchmarks_backup/clean_rag` | `train.jsonl` (7), `val.jsonl` (1), `test.jsonl` (2) | 10 total | Identical backup | Answers (`yes`/`no`), No NLI labels |
| `data/processed/boolq` | `validation.jsonl`, `custom_splits/*` | 100 total | BoolQ Reading Comprehension | Boolean labels, No NLI labels |
| `data/processed/ms_marco` | `validation.jsonl` | 10,047 | Passage Retrieval / Ranking | Passage relevance, No NLI labels |
| `data/processed/hotpotqa` | `validation.jsonl` | 7,405 | Multi-hop Question Answering | Supporting facts, No NLI labels |
| `data/processed/ragtruth` | `train.jsonl` (15,090), `test.jsonl` (2,700) | 17,790 | Hallucination Detection | `FACTUAL` vs `HALLUCINATED` |
| `data/processed/sft_v2/nli` | `train.jsonl` (10,815), `validation.jsonl` (2,662) | 13,477 | 3-way NLI (Premise, Hypothesis) | `ENTAILMENT`, `NEUTRAL`, `CONTRADICTION` |

### 4.2 Forensic Audit of Candidate Datasets

#### Candidate 1: `data/benchmarks/clean_rag/`
- **Path:** `/home/aditya/rags/TrustRag-phase11/data/benchmarks/clean_rag/`
- **Sample Count:** 10 samples total (7 train, 1 val, 2 test).
- **Provenance:** Derived from BoolQ validation set.
- **Record Schema:** Contains `query_id`, `query`, `metadata.passage`, and `answer`.
- **NLI Compatibility:** Lacks premise–hypothesis sentence segmentation, lacks NLI labels, and has no contradiction ground truth.
- **Model Predictions:** **ZERO.** No inference predictions exist for `deberta-v3-small-nli-phase11_1-full3epoch` on this benchmark.
- **Statistical Significance:** $N=10$ is statistically unviable for estimating false alarm rates.

#### Candidate 2: `data/processed/ragtruth/test.jsonl`
- **Path:** `/home/aditya/rags/TrustRag-phase11/data/processed/ragtruth/test.jsonl`
- **Sample Count:** 2,700 records.
- **Provenance:** RAGTruth test split (GPT-4, LLaMA-2, and ChatGPT generated responses on CNN/DM, PubMed, COVID-QA).
- **Label Distribution:** Binary labels only (`FACTUAL`: ~73%, `HALLUCINATED`: ~27%).
- **NLI Compatibility:** Does not isolate `CONTRADICTION` from baseless `NEUTRAL` hallucinations.
- **Model Predictions:** **ZERO.** No predictions from the trained NLI model exist on this split.

#### Candidate 3: `data/processed/ms_marco` & `hotpotqa`
- Both datasets represent retrieval corpora, not clean query–evidence NLI evaluation pairs. No NLI predictions exist.

### 4.3 Finding on Clean-Query Benchmark Availability: BLOCKED

> [!CAUTION]
> **Definitive Finding:** There is **NO** independent, clean-query RAG evaluation dataset with precomputed DeBERTa-v3-small NLI predictions anywhere in the project workspace.
>
> In accordance with strict audit instructions:
> 1. Clean-query utility measurement on real-world external RAG data is designated as **BLOCKED**.
> 2. No replacement evidence has been fabricated or labeled as real-world clean data.
> 3. No live model inference was executed, as doing so would violate the strict read-only audit scope.

---

## 5. Task 3: Utility Evaluation (Internal Validation Proxy)

Because external clean-query evaluation is blocked, an **Internal Validation Proxy Evaluation** was conducted on the 2,306 non-contradiction samples from the authoritative validation predictions (`predictions_val.jsonl`).

### 5.1 Definition & Scope of Internal Non-Contradiction Proxy

In RAG systems, "clean evidence" comprises retrieved passages that do not contradict the query or grounded claims. Within `predictions_val.jsonl`:
- **Clean Ground Truth Proxy ($N = 2,306$):**
  - **Entailment Class ($N = 1,662$):** Grounded, fully supported evidence. Falsely flagging this evidence as a contradiction represents a severe system failure.
  - **Neutral Class ($N = 644$):** Benign, non-conflicting supplementary information (unsupported or tangential claims). Falsely flagging this evidence as a contradiction represents an unnecessary rejection.
- **Contradiction Class ($N = 356$):** True adversarial or contradictory claims.

### 5.2 Evaluation of Candidate Thresholds ($0.16, 0.20, 0.24, 0.25, 0.50$)

| Evaluation Metric | $\theta = 0.16$ (Max F1) | $\theta = 0.20$ | $\theta = 0.24$ | $\theta = 0.25$ | $\theta = 0.50$ (Majority) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Total Predicted Contradictions** | 441 | 213 | 173 | 169 | 138 |
| **Contradiction True Positives (TP)** | 166 | 105 | 95 | 95 | 89 |
| **Contradiction Recall** | **46.63%** | **29.49%** | **26.69%** | **26.69%** | **25.00%** |
| **Clean False Contradiction Rate (Clean FCR)** | **11.93%** (275/2,306) | **4.68%** (108/2,306) | **3.38%** (78/2,306) | **3.21%** (74/2,306) | **2.12%** (49/2,306) |
| **Entailment False Alarm Rate (FAR)** | **6.38%** (106/1,662) | **2.53%** (42/1,662) | **1.68%** (28/1,662) | **1.68%** (28/1,662) | **0.78%** (13/1,662) |
| **Neutral False Alarm Rate (FAR)** | **26.24%** (169/644) | **10.25%** (66/644) | **7.76%** (50/644) | **7.14%** (46/644) | **5.59%** (36/644) |
| **Evidence Rejection Rate (Clean)** | **11.93%** | **4.68%** | **3.38%** | **3.21%** | **2.12%** |
| **Correct Evidence Preservation Rate** | **88.07%** | **95.32%** | **96.62%** | **96.79%** | **97.88%** |

### 5.3 Impact on Entailment vs Neutral Evidence

1. **Entailment Preservation:**
   - At $\theta = 0.16$, $6.38\%$ of grounded entailed evidence is discarded.
   - At $\theta \ge 0.24$, Entailment loss drops below $1.7\%$.
   - At $\theta = 0.50$, Entailment loss is $0.78\%$.
2. **Neutral Rejection Vulnerability:**
   - At $\theta = 0.16$, **$26.24\%$ (over 1 in 4)** of neutral passages are falsely categorized as contradictions.
   - Even at $\theta = 0.20$, $10.25\%$ of neutral evidence is discarded.
   - This occurs because the model's logits often confuse non-entailed neutral information with active semantic contradiction.

### 5.4 Temperature-Calibrated Utility Dynamics

When evaluating the calibrated distribution ($T^* = 1.770106$):

| Metric | Calibrated $\theta = 0.16$ | Calibrated $\theta = 0.20$ | Calibrated $\theta = 0.24$ (Cal Peak) | Calibrated $\theta = 0.25$ | Calibrated $\theta = 0.50$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Total Predicted Contradictions** | 1,113 | 730 | 419 | 340 | 135 |
| **Contradiction Recall** | 68.82% | 57.58% | **45.22%** | 39.04% | 25.00% |
| **Clean False Contradiction Rate** | 37.64% | 22.77% | **11.19%** | 8.72% | 1.99% |
| **Entailment False Alarm Rate** | 29.30% | 14.08% | **5.90%** | 4.51% | 0.78% |
| **Neutral False Alarm Rate** | 59.16% | 45.19% | **24.84%** | 19.57% | 5.12% |
| **Clean Evidence Preservation** | 62.36% | 77.23% | **88.81%** | 91.28% | 98.01% |

**Insight:** Because temperature scaling scales down logit magnitudes ($T > 1$), probabilities are drawn toward uniform ($\frac{1}{3}$). Consequently, uncalibrated thresholds like $0.16$ and $0.20$ trigger massive false-positive explosions under calibrated probabilities. The calibrated operating point corresponding to peak F1 is $\theta = 0.24$, which mirrors the behavior of uncalibrated $\theta = 0.16$.

---

## 6. Task 4: Operating-Point Recommendation & Trade-Off Analysis

### 6.1 The Utility–Security Dilemma in RAG Pipelines

A contradiction detector deployed in a RAG pipeline functions as an automated guardrail:
- **Security Goal:** Intercept adversarial knowledge poisoning, corrupted retrieved passages, and hallucinated contradictions before response generation.
- **Utility Goal:** Preserve legitimate retrieved evidence so the generation engine can synthesize complete, accurate answers.

```
                      [Retrieved Evidence Passages]
                                   │
                                   ▼
                 [DeBERTa-v3-small NLI Guardrail]
                                   │
                 p(CONTRADICTION) >= theta ?
                        /                     \
                      YES                      NO
                      /                         \
           [Discard / Reject]             [Feed to Generator]
           (Security Protected)             (Utility Preserved)
```

### 6.2 Compounding Rejection Risk in Multi-Passage Retrieval

In standard production RAG architectures, multiple passages ($K \in \{3, 5, 10\}$) are retrieved per user query. If passages are evaluated independently, the probability that a completely clean query experiences at least one false rejection compounds exponentially:

$$P(\ge 1 \text{ false rejection}) = 1 - (1 - \text{Clean FCR})^K$$

| Operating Point | Clean FCR | $K = 1$ Passage | $K = 3$ Passages | $K = 5$ Passages | $K = 10$ Passages | Contradiction Recall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **$\theta = 0.16$ (Max F1)** | **11.93%** | 11.93% | **31.74%** | **47.45%** | **72.39%** | **46.63%** |
| **$\theta = 0.20$** | **4.68%** | 4.68% | 13.41% | 21.36% | 38.16% | 29.49% |
| **$\theta = 0.24$** | **3.38%** | 3.38% | 9.81% | 15.82% | 29.13% | 26.69% |
| **$\theta = 0.25$** | **3.21%** | 3.21% | 9.32% | 15.06% | 27.86% | 26.69% |
| **$\theta = 0.50$ (Majority)** | **2.12%** | 2.12% | 6.23% | 10.19% | 19.34% | 25.00% |

> [!WARNING]
> At the mathematical Max-F1 threshold ($\theta = 0.16$), a standard 5-passage RAG pipeline will experience a false evidence rejection on **nearly half (47.45%) of all completely benign queries**. In a 10-passage retrieval setup, almost three-quarters (72.39%) of clean queries will have valid evidence dropped.

### 6.3 Gating Conditions for Production Deployment

> [!IMPORTANT]
> **Definitive Auditor Ruling:** **NO THRESHOLD IS CURRENTLY AUTHORIZED FOR PRODUCTION DEPLOYMENT.**

Any production deployment recommendation is strictly withheld pending fulfillment of the following three empirical gates:
1. **Gate 1 (Clean-Query Benchmark Acquisition):** A dedicated, non-adversarial benchmark of at least 1,000 domain-specific RAG queries with ground-truth clean evidence must be evaluated.
2. **Gate 2 (Downstream Task Utility Gating):** End-to-end RAG answer quality (e.g. Exact Match, ROUGE-L, Faithfulness, Abstention Rate) must be evaluated with the guardrail enabled at $\theta \in \{0.16, 0.20, 0.24, 0.50\}$ to determine acceptable evidence loss tolerances.
3. **Gate 3 (Neutral/Contradiction Boundary Remediation):** The 26.24% false-alarm rate on neutral evidence at $\theta = 0.16$ must be mitigated (e.g., via a two-stage verifier or focal loss on hard negatives) before security thresholds can be safely lowered.

---

## 7. Limitations

1. **No External Clean Benchmark:** Clean-query utility metrics reported in Section 5 are internal validation proxy estimates derived from RAGTruth non-contradictory samples. They do not represent real-world enterprise queries.
2. **Held-Out Calibration Absent:** Temperature scaling was fit on the validation set itself. True out-of-distribution calibration error may be higher than the reported 0.0306.
3. **Capacity Constraints:** DeBERTa-v3-small (44M backbone parameters) displays an uncalibrated probability ceiling of 0.85 and misses 39.3% of contradictions even at $\theta = 0.10$.
4. **Binary Utility Abstraction:** In real RAG systems, rejecting one passage out of five does not necessarily cause an answer failure if other passages contain redundant facts. End-to-end utility cannot be fully modeled from sentence-level NLI alone.

---

## 8. Recommended Next Experiments

1. **Phase 11.2 Milestone: Clean RAG Retrieval Audit:** Acquire and format an independent test set of 1,000 clean QA pairs (e.g., from MS MARCO or Natural Questions) through the frozen DeBERTa-v3-small NLI detector.
2. **End-to-End Downstream Utility Testing:** Run generation benchmarks comparing RAG output quality with the detector running at $\theta = 0.50$ (high utility / low recall) versus $\theta = 0.16$ (balanced F1 / high false alarm).
3. **Hierarchical 2-Stage Verification:** Implement a coarse filter at $\theta = 0.50$ followed by a secondary classifier specifically trained to separate Neutral from Contradiction in ambiguous samples.

---

## 9. Final Audit Sign-Off

### Overall Audit Verdict: **`PASS_WITH_LIMITATIONS`**

- **Step 04 Verification:** Confirmed valid, correct, and fully reproducible.
- **Clean-Query Discovery:** Confirmed missing; appropriately reported as **BLOCKED** without fabricating data.
- **Utility Analysis:** Documented using rigorous internal validation proxy measurements.
- **Deployment Safety:** Unambiguously gated; no premature production claims made.

**Audit Completed By:** Senior ML Evaluation Auditor  
**Integrity Seal:** Strict Read-Only Mode Maintained  
**Report Artifact:** `reports/research_completion/phase11_1_step05_clean_query_utility/clean_query_utility_audit.md`

