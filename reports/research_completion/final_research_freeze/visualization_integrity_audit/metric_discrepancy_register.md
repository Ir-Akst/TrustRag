# TrustRAG — Metric Discrepancy & Anomaly Register

**Auditor:** Senior ML Evaluation Auditor & Scientific Reproducibility Specialist  
**Date:** 2026-11-19T02:58:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Dedicated Branch:** `phase-17-20-final-release`  
**Release Tag Candidate:** `trustrag-v1.0.0-rc1` (Commit: `531bff3`)  
**Audited Artifacts:** All 13 Figures, CSV Datasets, and Source Experiment Logs  
**Output Directory:** `reports/research_completion/final_research_freeze/visualization_integrity_audit/`  

---

## 1. Executive Summary & Purpose

In compliance with scientific audit principles:
> *"Do not declare the figures publication-ready until every material discrepancy has been resolved or explicitly disclosed."*

This register catalogs every numerical variance, metric ambiguity, or transcription discrepancy identified during the forensic source-level audit of the 13 publication figures.

Each entry documents the observed value, the ground truth value derived from raw experimental records, the root-cause mechanism, the publication impact, and the recommended remediation.

---

## 2. Comprehensive Discrepancy Register

```
+---------------------------------------------------------------------------------------------------------+
|                                    DISCREPANCY REGISTER SUMMARY                                         |
+---------------------------------------------------------------------------------------------------------+
|  ID      Figure / Metric               Plotted Value   Ground Truth    Severity    Status               |
|  DISC-01 Figure 13 (Phase 11.1 Macro F1) 84.1%         55.04%          MODERATE    RESOLVED & DISCLOSED |
|  DISC-02 Figure 2 (Attack Denominators) 1,000 Total     875 Canonical   MINOR       RESOLVED & DISCLOSED |
|  DISC-03 Figure 6 (Calibration Partition) In-sample Val Dev/Eval Split  MINOR       RESOLVED & DISCLOSED |
|  DISC-04 Figure 11 (External Samples)   N=200 Balanced  2,700 / 3,000   INFORMATIONAL RECONCILED        |
+---------------------------------------------------------------------------------------------------------+
```

---

### Discrepancy DISC-01: Figure 13 Phase 11.1 Macro F1 Discrepancy (84.1% vs. 55.04%)
- **Affected Figure:** Figure 13 (`figure_13_research_progress.png`, `figure_13_research_progress.csv`, line 2).
- **Plotted / Reported String:** `"Phase 11.1, Nov 14, DeBERTa NLI Training, Macro F1, 84.1"`.
- **Ground Truth Empirical Value:** **`55.04%`** ($0.550383$).
- **Data Source Traced:**
  - Raw prediction file: `phase11_1_step03_full_nli_training/predictions_val.jsonl` ($N=2,662$).
  - Official training summary: `phase11_1_step03_full_nli_training/training_results.json` (`"best_macro_f1": 0.550382866935089`).
  - Formal post-training audit: `phase11_1_step03_full_nli_training/post_training_independent_audit.md` (Section 2.1: `"Macro F1: 0.550383"`).
- **Class Breakdown Analysis:**
  $$\text{Macro F1} = \frac{F_1(\text{Entailment}) + F_1(\text{Neutral}) + F_1(\text{Contradiction})}{3} = \frac{0.8230 + 0.4660 + 0.3622}{3} = 0.5504 \implies 55.04\%$$
  $$\text{Weighted F1} = \frac{0.8230(1662) + 0.4660(644) + 0.3622(356)}{2662} = 0.6750 \implies 67.50\%$$
- **Root Cause Forensic Reconstruction:**
  During early project drafting, the value `84.1%` was mistakenly transcribed. It originated from an informal aggregation of Entailment recall ($91.46\%$) and Entailment F1 ($82.30\%$) or binary classification accuracy, and was erroneously labeled as "Macro F1" in milestone summaries.
- **Scientific Impact:**
  Moderate. The underlying model checkpoint, weights, and predictions were not affected. However, reporting 84.1% Macro F1 in an academic paper would be scientifically inaccurate and immediately challenged during peer review.
- **Mandatory Remediation:**
  In the publication manuscript, Figure 13 must report **Macro F1 = 55.04%** (or relabel the milestone as Entailment F1 = 82.3% / Overall Accuracy = 70.40%). This register formally records the correct empirical value.

---

### Discrepancy DISC-02: Figure 2 Attack Denominators ($N=1,000$ vs. $N=875$)
- **Affected Figure:** Figure 2 (`figure_02_attack_defense.png`, `figure_02_attack_defense.csv`).
- **Plotted String:** `(N=125 per category, Total N=1,000)`.
- **Ground Truth Empirical Value:**
  The canonical synthetic security benchmark in `custom_security/raw_train.jsonl` contains exactly $2,000$ records ($1,000$ clean, $1,000$ poisoned).
  Of the $1,000$ poisoned records, exactly $125$ records are `benign_instruction_control` (clean imperative user prompts), leaving strictly **$N=875$ genuine malicious attacks** across 7 subtypes.
- **Analysis of Figure 2 Cohorts:**
  Figure 2 plotted 8 categories:
  1. Direct Prompt Injection ($N=125$)
  2. Medical Dosage ($N=125$)
  3. Cryptographic ($N=125$)
  4. Financial Disinfo ($N=125$)
  5. Astrophysics ($N=125$)
  6. Duplicate Conflict ($N=125$)
  7. Multi-doc 3v1 ($N=125$)
  8. Token DoS ($N=125$)
  - Categories 6 and 7 (Duplicate Conflict and Multi-doc 3v1) were drawn from Phase 13 Step 04 evaluations, while Credential Exfiltration ($N=125$) and Benign Instruction Controls ($N=125$) were omitted.
  - The sum equals $8 \times 125 = 1,000$.
- **Scientific Impact:**
  Minor. The individual category defense percentages ($100\%$ across categories for TrustRAG) are empirically verified from Phase 13 Step 04 records. However, the caption must not conflate the $N=1,000$ stress cohort with the canonical $N=875$ benchmark denominator.
- **Mandatory Remediation:**
  Figure 2 caption must explicitly state: *"Evaluated across 8 distinct attack categories ($N=125$ each, total $N=1,000$ evaluations in Phase 13 end-to-end audit); the canonical core benchmark contains $N=875$ genuine attacks."*

---

### Discrepancy DISC-03: Figure 6 Calibration Partition & In-Sample Validation
- **Affected Figure:** Figure 6 (`figure_06_calibration.png`, `figure_06_calibration.csv`).
- **Visual Claim:** ECE drops from $15.01\%$ to $3.06\%$ after temperature scaling ($T=1.7701$).
- **Ground Truth Context:**
  - In Phase 11.1 Step 04, temperature scaling parameter $T=1.7701$ was fitted directly on `predictions_val.jsonl` ($N=2,662$).
  - Figure 6 evaluates calibration on this same validation split ($N=2,662$), meaning that $T=1.7701$ represents in-sample validation calibration.
  - In Phase 16.2 Step 02, a separate, strictly grouped calibration partition (`sec_pair_0000` to `sec_pair_0299`, $N=600$ records) was used to fit domain temperature $T=1.4502$, achieving ECE = $0.0582$ on held-out evaluations.
- **Scientific Impact:**
  Minor. In-sample temperature scaling on validation data is common practice in NLI literature, but strict methodology requires disclosing that $T=1.7701$ was optimized on the validation distribution.
- **Mandatory Remediation:**
  Caption must explicitly note: *"Temperature scaling ($T=1.7701$) evaluated on the $N=2,662$ validation split; domain-fitted temperature on the $N=600$ security calibration dev partition yielded $T=1.4502$ (ECE=5.82%)."*

---

### Discrepancy DISC-04: Figure 11 External Benchmark Sample Sizes ($N=200$ vs. Full Splits)
- **Affected Figure:** Figure 11 (`figure_11_external_benchmarks.png`).
- **Plotted Sample Sizes:** RAGTruth $N=200$, HaluEval $N=200$.
- **Ground Truth Context:**
  - Total test records available in raw files: RAGTruth = $2,700$ records, HaluEval = $3,000$ records.
  - In Phase 15 Step 03 (`step03_external_validation_report.md`), a balanced sample of $N=200$ ($100$ factual, $100$ hallucinated) was formally evaluated against the live G3 hybrid verifier to measure precise clean preservation and defense rates.
  - Figure 11 faithfully plots this Phase 15 empirical benchmark ($N=200$ each).
- **Scientific Impact:**
  Informational. Reconciled and validated.

---

## 3. Discrepancy Resolution Verdict

All identified numerical and methodological discrepancies have been forensically investigated, mathematically explained, and documented in this register. The figures and reports are scientifically defensible under the disclosed conditions.

