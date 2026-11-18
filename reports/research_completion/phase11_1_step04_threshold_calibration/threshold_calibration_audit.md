# TrustRAG Phase 11.1 — Step 04: NLI Threshold Calibration & Operating-Point Audit

**Auditor Role:** Senior ML Evaluation Engineer and Independent Research Auditor  
**Date:** 2026-11-18  
**Repository:** `/home/aditya/rags/TrustRag-phase11` — Branch `phase-11` — HEAD `aba5cc9d`  
**Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  
**Predictions:** `reports/research_completion/phase11_1_step03_full_nli_training/predictions_val.jsonl`  
**Prior Audit:** `reports/research_completion/phase11_1_step03_full_nli_training/post_training_independent_audit.md` (Verdict: PASS WITH LIMITATIONS)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Methodology](#2-methodology)
3. [Reproducibility Verification](#3-reproducibility-verification)
4. [Baseline Metrics Recap](#4-baseline-metrics-recap)
5. [Threshold Sweep — Full Results](#5-threshold-sweep--full-results)
6. [Operating-Point Analysis](#6-operating-point-analysis)
7. [Explicit Comparison: θ = 0.50 vs θ = 0.15](#7-explicit-comparison-θ--050-vs-θ--015)
8. [Class-wise False Alarm Analysis](#8-class-wise-false-alarm-analysis)
9. [Calibration Analysis](#9-calibration-analysis)
10. [Temperature Scaling Experiment](#10-temperature-scaling-experiment)
11. [Post-Calibration Threshold Sweep](#11-post-calibration-threshold-sweep)
12. [False Negative Analysis](#12-false-negative-analysis)
13. [Limitations](#13-limitations)
14. [Recommended Next Experiments](#14-recommended-next-experiments)
15. [Final Verdict](#15-final-verdict)

---

## 1. Executive Summary

This report presents a comprehensive, strictly read-only threshold calibration and operating-point analysis of the completed DeBERTa-v3-small NLI checkpoint trained during the Phase 11.1 campaign. All analysis uses existing validation predictions (2,662 samples) with raw logits and softmax probabilities.

**Key Findings:**

| Metric | Value |
|--------|-------|
| **Peak contradiction F1** | **0.4166** at θ = 0.16 (uncalibrated) |
| **Peak contradiction F1 (calibrated)** | **0.4155** at θ = 0.24 (T = 1.7701) |
| **Optimal temperature** | T = 1.7701 |
| **ECE improvement** | 0.1501 → **0.0306** (−79.6%) |
| **Brier improvement** | 0.4736 → **0.4383** (−7.4%) |
| **NLL improvement** | 0.8838 → **0.7741** (−12.4%) |
| **Max achievable recall at F1 > 0.38** | 56.74% (θ = 0.12) |
| **Verdict** | **PASS WITH LIMITATIONS** |

> [!IMPORTANT]
> No threshold is designated as deployment-safe. Deployment requires separate clean-query utility evaluation and domain-specific false-positive tolerance assessment.

---

## 2. Methodology

### 2.1 Threshold Sweep

For contradiction detection, the binary decision rule is:

$$\text{predict CONTRADICTION} \iff p(\text{CONTRADICTION} \mid x) \geq \theta$$

where $p(\text{CONTRADICTION} \mid x)$ is the softmax probability for the contradiction class (index 1).

Thresholds were swept from θ = 0.01 to θ = 0.99 at 0.01 increments (99 operating points). At each threshold:

- **True Positives (TP):** True contradictions flagged as contradictions
- **False Positives (FP):** Non-contradictions flagged as contradictions, decomposed into Entailment-origin FPs and Neutral-origin FPs
- **False Negatives (FN):** True contradictions missed
- **Precision** = TP / (TP + FP)
- **Recall** = TP / (TP + FN)
- **F1** = 2 · Precision · Recall / (Precision + Recall)
- **FPR** = FP / (FP + TN) — false positive rate on non-contradiction samples
- **FNR** = FN / (FN + TP)

### 2.2 Calibration Metrics

- **Multiclass Brier Score:** $\text{BS} = \frac{1}{N} \sum_{i=1}^{N} \sum_{c=1}^{C} (p_{ic} - y_{ic})^2$
- **ECE-10 (Expected Calibration Error):** 10 equal-width bins on max predicted confidence
- **NLL (Negative Log-Likelihood):** $\text{NLL} = -\frac{1}{N} \sum_{i=1}^{N} \log p_{i, y_i}$

### 2.3 Temperature Scaling

A single scalar temperature T is applied to raw logits before softmax:

$$p_c^{(T)}(x) = \frac{\exp(z_c / T)}{\sum_{j} \exp(z_j / T)}$$

T was optimized by minimizing NLL on the validation set via scipy bounded optimization (backed by grid search verification). T > 1 spreads the softmax distribution, reducing overconfidence.

> [!WARNING]
> Temperature scaling was fit on the validation set itself (no held-out calibration split). Post-calibration metrics are therefore optimistic and must not be quoted as generalization bounds.

---

## 3. Reproducibility Verification

| Item | Value | Status |
|------|-------|--------|
| Predictions file | `predictions_val.jsonl` | ✅ |
| Predictions SHA-256 | `6d57e5554358ba16d744b727703632cc91f1a432be7e2607d03a7bbc80ee6b48` | ✅ |
| Checkpoint checksums file SHA-256 | `a486e37f43be43b598021fbbc811809e00e4b2966dcc67bb5aea26c329e32d3d` | ✅ |
| Total predictions | 2,662 (exactly once per validation sample) | ✅ |
| Duplicate sample IDs | 0 | ✅ |
| Label mapping | ENTAILMENT=0, CONTRADICTION=1, NEUTRAL=2 | ✅ |
| Train-val (premise, hypothesis) overlap | 0 / 2,662 (0.00%) | ✅ |

**Class Distribution:**

| Class | Count | Proportion |
|-------|-------|------------|
| ENTAILMENT | 1,662 | 62.43% |
| CONTRADICTION | 356 | 13.37% |
| NEUTRAL | 644 | 24.19% |

**Checkpoint Artifacts (9 files):**

| File | SHA-256 |
|------|---------|
| `checkpoint_meta.json` | `0bd573e73a940c4146e54be751a47237aa6b9c72a3800cd921d879dca108ee09` |
| `config.json` | `38370396a4e2988a14226b6b8875766e660ab8bbd1374b9e23a6e0c7a05ef385` |
| `model.safetensors` | `0464758a2cd31260b44af96093dd52c2824a8305278d136ec438c87ee2b92313` |
| `optimizer.pt` | `9a2fd299dd3961fdf66532f12c1bf9ff06365dcb6957e0bcc50487d6b9792ac7` |
| `rng_state.pt` | `437b2e84b3fc90e6bc22ef0a043a986cf6124d523be0962df7a988a44d452e12` |
| `scheduler.pt` | `1d78acdcfbbbb16e77bbe7752380688630dfe37fa53954279a7d69d3ad41e648` |
| `tokenizer.json` | `e9ddd853a4a31023721c993458663f2019e3154a05dacf0d2b3c217e53d9bdc8` |
| `tokenizer_config.json` | `1121ad33ecd98a97b2db184ce896546feb7555bebddf33a2dfe1b1a1077dc847` |

---

## 4. Baseline Metrics Recap

Final checkpoint (Step 8,112, Epoch 3) argmax classification:

| Metric | Value |
|--------|-------|
| Accuracy | 70.40% |
| Balanced Accuracy | 52.58% |
| Macro F1 | 0.5504 |
| Weighted F1 | 0.6750 |

**Confusion Matrix (argmax):**

| | Pred ENT | Pred CON | Pred NEU |
|---|---:|---:|---:|
| **True ENT** | 1,520 | 13 | 129 |
| **True CON** | 170 | 90 | 96 |
| **True NEU** | 342 | 38 | 264 |

**Per-Class Metrics:**

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| ENTAILMENT | 74.80% | 91.46% | 0.8230 | 1,662 |
| CONTRADICTION | 63.83% | 25.28% | 0.3622 | 356 |
| NEUTRAL | 53.99% | 40.99% | 0.4660 | 644 |

---

## 5. Threshold Sweep — Full Results

### 5.1 Key Operating Points (Uncalibrated)

| θ | Pred+ | TP | FP | FN | TN | Precision | Recall | F1 | FPR | FP(ENT) | FP(NEU) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.01 | 2,580 | 353 | 2,227 | 3 | 79 | 13.68% | 99.16% | 0.2405 | 96.57% | 1,585 | 642 |
| 0.05 | 1,394 | 272 | 1,122 | 84 | 1,184 | 19.51% | 76.40% | 0.3109 | 48.66% | 666 | 456 |
| 0.08 | 976 | 232 | 744 | 124 | 1,562 | 23.77% | 65.17% | 0.3483 | 32.26% | 386 | 358 |
| 0.10 | 828 | 216 | 612 | 140 | 1,694 | 26.09% | 60.67% | 0.3649 | 26.54% | 290 | 322 |
| 0.12 | 705 | 202 | 503 | 154 | 1,803 | 28.65% | 56.74% | 0.3808 | 21.81% | 220 | 283 |
| 0.14 | 579 | 186 | 393 | 170 | 1,913 | 32.12% | 52.25% | 0.3979 | 17.04% | 160 | 233 |
| **0.15** | **511** | **176** | **335** | **180** | **1,971** | **34.44%** | **49.44%** | **0.4060** | **14.53%** | **134** | **201** |
| **0.16** | **441** | **166** | **275** | **190** | **2,031** | **37.64%** | **46.63%** | **0.4166** | **11.93%** | **106** | **169** |
| 0.17 | 373 | 146 | 227 | 210 | 2,079 | 39.14% | 41.01% | 0.4005 | 9.84% | 89 | 138 |
| 0.18 | 306 | 129 | 177 | 227 | 2,129 | 42.16% | 36.24% | 0.3897 | 7.68% | 70 | 107 |
| 0.20 | 213 | 105 | 108 | 251 | 2,198 | 49.30% | 29.49% | 0.3691 | 4.68% | 42 | 66 |
| 0.25 | 169 | 95 | 74 | 261 | 2,232 | 56.21% | 26.69% | 0.3619 | 3.21% | 28 | 46 |
| 0.30 | 158 | 94 | 64 | 262 | 2,242 | 59.49% | 26.40% | 0.3658 | 2.78% | 23 | 41 |
| 0.40 | 140 | 90 | 50 | 266 | 2,256 | 64.29% | 25.28% | 0.3629 | 2.17% | 13 | 37 |
| **0.50** | **138** | **89** | **49** | **267** | **2,257** | **64.49%** | **25.00%** | **0.3603** | **2.12%** | **13** | **36** |
| 0.60 | 135 | 89 | 46 | 267 | 2,260 | 65.93% | 25.00% | 0.3625 | 1.99% | 13 | 33 |
| 0.70 | 127 | 83 | 44 | 273 | 2,262 | 65.35% | 23.31% | 0.3437 | 1.91% | 13 | 31 |
| 0.80 | 88 | 59 | 29 | 297 | 2,277 | 67.05% | 16.57% | 0.2658 | 1.26% | 8 | 21 |
| 0.86+ | 0 | 0 | 0 | 356 | 2,306 | — | 0.00% | 0.0000 | 0.00% | 0 | 0 |

### 5.2 F1 Curve Characteristics

The F1 curve peaks sharply near θ = 0.16 and falls off rapidly in both directions:

- θ < 0.10: F1 < 0.37, dominated by false positives
- θ = 0.10–0.17: F1 plateau region (0.365–0.417), the useful operating band
- θ = 0.16: **Global maximum F1 = 0.4166**
- θ > 0.20: F1 declines monotonically as recall drops below 30%
- θ ≥ 0.86: Zero predictions — model never assigns p(CONTRADICTION) ≥ 0.86

> [!NOTE]
> The model's contradiction probability scores are compressed into a narrow range. The effective decision band spans only θ ∈ [0.08, 0.25]; outside this band, either FPR or FNR is catastrophically high.

---

## 6. Operating-Point Analysis

### 6.1 Named Operating Points (Uncalibrated)

| Operating Point | θ | Precision | Recall | F1 | FPR |
|----------------|---:|---:|---:|---:|---:|
| **Max F1** | **0.16** | **37.64%** | **46.63%** | **0.4166** | **11.93%** |
| Recall ≥ 40% | 0.17 | 39.14% | 41.01% | 0.4005 | 9.84% |
| Recall ≥ 45% | 0.16 | 37.64% | 46.63% | 0.4166 | 11.93% |
| Recall ≥ 50% | 0.14 | 32.12% | 52.25% | 0.3979 | 17.04% |
| Recall ≥ 55% | 0.12 | 28.65% | 56.74% | 0.3808 | 21.81% |
| Recall ≥ 60% | 0.10 | 26.09% | 60.67% | 0.3649 | 26.54% |
| Default (argmax/0.50) | 0.50 | 64.49% | 25.00% | 0.3603 | 2.12% |

### 6.2 Trade-off Summary

Lowering the threshold from 0.50 to 0.16:
- **Recall doubles**: 25.00% → 46.63% (+21.63 pp)
- **F1 improves**: 0.3603 → 0.4166 (+15.6%)
- **Cost**: Precision drops 64.49% → 37.64%, FPR rises 2.12% → 11.93%

The ≥ 50% recall point (θ = 0.14) requires accepting a 17% false positive rate on non-contradiction samples.

---

## 7. Explicit Comparison: θ = 0.50 vs θ = 0.15

| Metric | θ = 0.50 | θ = 0.15 | Δ |
|--------|----------|----------|---|
| Predicted positives | 138 | 511 | +373 |
| True positives | 89 | 176 | +87 |
| False positives | 49 | 335 | +286 |
| False negatives | 267 | 180 | −87 |
| Precision | 64.49% | 34.44% | −30.05 pp |
| Recall | 25.00% | 49.44% | **+24.44 pp** |
| F1 | 0.3603 | 0.4060 | **+0.0457** |
| FPR | 2.12% | 14.53% | +12.41 pp |
| FP from Entailment | 13 | 134 | +121 |
| FP from Neutral | 36 | 201 | +165 |

**Interpretation:** Moving from θ = 0.50 to θ = 0.15 recovers 87 additional true contradictions but generates 286 additional false alarms. The majority of new false positives originate from Neutral samples (58%), with Entailment samples contributing 42%.

---

## 8. Class-wise False Alarm Analysis

### 8.1 FP Origin Breakdown by Threshold

| θ | Total FP | FP from ENT | FP from NEU | ENT FPR | NEU FPR |
|---:|---:|---:|---:|---:|---:|
| 0.05 | 1,122 | 666 (59.4%) | 456 (40.6%) | 40.07% | 70.81% |
| 0.10 | 612 | 290 (47.4%) | 322 (52.6%) | 17.45% | 50.00% |
| 0.15 | 335 | 134 (40.0%) | 201 (60.0%) | 8.06% | 31.21% |
| **0.16** | **275** | **106 (38.5%)** | **169 (61.5%)** | **6.38%** | **26.24%** |
| 0.20 | 108 | 42 (38.9%) | 66 (61.1%) | 2.53% | 10.25% |
| 0.25 | 74 | 28 (37.8%) | 46 (62.2%) | 1.68% | 7.14% |
| 0.50 | 49 | 13 (26.5%) | 36 (73.5%) | 0.78% | 5.59% |

> [!NOTE]
> At all thresholds, Neutral samples are disproportionately false-flagged as contradictions relative to their population share (24% of data, but 60%+ of FPs at θ ≤ 0.20). This indicates the model struggles with the Neutral–Contradiction decision boundary.

### 8.2 Per-Source-Class FPR

At the optimal F1 threshold (θ = 0.16):
- **Entailment false alarm rate:** 106 / 1,662 = **6.38%** — Acceptable for most downstream uses.
- **Neutral false alarm rate:** 169 / 644 = **26.24%** — Problematic. One in four neutral pairs is incorrectly flagged as a contradiction.

---

## 9. Calibration Analysis

### 9.1 Pre-Calibration (T = 1.0)

| Metric | Value |
|--------|-------|
| Multiclass Brier Score | 0.4736 |
| Contradiction Brier | 0.1005 |
| ECE-10 | 0.1501 |
| NLL | 0.8838 |

**Pre-Calibration Reliability Diagram (ECE-10 bins):**

| Bin | Count | Avg Conf | Avg Acc | Gap |
|-----|------:|:--------:|:-------:|:---:|
| (0.0, 0.1] | 0 | — | — | — |
| (0.1, 0.2] | 0 | — | — | — |
| (0.2, 0.3] | 0 | — | — | — |
| (0.3, 0.4] | 2 | 0.3877 | 0.0000 | 0.3877 |
| (0.4, 0.5] | 78 | 0.4610 | 0.5000 | 0.0390 |
| (0.5, 0.6] | 95 | 0.5464 | 0.4737 | 0.0727 |
| (0.6, 0.7] | 145 | 0.6615 | 0.5241 | 0.1374 |
| (0.7, 0.8] | 442 | 0.7454 | 0.6086 | 0.1368 |
| **(0.8, 0.9]** | **561** | **0.8544** | **0.6934** | **0.1610** |
| **(0.9, 1.0]** | **1,339** | **0.9516** | **0.7886** | **0.1629** |

> [!WARNING]
> Severe overconfidence in the top two bins (1,900 / 2,662 samples = 71.4%). The model assigns >80% confidence to samples it gets wrong 20–31% of the time.

### 9.2 Pre-Calibration Diagnosis

The reliability diagram reveals systematic overconfidence that worsens at higher confidence levels:
- Bins [0.8, 1.0] contain 71% of all predictions.
- Average gap in these bins: 0.1610–0.1629.
- The model rarely produces low-confidence predictions (0 samples below 0.3).

---

## 10. Temperature Scaling Experiment

### 10.1 Optimization

| Method | Optimal T | NLL |
|--------|-----------|-----|
| Coarse grid (0.5–5.0, step 0.1) | 1.80 | 0.774120 |
| Fine grid (±0.5, step 0.01) | 1.770 | 0.774052 |
| Scipy bounded optimization | **1.7701** | **0.774052** |

**Optimal temperature: T = 1.7701**

T > 1 confirms the model is systematically overconfident and needs its logits dampened.

### 10.2 Calibration Improvement

| Metric | Before (T=1.0) | After (T=1.7701) | Change |
|--------|-----------------|-------------------|--------|
| **ECE-10** | **0.1501** | **0.0306** | **−79.6%** |
| Multiclass Brier | 0.4736 | 0.4383 | −7.4% |
| Contradiction Brier | 0.1005 | 0.1001 | −0.4% |
| NLL | 0.8838 | 0.7741 | −12.4% |
| Accuracy | 70.40% | 70.40% | 0.0% |

> [!TIP]
> Temperature scaling dramatically reduces ECE (from 0.15 to 0.03) without changing classification accuracy, since it preserves the argmax ordering. The accuracy is identical because temperature scaling is a monotone transformation.

### 10.3 Post-Calibration Reliability Diagram

| Bin | Count | Avg Conf | Avg Acc | Gap |
|-----|------:|:--------:|:-------:|:---:|
| (0.0, 0.1] | 0 | — | — | — |
| (0.1, 0.2] | 0 | — | — | — |
| (0.2, 0.3] | 0 | — | — | — |
| (0.3, 0.4] | 22 | 0.3863 | 0.5455 | 0.1591 |
| (0.4, 0.5] | 173 | 0.4472 | 0.4855 | 0.0384 |
| (0.5, 0.6] | 487 | 0.5606 | 0.5708 | **0.0103** |
| (0.6, 0.7] | 507 | 0.6535 | 0.6982 | 0.0447 |
| (0.7, 0.8] | 754 | 0.7541 | 0.7056 | 0.0486 |
| (0.8, 0.9] | 719 | 0.8441 | 0.8540 | **0.0099** |
| (0.9, 1.0] | 0 | — | — | — |

Post-calibration, predictions are spread across bins [0.3, 0.9] rather than concentrated in [0.8, 1.0]. The largest gap (0.1591 in [0.3, 0.4]) occurs in a bin with only 22 samples. All major bins have gap < 0.05.

---

## 11. Post-Calibration Threshold Sweep

### 11.1 Key Operating Points (Calibrated, T = 1.7701)

| θ | Pred+ | TP | FP | Precision | Recall | F1 | FPR | FP(ENT) | FP(NEU) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.10 | 2,076 | 335 | 1,741 | 16.14% | 94.10% | 0.2755 | 75.50% | 1,148 | 593 |
| 0.15 | 1,276 | 258 | 1,018 | 20.22% | 72.47% | 0.3162 | 44.15% | 594 | 424 |
| 0.20 | 730 | 205 | 525 | 28.08% | 57.58% | 0.3775 | 22.77% | 234 | 291 |
| **0.24** | **419** | **161** | **258** | **38.42%** | **45.22%** | **0.4155** | **11.19%** | **98** | **160** |
| 0.25 | 340 | 139 | 201 | 40.88% | 39.04% | 0.3994 | 8.72% | 75 | 126 |
| 0.30 | 166 | 95 | 71 | 57.23% | 26.69% | 0.3640 | 3.08% | 26 | 45 |
| 0.40 | 139 | 89 | 50 | 64.03% | 25.00% | 0.3596 | 2.17% | 13 | 37 |
| 0.50 | 135 | 89 | 46 | 65.93% | 25.00% | 0.3625 | 1.99% | 13 | 33 |

### 11.2 Comparison: Uncalibrated vs Calibrated Operating Points

| Operating Point | Uncal θ | Uncal F1 | Cal θ | Cal F1 |
|----------------|--------:|--------:|------:|-------:|
| Max F1 | 0.16 | **0.4166** | 0.24 | 0.4155 |
| Recall ≥ 50% | 0.14 | 0.3979 | 0.22 | 0.3945 |

> [!NOTE]
> Temperature scaling shifts the optimal threshold upward (0.16 → 0.24) but achieves nearly identical peak F1 (0.4166 vs 0.4155). The benefit of calibration is better-calibrated confidence scores, not better discrimination.

---

## 12. False Negative Analysis

### 12.1 FN Volume at Key Thresholds

| θ | Total FN | FN → ENT | FN → NEU | Mean p(CON) of FNs |
|---:|---:|---:|---:|---:|
| 0.10 | 140 | 136 (97.1%) | 4 (2.9%) | 0.0466 |
| 0.15 | 180 | 156 (86.7%) | 24 (13.3%) | 0.0644 |
| 0.20 | 251 | 164 (65.3%) | 87 (34.7%) | 0.0956 |
| 0.30 | 262 | 167 (63.7%) | 95 (36.3%) | 0.1007 |
| 0.50 | 267 | 170 (63.7%) | 96 (36.0%) | 0.1058 |

### 12.2 Interpretation

At the default threshold (θ = 0.50), 267 of 356 true contradictions are missed (75%). Of those:
- **170 (63.7%)** are misclassified as Entailment — the model sees no semantic conflict.
- **96 (36.0%)** are misclassified as Neutral — the model sees ambiguity but not contradiction.
- Mean p(CONTRADICTION) of these FNs is only **0.1058** — the model is confidently wrong, not uncertain.

This pattern indicates that most missed contradictions are examples where the model fundamentally fails to detect the semantic conflict, rather than borderline cases that a threshold shift could rescue. Even at θ = 0.10, 140 contradictions (39.3%) remain undetectable.

---

## 13. Limitations

1. **Validation-only calibration:** Temperature scaling was fit on the same 2,662 validation samples used for evaluation. Post-calibration metrics (ECE = 0.0306) are optimistic. A proper calibration protocol requires a separate held-out calibration split.

2. **No deployment safety guarantee:** No threshold is validated against clean/non-adversarial queries. The 11.93% FPR at θ = 0.16 means approximately 1 in 8 non-contradiction inputs would be incorrectly flagged. Utility impact on downstream RAG retrieval is unknown.

3. **Class imbalance:** Contradiction is the minority class (13.37%). The 2:1 Neutral-to-Contradiction FP ratio at most thresholds reflects the model's poor Neutral/Contradiction boundary.

4. **Compressed probability range:** The model never assigns p(CONTRADICTION) ≥ 0.86. The effective decision band for threshold tuning is narrow (θ ∈ [0.08, 0.25]).

5. **Irrecoverable false negatives:** 39.3% of true contradictions have p(CONTRADICTION) < 0.10 and cannot be recovered by any threshold.

6. **Single validation set:** Results may not generalize to other domains or distribution shifts.

7. **No temperature scaling on a held-out test set:** The improvement in ECE should be validated on unseen data before deployment.

---

## 14. Recommended Next Experiments

1. **Clean-query utility evaluation:** Evaluate FPR on a curated set of clean (non-adversarial) query–document pairs to quantify the false-contradiction rate on typical RAG inputs.

2. **Contradiction recall on adversarial pairs:** Evaluate recall specifically on known contradictory query–document pairs extracted from the target domain.

3. **Two-stage classification:** Train a secondary Neutral-vs-Contradiction discriminator on samples with p(CONTRADICTION) ∈ [0.05, 0.30] to reduce the high neutral FP rate.

4. **Proper calibration split:** Reserve 20% of validation data for temperature scaling fitting; evaluate on the remaining 80%.

5. **Model scaling:** Compare with DeBERTa-v3-base or DeBERTa-v3-large to determine if the compressed probability range and low contradiction recall are capacity-limited.

6. **Hard negative mining:** Augment training with synthetic contradictions that look like neutrals (the dominant confusion pattern).

---

## 15. Final Verdict

### PASS WITH LIMITATIONS

**Justification:**

✅ All reproducibility requirements verified (SHA-256, sample counts, label mapping, zero data leakage).  
✅ Fine-grained threshold sweep (99 operating points) completed with class-wise FP decomposition.  
✅ Temperature scaling significantly improves calibration (ECE: 0.1501 → 0.0306, −79.6%).  
✅ Max-F1 operating point identified: θ = 0.16, F1 = 0.4166.  
✅ Clear operating-point trade-offs documented for recall targets 40%–60%.  

⚠️ Contradiction recall remains limited — peak F1 achieves only 46.63% recall.  
⚠️ 39% of contradictions are irrecoverable at any threshold (p(CON) < 0.10).  
⚠️ Neutral false alarm rate is high at useful operating points (26% at θ = 0.16).  
⚠️ Temperature calibration is validation-only (no held-out split).  
⚠️ No deployment threshold can be recommended without clean-query utility testing.

**Recommended operating point for further investigation:** θ = 0.16 (uncalibrated) or θ = 0.24 (calibrated). Both require downstream utility validation before deployment.

---

## Appendix A: Analysis Environment

| Component | Version/Path |
|-----------|-------------|
| Python | 3.10 |
| NumPy | 2.2.6 |
| SciPy | 1.15.3 |
| PyTorch | 2.14.1+cpu |
| Analysis script | `scratch/step04_threshold_calibration.py` |
| Results JSON | `scratch/step04_results.json` |

## Appendix B: Integrity Statement

This audit was performed in strictly read-only mode. No training processes were started, stopped, or modified. No checkpoints, datasets, predictions, scripts, configurations, or Git state were altered. The only file created was this report and the supporting analysis script/results in the scratch directory.

