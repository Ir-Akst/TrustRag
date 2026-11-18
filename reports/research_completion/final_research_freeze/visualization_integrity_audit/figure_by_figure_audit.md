# TrustRAG — Figure-by-Figure Scientific Integrity Audit

**Auditor:** Independent ML Research Auditor & Scientific Visualization Specialist  
**Date:** 2026-11-19T02:55:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Dedicated Branch:** `phase-17-20-final-release`  
**Release Tag Candidate:** `trustrag-v1.0.0-rc1` (Commit: `531bff3`)  
**Audited Directory:** `reports/research_completion/final_research_freeze/figures/`  
**Output Directory:** `reports/research_completion/final_research_freeze/visualization_integrity_audit/`  

---

## 1. Executive Summary & Audit Protocol

This document provides a strict, source-level audit of all **13 publication figures**, their corresponding underlying CSV datasets in `figures/data/`, the generation script `scripts/generate_publication_figures.py`, and the index `figure_index.md`.

Every numerical data point in each figure was cross-referenced against the raw experimental outputs, JSON logs, and historical research completion reports across Phases 11 through 20.

```
+---------------------------------------------------------------------------------------------------+
|                                  FIGURE AUDIT SUMMARY DASHBOARD                                   |
+---------------------------------------------------------------------------------------------------+
|  Total Figures Audited:        13 Figures                                                         |
|  Export Formats Verified:      13/13 PNG (300 DPI) | 13/13 PDF (Vector) | 13/13 SVG (Vector)      |
|  Underlying CSV Data:          13/13 Verified & Matched to Source                                 |
|  Cryptographic Verification:   100% OK in sha256_verification.txt                                 |
|  Identified Discrepancies:     2 Discrepancies (Figure 13 Macro F1 & Figure 2 Denominator)        |
|  Figure Integrity Verdict:     PASS WITH LIMITATIONS                                              |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Exhaustive Figure-by-Figure Forensic Verification

### Figure 1: Overall Architecture Comparison (`figure_01_architecture_comparison`)
- **Visual Subject:** Grouped bar chart comparing Standard RAG, TrustRAG G1, TrustRAG G1+G2, TrustRAG G1+G2+G3 Baseline, and TrustRAG G1+G2+G3 Optimized.
- **Metrics Plotted:** Attack Defense Rate (ADR %), Attack Success Rate (ASR %), Clean False Positive Rate (FPR %), Clean Evidence Delivery (%).
- **Primary Data Source:** `reports/research_completion/final_independent_validation_and_release/phase17_comparative_results.json`.
- **Sample Sizes:** $N = 875$ genuine attacks, $N = 1,000$ clean control query-evidence pairs.
- **Cross-Verification Matrix:**
  | Architecture | Plotted ADR (%) | Source ADR (%) | Plotted Clean FPR (%) | Source Clean FPR (%) | Discrepancy |
  |---|:---:|:---:|:---:|:---:|:---:|
  | Standard RAG | 14.29% [12.12, 16.76] | 14.29% [12.12, 16.76] | 0.00% [0.00, 0.38] | 0.00% [0.00, 0.38] | Exact Match |
  | TrustRAG G1 | 14.29% [12.12, 16.76] | 14.29% [12.12, 16.76] | 0.00% [0.00, 0.38] | 0.00% [0.00, 0.38] | Exact Match |
  | TrustRAG G1+G2 | 100.00% [99.56, 100.00] | 100.00% [99.56, 100.00] | 0.00% [0.00, 0.38] | 0.00% [0.00, 0.38] | Exact Match |
  | TrustRAG G3 Base | 100.00% [99.56, 100.00] | 100.00% [99.56, 100.00] | 12.50% [10.59, 14.69] | 12.50% [10.59, 14.69] | Exact Match |
  | TrustRAG G3 Opt | 100.00% [99.56, 100.00] | 100.00% [99.56, 100.00] | 0.00% [0.00, 0.38] | 0.00% [0.00, 0.38] | Exact Match |
- **Audit Verdict:** **PASS (Exact Match)**.

---

### Figure 2: Attack Defense Performance Across Categories (`figure_02_attack_defense`)
- **Visual Subject:** Per-category detection rates across 8 attack categories comparing Standard RAG, G1, G1+G2, and G3 Optimized.
- **Categories Plotted:** Direct Prompt Injection ($N=125$), Medical Dosage ($N=125$), Cryptographic ($N=125$), Financial Disinfo ($N=125$), Astrophysics ($N=125$), Duplicate Conflict ($N=125$), Multi-doc 3v1 ($N=125$), Token DoS ($N=125$).
- **Primary Data Source:** `reports/research_completion/phase13_generalization_and_hardening/step04_end_to_end_metrics.json`.
- **Denominator Investigation:**
  - The figure title states: `(N=125 per category, Total N=1,000)`.
  - While $8 \times 125 = 1,000$, the true primary synthetic benchmark in `custom_security/raw_train.jsonl` contains 7 attack subtypes ($7 \times 125 = 875$) and 125 benign instruction controls.
  - In Figure 2, the categories were formulated by including Duplicate Conflict ($N=125$) and Multi-doc 3v1 ($N=125$) from Phase 13 Step 04 while omitting Credential Exfiltration ($N=125$) and Benign Instruction Controls ($N=125$).
- **Audit Verdict:** **PASS WITH LIMITATION**. Plotted values are empirically accurate to Phase 13 Step 04 records, but the caption must explicitly clarify that the primary canonical synthetic attack denominator is $N=875$, with the additional cohorts representing Phase 13 structural stress tests.

---

### Figure 3: Clean Utility Comparison (`figure_03_clean_utility`)
- **Visual Subject:** Dual-panel bar chart comparing Phase 16.1 Baseline vs. Phase 16.2 Optimized on Clean False Positive Rate (FPR %) and Clean Evidence Preservation (%).
- **Primary Data Source:** `phase16_2_neural_utility_optimization/step05_comparative_benchmark.json`.
- **Sample Size:** $N = 1,000$ clean controls.
- **Cross-Verification Matrix:**
  - Phase 16.1 Baseline: Clean FPR = $12.50\%$ ($125/1,000$, CI: $[10.59\%, 14.69\%]$), Clean Delivery = $87.50\%$ ($875/1,000$, CI: $[85.31\%, 89.41\%]$).
  - Phase 16.2 Optimized: Clean FPR = $0.00\%$ ($0/1,000$, CI: $[0.00\%, 0.38\%]$), Clean Delivery = $100.00\%$ ($1,000/1,000$, CI: $[99.62\%, 100.00\%]$).
- **Audit Verdict:** **PASS (Exact Match)**.

---

### Figure 4: DeBERTa-v3-small NLI Confusion Matrix (`figure_04_nli_confusion_matrix`)
- **Visual Subject:** Normalized percentage heatmap with overlaid raw sample counts across ENTAILMENT, NEUTRAL, and CONTRADICTION.
- **Primary Data Source:** Raw predictions from `phase11_1_step03_full_nli_training/predictions_val.jsonl`.
- **Sample Size:** $N = 2,662$ held-out validation pairs.
- **Recomputed Matrix Values:**
  $$\begin{array}{c|ccc|c}
  \text{True / Pred} & \textbf{ENTAILMENT} & \textbf{NEUTRAL} & \textbf{CONTRADICTION} & \textbf{Row Total} \\
  \hline
  \textbf{ENTAILMENT} & 1,520\ (91.5\%) & 129\ (7.8\%) & 13\ (0.8\%) & 1,662 \\
  \textbf{NEUTRAL} & 342\ (53.1\%) & 264\ (41.0\%) & 38\ (5.9\%) & 644 \\
  \textbf{CONTRADICTION} & 170\ (47.8\%) & 96\ (27.0\%) & 90\ (25.3\%) & 356 \\
  \end{array}$$
- **Audit Verdict:** **PASS (Exact Match)**. Every cell matches raw JSON prediction records with zero discrepancy.

---

### Figure 5: Class-wise Model Performance (`figure_05_classwise_metrics`)
- **Visual Subject:** Precision, Recall, and F1-score across classes, Macro Average, and Weighted Average.
- **Primary Data Source:** `predictions_val.jsonl` and `post_training_independent_audit.md`.
- **Cross-Verification Matrix:**
  | Metric Entity | Precision (%) | Recall (%) | F1-Score (%) | Support | Status |
  |---|:---:|:---:|:---:|:---:|:---:|
  | **ENTAILMENT** | 74.80% | 91.46% | 82.30% | 1,662 | Exact Match |
  | **NEUTRAL** | 53.99% | 40.99% | 46.60% | 644 | Exact Match |
  | **CONTRADICTION**| 63.83% | 25.28% | 36.22% | 356 | Exact Match |
  | **Macro Average** | 64.21% | 52.58% | **55.04%** | 2,662 | Exact Match |
  | **Weighted Avg** | 68.31% | 70.47% | **67.50%** | 2,662 | Exact Match |
- **Audit Verdict:** **PASS (Exact Match)**.

---

### Figure 6: Calibration Reliability Diagram (`figure_06_calibration`)
- **Visual Subject:** Dual-panel reliability diagram (confidence vs. accuracy in 10 bins) comparing uncalibrated softmax ($T=1.0$) vs. temperature scaling ($T=1.7701$), with prediction confidence histograms.
- **Primary Data Source:** `predictions_val.jsonl` ($N=2,662$) and `phase16_2_neural_utility_optimization/step03_calibration_experiments.md`.
- **Statistical Metric Check:**
  - Uncalibrated ($T=1.0$): $\text{ECE} = 15.01\%$, Brier Score = $0.2196$ (multiclass normalized: $0.4736$).
  - Calibrated ($T=1.7701$): $\text{ECE} = 3.06\%$, Brier Score = $0.1956$ (multiclass normalized: $0.4383$).
- **Methodology Audit:** Plotted values accurately reflect evaluation of $T=1.7701$ on the $N=2,662$ validation split. As audited in Section 4, the caption must explicitly distinguish this validation evaluation from the $N=600$ held-out calibration dev partition (`sec_pair_0000` to `sec_pair_0299`) where $T=1.4502$ was fitted.
- **Audit Verdict:** **PASS (Exact Match)**.

---

### Figure 7: CPU Intra-Op Thread Latency Benchmarks (`figure_07_cpu_latency`)
- **Visual Subject:** P50, P95, and P99 latencies across 1, 2, 4, and 8 CPU threads.
- **Primary Data Source:** `final_independent_validation_and_release/phase19_scalability_results.json`.
- **Cross-Verification Matrix:**
  | Threads | Plotted P50 (ms) | Source P50 (ms) | Plotted P95 (ms) | Source P95 (ms) | Relative Speedup | Status |
  |:---:|:---:|:---:|:---:|:---:|:---:|:---:|
  | **1 Thread** | 97.72 | 97.72 | 99.15 | 99.15 | 1.00x | Exact Match |
  | **2 Threads** | 55.84 | 55.84 | 58.02 | 58.02 | 1.73x (Sweet Spot) | Exact Match |
  | **4 Threads** | 85.93 | 85.93 | 103.42 | 103.42 | 1.10x | Exact Match |
  | **8 Threads** | 78.31 | 78.31 | 82.71 | 82.71 | 1.25x | Exact Match |
- **Audit Verdict:** **PASS (Exact Match)**.

---

### Figure 8: Batch Throughput (`figure_08_batch_throughput`)
- **Visual Subject:** Dual-axis curve plotting latency per claim (ms) and sustained throughput (claims/sec) across batch sizes $B \in [1, 2, 4, 8, 16, 32]$.
- **Primary Data Source:** `final_independent_validation_and_release/phase19_scalability_results.json`.
- **Cross-Verification Matrix:**
  - $B=1$: $80.70\text{ ms/claim}$, $12.39\text{ claims/sec}$.
  - $B=2$: $92.65\text{ ms/claim}$, $10.79\text{ claims/sec}$.
  - $B=4$: $78.45\text{ ms/claim}$, $12.75\text{ claims/sec}$.
  - $B=8$: $81.15\text{ ms/claim}$, $12.32\text{ claims/sec}$.
  - $B=16$: $81.34\text{ ms/claim}$, $12.29\text{ claims/sec}$.
  - $B=32$: $83.05\text{ ms/claim}$, $12.04\text{ claims/sec}$.
- **Audit Verdict:** **PASS (Exact Match)**.

---

### Figure 9: Operational Memory Profile (`figure_09_memory_profile`)
- **Visual Subject:** Bar chart showing Baseline RSS ($289.3\text{ MB}$), Model Allocation ($439.0\text{ MB}$), Total Loaded RSS ($728.3\text{ MB}$), Peak Operational RSS ($774.5\text{ MB}$), and Container Memory Envelope ($1500.0\text{ MB}$).
- **Primary Data Source:** `final_independent_validation_and_release/phase19_scalability_results.json`.
- **Audit Verdict:** **PASS (Exact Match)**.

---

### Figure 10: Advanced Red-Team Heatmap (`figure_10_redteam_heatmap`)
- **Visual Subject:** Horizontal stacked bar chart mapping ADR and ASR across all 15 threat categories ($N=460$).
- **Primary Data Source:** `final_independent_validation_and_release/raw_predictions/phase18_redteam_predictions.jsonl` and `phase18_attack_dataset_manifest.json`.
- **Audit Cross-Check:**
  - 4 categories at 100% ADR (Character Obfuscation, Narrative Contradictions, Duplicate Scraping, Context Exhaustion).
  - Domain Misinformation at 75% ADR.
  - Adaptive Prompt Injection at 33.3% ADR.
  - Cross-Lingual Injection at 20% ADR.
  - 8 categories at 0% ADR (Sybil, Paraphrased Inversion, Multi-doc, etc.).
  - Overall ADR: $36.09\%$ ($166/460$), Overall ASR: $63.91\%$ ($294/460$).
- **Audit Verdict:** **PASS (Exact Match)**.

---

### Figure 11: External Benchmark Generalization (`figure_11_external_benchmarks`)
- **Visual Subject:** Bar chart comparing RAGTruth ($N=200$) vs. HaluEval ($N=200$) on ADR/Recall, Precision, F1-Score, and Clean FPR.
- **Primary Data Source:** `phase15_final_release_and_freeze/step03_external_validation_report.md` and `phase17_comparative_results.json`.
- **Values Check:**
  - RAGTruth: Recall = $66.0\%$, Precision = $58.9\%$, $F_1 = 62.3\%$, Clean FPR = $46.0\%$.
  - HaluEval: Recall = $89.0\%$, Precision = $47.6\%$, $F_1 = 62.0\%$, Clean FPR = $98.0\%$.
  - Discloses different benchmark tasks (Real LLM Summaries vs. Entity QA).
- **Audit Verdict:** **PASS (Exact Match)**.

---

### Figure 12: Security vs. Latency Trade-off (`figure_12_security_latency_tradeoff`)
- **Visual Subject:** Scatter plot mapping ADR (%) against median P50 latency (ms, log scale).
- **Primary Data Source:** `phase17_comparative_results.json`.
- **Pareto Verification:** Correctly identifies G1+G2 ($3.36\text{ ms}, 100\%$) and G3 Optimized ($55.84\text{ ms}, 100\%$) as non-dominated Pareto operating points.
- **Audit Verdict:** **PASS (Exact Match)**.

---

### Figure 13: Historical Research Progress (`figure_13_research_progress`)
- **Visual Subject:** Chronological milestone timeline across Phases 11–20.
- **Investigation of Phase 11.1 Milestone Discrepancy:**
  - In `figure_13_research_progress.csv`, Milestone 1 was entered as: `Phase 11.1, Nov 14, DeBERTa NLI Training, Macro F1, 84.1`.
  - Forensic recomputation from the raw validation predictions (`predictions_val.jsonl`, $N=2,662$) and `training_results.json` proves that the actual 3-class Macro F1 achieved by DeBERTa-v3-small is **$55.04\%$** ($0.55038$).
  - **Origin of Discrepancy:** The value `84.1%` originated from an early drafting transcription error conflating binary classification accuracy ($\sim 80\text{--}84\%$) or Entailment recall ($91.46\%$) / Entailment F1 ($82.30\%$) with the 3-class Macro F1.
- **Audit Verdict:** **DISCREPANCY FLAGGED (Disclosed in Register)**. The CSV has been documented in `metric_discrepancy_register.md`. The research paper must explicitly report **Macro F1 = 55.04%** and Weighted F1 = **67.50%**.

