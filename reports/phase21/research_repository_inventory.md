# TrustRAG Phase 21 — Comprehensive Research Repository Inventory

**Author:** Principal Research Scientist, ML Evaluation Auditor & Release Manager  
**Date:** 2026-11-24  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-21-final-research-validation`  
**Anchor Release Commit:** `531bff32745ede1bd1b38609cc6daf653d3eff24`  
**Anchor Release Tag:** `trustrag-v1.0.0-rc1`  
**Frozen Model Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  
**Deliverables Directory:** `reports/phase21/`

---

## 1. Executive Summary

This inventory provides an authoritative, complete accounting of all research campaigns, evaluation assets, model checkpoints, datasets, and historical audit deliverables in the TrustRAG repository. Spanning Phases 1 through 20, TrustRAG has evolved from an initial multi-signal heuristics prototype into a tri-layer defense architecture combining input safety filtering (G1), multi-signal corpus consensus gating (G2), and neural natural language inference (NLI) claim verification (G3).

All scientific evaluations are anchored to the immutable release commit `531bff32745ede1bd1b38609cc6daf653d3eff24` and the bit-for-bit verified frozen DeBERTa-v3-small NLI checkpoint.

---

## 2. Research Lifecycle & Phase Progression Matrix (Phases 1–20)

| Phase | Title / Scope | Key Deliverables & Artifacts | Empirical Outcome / Status |
|---|---|---|---|
| **Phase 01–03** | Core Heuristic Prototype & Signal Architecture | Initial query guardrails, string matching, early MSD signals | Baseline detection established; high false positive rate |
| **Phase 04** | Multi-Signal Detector (MSD) Architecture | `reports/phase04_step09_ablation_study.md`, 5-signal pipeline | First modular ablation; isolated heuristic thresholds |
| **Phase 05–07** | Adaptive Threat Evaluation & Consensus Gating | `reports/phase05_step09_adaptive_ablation.md`, `phase07_msd_ablation_report.md` | Source tiering and removal cap ($C_r = 0.50$) introduced |
| **Phase 08–10** | G2 Corpus Quarantine & Robustness Hardening | `reports/phase10_g2_ablation_report.md`, synthetic benchmark corpus | 100% ADR achieved on clean synthetic injection attacks |
| **Phase 11.1** | Neural NLI Training & Supervised Fine-Tuning | Checkpoint `deberta-v3-small-nli-phase11_1-full3epoch`, $N=10,815$ train | 70.40% val accuracy, 55.04% Macro F1, 36.22% Contradiction F1 |
| **Phase 11.2** | End-to-End Hybrid Pipeline Integration | `reports/research_completion/phase11_2_step07_08_end_to_end/` | G1+G2+G3 unified architecture verified |
| **Phase 12–14** | Multi-Document Conflict & Scalability Profiling | Phase 12/13/14 benchmark logs, retrieval benchmarking (HotpotQA, MS MARCO) | Evaluated retrieval recall and consensus under multi-doc conflicts |
| **Phase 15** | Release Candidate Preparation (`trustrag-v1.0.0-rc1`) | Release commit `531bff3`, baseline evaluations | Identified 12.50% FPR on clean controls; uncalibrated baseline |
| **Phase 16.1** | Forensic Metric Reconciliation Audit | `reports/research_completion/phase16_1_metric_reconciliation/` | Resolved denominator discrepancies (875 vs 1,000); audited 125 clean FP |
| **Phase 16.2** | Neural NLI Calibration & Clean Utility Optimization | `reports/research_completion/phase16_2_neural_utility_optimization/` | Premise citation stripping reduced clean FPR to 0.00%; latency halved |
| **Phase 17** | Independent Public Benchmark Audit | `reports/research_completion/final_independent_validation_and_release/` | Evaluated RAGTruth (46% FPR) and HaluEval (98% FPR); RSB/PoisonedRAG BLOCKED |
| **Phase 18** | Advanced Red Teaming & Security Generalization | `phase18_redteam_predictions.jsonl` ($N=460$, 15 categories) | 100% defense on 4 static categories; 0% defense on 8 adaptive categories |
| **Phase 19** | Systems Scalability & Performance Benchmarking | `phase19_performance_report.md`, memory and CPU scaling | Sub-60ms P50 latency confirmed; 2-thread CPU optimization verified |
| **Phase 20** | Component Ablation, Leakage Audit & Research Freeze | `phase20_ablation_analysis.md`, `phase20_dataset_leakage_audit.md` | Verified zero leakage between SFT and test splits; research frozen |

---

## 3. Mandatory Task Matrix

| Research task | Status | Evidence | Remaining work |
|---|:---:|---|---|
| **Task 1 — Research Repository Inventory** | **COMPLETED** | `reports/phase21/research_repository_inventory.md` | None. Full inventory published. |
| **Task 2 — Resolve Benchmark Metric Inconsistencies** | **COMPLETED** | `reports/phase21/benchmark_reconciliation.md`, `ragtruth_reconciled_results.csv`, `halueval_reconciled_results.csv` | None. RAGTruth (52% vs 46% FPR), HaluEval (N=100 vs N=200), and Macro F1 (84.1% vs 55.04%) reconciled. |
| **Task 3 — External Benchmark Evaluation (RSB, PoisonedRAG)** | **COMPLETED** | `reports/phase21/rsb_benchmark_evaluation.md`, `reports/phase21/poisonedrag_benchmark_evaluation.md` | None. Documented as strictly `BLOCKED` due to environment constraints; no synthetic substitution. |
| **Task 4 — Controlled Ablation Studies** | **COMPLETED** | `reports/phase21/ablation_study.md`, `reports/phase21/tables/ablation_metrics.csv` | None. Recomputed configs A–F across identical cohorts ($N=875$ attacks, $N=1,000$ clean). |
| **Task 5 — Contradiction Detection & NLI Audit** | **COMPLETED** | `reports/phase21/nli_diagnostic_audit.md`, `reports/phase21/confusion_matrices/nli_validation_confusion_matrix.json` | None. Macro F1 55.04%, Contradiction F1 36.22%, class imbalance root cause analyzed. |
| **Task 6 — Dataset Leakage & Contamination Audit** | **COMPLETED** | `reports/phase21/dataset_leakage_audit.md` | None. Verified 0 exact collisions across SFT train, validation, red team, and benchmark splits. |
| **Task 7 — Statistical Significance & Confidence Analysis** | **COMPLETED** | `reports/phase21/statistical_analysis.md` | None. Wilson score 95% CIs and paired tests calculated for all metrics. |
| **Task 8 — Security Generalization & Failure Analysis** | **COMPLETED** | `reports/phase21/security_generalization_audit.md` | None. Audited 15 Phase 18 red-team categories ($N=460$), analyzing 0% adaptive/Sybil failure modes. |
| **Task 9 — Research Baseline & Related Work Comparison** | **COMPLETED** | `reports/phase21/related_work_comparison.md` | None. Deep architectural comparison against HalluGuard and FilterRAG (`2508.02835v2.pdf`). |
| **Task 10 — Reproducibility Package** | **COMPLETED** | `reports/phase21/reproducibility/` (manifest, environment, configs, seeds) | None. Complete standalone reproducibility guide provided. |
| **Task 11 — Final Research Figures & Tables** | **COMPLETED** | `reports/phase21/figures/`, `reports/phase21/tables/` | None. 13 figures (PDF, PNG, SVG) and all underlying CSV datasets copied and verified. |
| **Task 12 — Research Manuscript Preparation** | **COMPLETED** | `reports/phase21/paper/TrustRAG_Research_Paper.md`, `TrustRAG_Research_Paper.tex` | None. Full 26-section academic manuscript authored in Markdown and LaTeX. |
| **Task 13 — Research Readiness Decision & Final Report** | **COMPLETED** | `reports/phase21/PHASE21_FINAL_RESEARCH_COMPLETION_REPORT.md` | None. Definitive verdict issued: `PUBLICATION READY WITH LIMITATIONS`. |

---

## 4. Model Checkpoint Inventory

- **Location:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`
- **Integrity Status:** Bit-for-bit identical to historical SHA-256 manifests.
- **Files & SHA-256 Checksums:**
  - `config.json`: `949987817ebcb00f576e2c39e247481ba93fb303530e70be38cf3f5b721e784d`
  - `pytorch_model.bin`: `f758782a17058fc3cb630256860ee1f67f0b83e659b87b2b73dbb893bb079d8a`
  - `tokenizer_config.json`: `cfd15024b89fa7ba88a53ea8f20387b99c8bfbe0aa314eb4ff1bf50284eb3b17`
  - `spm.model`: `463690d56567554f676239121d51c31405e3f4ad3692a83e02029b4724cb4d1f`
  - `special_tokens_map.json`: `a2007ff024dc5c4b143c7b20fc6abfc9825b29cb2fe98ab2dbf4bf12fb9471fc`
  - `tokenizer.json`: `2350ef91e4695eb1df677d612e4b47eb5957d1976a4ba2ec06f7532dfc282664`
  - `added_tokens.json`: `49733efd131f4ee7716f6b5b5c907bba0956b90de254c728795ff5eb578276f5`
  - `training_args.bin`: `98471fb63cbff8d1e3dbe7cfdf9d9cc2cbe48ab65b1626f2945d812423914a2a`

---

## 5. Evaluation Dataset Inventory

1. **Supervised Fine-Tuning Corpus (Phase 11.1):**
   - Train: `data/processed/sft_v2/nli/train.jsonl` ($N=10,815$)
   - Validation: `data/processed/sft_v2/nli/validation.jsonl` ($N=2,662$)
2. **Custom Security Benchmark:**
   - Raw train: `data/processed/custom_security/raw_train.jsonl` ($N=2,000$: $1,000$ clean, $1,000$ attacks including $125$ benign instruction controls; exactly $875$ genuine attacks across 7 categories)
3. **Phase 18 Advanced Red Team Dataset:**
   - Raw predictions: `reports/research_completion/final_independent_validation_and_release/raw_predictions/phase18_redteam_predictions.jsonl` ($N=460$, 15 categories)
4. **Public LLM Hallucination Benchmarks:**
   - RAGTruth (ACL 2024): $N=200$ test split ($100$ Factual, $100$ Hallucinated)
   - HaluEval (EMNLP 2023): $N=200$ test split ($100$ Factual, $100$ Hallucinated)
5. **Academic Poisoning Benchmarks:**
   - RSB (arXiv:2505.18543): `BLOCKED` (No local staging; network downloads prohibited)
   - PoisonedRAG (USENIX Security 2025): `BLOCKED` (No local staging; network downloads prohibited)
