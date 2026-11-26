# TrustRAG Phase 21 — Index of Publication Figures & Visual Assets

**Directory:** `reports/phase21/figures/`  
**Underlying Data:** `reports/phase21/tables/`  
**Formats Available:** High-resolution PNG (300 DPI), Vector PDF, Vector SVG  

---

## 1. Catalog of Scientific Figures

| Figure | Title / Focus | Formats | Source Data File | Key Scientific Takeaway |
|:---:|---|:---:|---|---|
| **Fig 01** | **Overall Architecture Comparison** | PNG, PDF, SVG | `tables/figure_01_architecture_comparison.csv` | Compares ADR, ASR, clean FPR, and clean delivery across Standard RAG, G1, G1+G2, Baseline G3, and Optimized G3. |
| **Fig 02** | **Attack Defense Performance by Category** | PNG, PDF, SVG | `tables/figure_02_attack_defense.csv` | Category-level detection rate across synthetic attack vectors ($N=875$). |
| **Fig 03** | **Clean Utility Comparison** | PNG, PDF, SVG | `tables/figure_03_clean_utility.csv` | Isolates clean FPR drop from 12.50% (Baseline) to 0.00% (Optimized) with Wilson 95% CIs. |
| **Fig 04** | **NLI Confusion Matrix** | PNG, PDF, SVG | `tables/figure_04_nli_confusion_matrix.csv` | Complete $3 \times 3$ confusion matrix for frozen DeBERTa-v3-small on held-out validation ($N=2,662$). |
| **Fig 05** | **Class-wise Model Performance** | PNG, PDF, SVG | `tables/figure_05_classwise_metrics.csv` | Precision, recall, and F1 across Entailment (82.3%), Neutral (46.6%), and Contradiction (36.2%). |
| **Fig 06** | **NLI Confidence Calibration** | PNG, PDF, SVG | `tables/figure_06_calibration.csv` | Reliability diagram demonstrating temperature scaling improvement ($ECE: 0.142 \to 0.048$). |
| **Fig 07** | **CPU Inference Latency Distribution** | PNG, PDF, SVG | `tables/figure_07_cpu_latency.csv` | Latency breakdown across P50, P90, P95, and P99 showing 55.84 ms median CPU latency. |
| **Fig 08** | **Batch Throughput Scaling** | PNG, PDF, SVG | `tables/figure_08_batch_throughput.csv` | Throughput scaling (queries/sec) as batch size increases on multi-core CPU. |
| **Fig 09** | **Memory Consumption Profile** | PNG, PDF, SVG | `tables/figure_09_memory_profile.csv` | Resident set size (RSS) footprint across pipeline stages (< 500 MB footprint). |
| **Fig 10** | **Advanced Red-Team Security Heatmap** | PNG, PDF, SVG | `tables/figure_10_redteam_heatmap.csv` | Defense performance across all 15 Phase 18 adversarial attack categories ($N=460$). |
| **Fig 11** | **External Benchmark Generalization** | PNG, PDF, SVG | `tables/figure_11_external_benchmarks.csv` | Empirical ADR and Clean FPR on commercial LLM generations (RAGTruth and HaluEval). |
| **Fig 12** | **Security vs Latency Frontier** | PNG, PDF, SVG | `tables/figure_12_security_latency_tradeoff.csv` | Pareto frontier mapping ADR against P50 latency across all system configurations. |
| **Fig 13** | **Research Progression Across Phases** | PNG, PDF, SVG | `tables/figure_13_research_progress.csv` | Chronological progression of ADR, clean delivery, and latency across development phases. |

---

## 2. Integrity Verification
All 13 figures have been audited against their source CSVs. Denominators, confidence intervals, and axis labels match the reconciled empirical records exactly.
