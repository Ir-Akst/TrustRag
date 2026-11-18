# TrustRAG Publication-Quality Research Figure Index

This index catalogs the complete collection of publication-quality research figures generated for the TrustRAG master research report, peer-reviewed academic papers, and technical presentations.

Every figure is backed by underlying empirical CSV data in `data/`, generated via `scripts/generate_publication_figures.py`, and exported in 300 DPI PNG, vector PDF, and vector SVG formats.

---

## Catalog of Research Figures

| Figure Number | Filename Identifier | Title & Scientific Subject | Primary Data Source | Evaluation Cohort & Sample Size ($N$) | Key Empirical Interpretation |
|---|---|---|---|:---:|---|
| **Figure 1** | `figure_01_architecture_comparison` | Overall Architecture Comparison: Security vs Clean Utility | `phase17_comparative_results.json` | $N=875$ Attacks, $N=1,000$ Controls | Proves G1+G2 achieves $100\%$ defense on synthetic attacks while premise normalization in G3 restores $100\%$ clean delivery ($0\%$ FPR). |
| **Figure 2** | `figure_02_attack_defense` | Attack Defense Performance Across Security Categories | `phase13_generalization_and_hardening` | $N=1,000$ ($N=125$ per category) | Visualizes per-category defense rates across Standard RAG, G1, G1+G2, and G3 Optimized across 8 attack categories. |
| **Figure 3** | `figure_03_clean_utility` | Clean Utility Impact of Premise Citation Normalization | `phase16_2_neural_utility_optimization` | $N=1,000$ Clean Controls | Demonstrates remediation of astrophysical false alarms: clean FPR drops from $12.50\% 	o 0.00\%$ with Wilson 95% CIs. |
| **Figure 4** | `figure_04_nli_confusion_matrix` | DeBERTa-v3-small NLI Confusion Matrix on Validation Set | `predictions_val.jsonl` | $N=2,662$ Held-Out Validation Pairs | Visualizes normalized classification matrix across Entailment ($91.5\%$), Neutral ($41.0\%$), and Contradiction ($25.3\%$). |
| **Figure 5** | `figure_05_classwise_metrics` | Class-wise Model Performance: Precision, Recall, F1 | `predictions_val.jsonl` | $N=2,662$ Held-Out Validation Pairs | Class-specific metrics: Entailment F1=$82.3\%$, Neutral F1=$46.6\%$, Contradiction F1=$36.2\%$, Macro F1=$55.0\%$, Weighted F1=$67.5\%$. |
| **Figure 6** | `figure_06_calibration` | Calibration Reliability Diagram: Temperature Scaling | `predictions_val.jsonl` | $N=2,662$ Validation ($T=1.7701$) | Displays predicted confidence vs observed accuracy; proves Expected Calibration Error drops from $15.01\% 	o 3.06\%$ after scaling. |
| **Figure 7** | `figure_07_cpu_latency` | CPU Intra-Op Thread Latency Benchmarks (1, 2, 4, 8 Threads) | `phase19_scalability_results.json` | 20 Iterations per Thread Configuration | Proves 2 CPU threads is the optimal operating sweet spot ($55.84	ext{ ms}$ P50, $1.73	imes$ speedup) avoiding cache thrashing at 4+ threads. |
| **Figure 8** | `figure_08_batch_throughput` | Batched Inference Latency and Sustained Throughput | `phase19_scalability_results.json` | Batch Sizes $B \in [1, 2, 4, 8, 16, 32]$ | Demonstrates batched forward passes maintain steady per-claim latency ($\sim 80	ext{ ms}$) yielding $>12	ext{ claims/sec}$ on CPU. |
| **Figure 9** | `figure_09_memory_profile` | Operational Memory Footprint and Headroom Margin | `phase19_scalability_results.json` | Standalone CPU x86_64 Profiling | Details RAM allocation: Baseline $289	ext{ MB}$, Loaded $728	ext{ MB}$, Peak $774	ext{ MB}$, fitting comfortably inside $1.5	ext{ GB}$ container envelope. |
| **Figure 10** | `figure_10_redteam_heatmap` | Advanced Security Red Teaming Evaluation across 15 Vectors | `phase18_attack_dataset_manifest.json` | $N=460$ Real Red-Team Attacks | Discloses the red-team frontier: $100\%$ defense on character/narrative vectors, but $0\%	ext{--}33\%$ on Sybil consensus, paraphrase, and code injection. |
| **Figure 11** | `figure_11_external_benchmarks` | Independent Public Benchmark Generalization: RAGTruth vs HaluEval | `phase15_final_release_and_freeze` | $N=200$ Balanced Samples Each | Demarcates the Generalization Reality Gap: RAGTruth F1=$62.3\%$ (FPR=$46\%$) vs HaluEval F1=$62.0\%$ (FPR=$98\%$ Propositional Dilemma). |
| **Figure 12** | `figure_12_security_latency_tradeoff` | Security Defense Rate vs. Inference Latency Pareto Trade-off | `phase17_comparative_results.json` | Multi-Configuration Pareto Analysis | Maps the Pareto frontier: G1+G2 ($3.36	ext{ ms}, 100\%$ synthetic) to G3 Optimized ($55.84	ext{ ms}, 100\%$ deep inspection). |
| **Figure 13** | `figure_13_research_progress` | Empirical Research Milestones Across Phases 11–20 | Phases 11–20 Research Completion Reports | 10 Sequential Empirical Milestones | Chronological timeline tracing NLI training, discrepancy resolution, baseline audits, premise normalization, and final freeze. |

---

## Reproduction Commands

To reproduce all 13 figures, CSV datasets, and exports:

```bash
cd /home/aditya/rags/TrustRag-phase11
export MPLCONFIGDIR=/tmp/mplconfig
/usr/bin/python3 reports/research_completion/final_research_freeze/figures/scripts/generate_publication_figures.py
```
