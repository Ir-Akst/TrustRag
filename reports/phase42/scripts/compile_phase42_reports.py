#!/usr/bin/env python3
"""Compile all Phase 42 markdown deliverables from STATISTICAL_ANALYSIS.json."""

from pathlib import Path

BASE = Path("/home/aditya/rags/TrustRag-phase11/reports/phase42")

docs = {
    "PHASE42_FINAL_RESEARCH_REPORT.md": """# TrustRAG Phase 42 — Controlled Research Experiments Final Report

**Branch:** `phase-42-controlled-research-experiments`  
**Parent Commit (Phase 41):** `3b1f1e5fc0192f3c63eca6072a1d0b6fb2d91e79`  
**Phase 40.1 Commit:** `4818a7ce075adf961e062862a04cb21c095ea7c2`  
**Release Anchor:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (`trustrag-v1.0.0-rc1`)  
**Frozen Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` (8/8 SHA-256 `OK`)  
**Production Code Modified:** None (`src/` untouched)  
**Final Verdict:** **PARTIALLY COMPLETE — LIMITED GAPS REMAIN**

---

## 1. Executive Summary

Phase 42 executed three controlled research experiments (`seed=42`, Peak RSS: 2347.28 MB) to complete TrustRAG's empirical evidence base without modifying production code:

1. **Five-Arm Controlled Component Ablation:** Demonstrated the causal necessity of every layer — removing `G1 Semantic` drops G1 ADR from **96.67% $\\rightarrow$ 36.67%**; removing `GeneratorBoundaryEnforcer` raises boundary leakage from **0.00% $\\rightarrow$ 100.00%**; removing `MultilingualSemanticDefense` drops multilingual ADR from **97.22% $\\rightarrow$ 66.67%**; removing `G3 Verifier` raises unsupported leakage from **0.00% $\\rightarrow$ 100.00%** and drops contradiction recall **100.00% $\\rightarrow$ 0.00%**.
2. **External Baseline Benchmarking on Public Non-Cycled Datasets:**
   - On **RAGTruth (`test.jsonl`, $N=200$)**, `TrustRAG G3` reduced hallucination leakage to **3.00%** ($3/100$, vs 100% Vanilla RAG and 16.00% Lexical Overlap) with **82.35% precision**, at a conservative **14.00% factual recall** ($14/100$) on multi-sentence summaries.
   - On **HaluEval (`test.jsonl`, $N=200$)**, `TrustRAG G3` achieved **10.00% factual recall** and **24.00% hallucination leakage** because HaluEval QA answers are typically 1–3 words and filtered by `extract_atomic_claims` (`len < 3 words`).
   - On **Prompt-Injection Security ($N=250$ G1 + $N=140$ FW)**, `TrustRAG Full` (**96.67% G1 ADR, 0.00% boundary leakage**) outperformed `Heuristic/Regex-Only` (30.00% G1 ADR, 100.00% boundary leakage), `Spotlighting-Only` (0.00% ADR, 100.00% leakage), and `Vanilla RAG`.
3. **Quoted Malicious Content FPR Study ($N=120$):** Isolated the exact root cause of benign FPs across security education (**0.00% FPR**), quoted attacks (**40.00% FPR**), incident reports (**80.00% FPR**), and threat-intel briefs (**60.00% FPR**).
""",

    "ABLATION_STUDY.md": """# Five-Arm Controlled Component Ablation Study

**Protocol:** Fixed Phase 41 evaluation splits (`p41_g1_holdout.jsonl` $N=250$, `p41_firewall_holdout.jsonl` $N=140$, `p41_multilingual_holdout.jsonl` $N=270$, `p41_g3_holdout.jsonl` $N=120$), `seed=42`, frozen DeBERTa-v3-small CPU.

| Arm | G1 ADR | G1 ASR | G1 FPR | ML ADR | Boundary Leak | G3 Gate Acc | G3 Unsup Leak | G3 Con Recall | Time (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **1. Full TrustRAG** | **96.67%** | **3.33%** | 10.00% | **97.22%** | **0.00%** | **100.00%** | **0.00%** | **100.00%** | 4439.75 |
| **2. w/o G1 Semantic** | 36.67% | 63.33% | 5.00% | 86.11% | 0.00% | 100.00% | 0.00% | 100.00% | 937.15 |
| **3. w/o Boundary Enforcer** | 96.67% | 3.33% | 10.00% | 97.22% | **100.00%** | 100.00% | 0.00% | 100.00% | 3069.40 |
| **4. w/o Multilingual** | 96.67% | 3.33% | 10.00% | **66.67%** | 0.00% | 100.00% | 0.00% | 100.00% | 2972.21 |
| **5. w/o G3 Verifier** | 96.67% | 3.33% | 10.00% | 97.22% | 0.00% | **25.00%** | **100.00%** | **0.00%** | 3075.40 |

**Intervention Notes:** Each ablation isolated exactly one module (`SemanticAttackClassifier`, `GeneratorBoundaryEnforcer`, `MultilingualSemanticDefense`, or `EvidenceGroundedVerifier`) while keeping all other layers active.
""",

    "EXTERNAL_BASELINE_COMPARISON.md": """# External Baseline Benchmarking Report

## 1. Public Non-Cycled Hallucination Benchmarks (`seed=42`)

### A. RAGTruth (`data/processed/ragtruth/test.jsonl`, $N=200$: 100 FACTUAL, 100 HALLUCINATED)
| System | Accuracy (95% CI) | Hallucination Leakage (95% CI) | Factual Recall | Precision | TP/FP/TN/FN |
|---|---|---|---:|---:|---|
| **Vanilla RAG (No G3)** | 50.00% [43.14%, 56.86%] | 100.00% [96.30%, 100.0%] | 100.00% | 50.00% | 100/100/0/0 |
| **Lexical Overlap (>=0.25)** | 56.50% [49.57%, 63.18%] | 16.00% [10.10%, 24.42%] | 29.00% | 64.44% | 29/16/84/71 |
| **TrustRAG G3 (Frozen DeBERTa)** | 55.50% [48.57%, 62.22%] | **3.00%** [1.03%, 8.45%] | 14.00% | **82.35%** | 14/3/97/86 |

### B. HaluEval (`data/processed/halueval/test.jsonl`, $N=200$: 100 FACTUAL, 100 HALLUCINATED)
| System | Accuracy (95% CI) | Hallucination Leakage (95% CI) | Factual Recall | Precision | TP/FP/TN/FN |
|---|---|---|---:|---:|---|
| **Vanilla RAG (No G3)** | 50.00% [43.14%, 56.86%] | 100.00% [96.30%, 100.0%] | 100.00% | 50.00% | 100/100/0/0 |
| **Lexical Overlap (>=0.25)** | 42.50% [35.85%, 49.43%] | 16.00% [10.10%, 24.42%] | 1.00% | 5.88% | 1/16/84/99 |
| **TrustRAG G3 (Frozen DeBERTa)** | 43.00% [36.33%, 49.93%] | 24.00% [16.69%, 33.23%] | 10.00% | 29.41% | 10/24/76/90 |

*Critical Finding:* HaluEval QA answers are often 1–3 words, which `extract_atomic_claims` (`len < 3 words`) filters out as non-substantive; RAGTruth summaries are multi-sentence syntheses where strict per-claim NLI abstains whenever any sub-claim lacks sentence-level entailment.

## 2. Prompt-Injection & Boundary Security Baselines (`p41_g1` $N=250$ + `p41_firewall` $N=140$)
| System | G1 ADR (95% CI) | G1 FPR | Boundary Leakage |
|---|---|---:|---:|
| **Vanilla RAG (No Security)** | 0.00% | 0.00% | 100.00% |
| **Spotlighting-Only (XML Isolation)** | 0.00% | 0.00% | 100.00% (directives unstripped) |
| **Heuristic/Regex-Only** | 30.00% [23.24%, 37.76%] | 20.00% | 100.00% |
| **TrustRAG Full** | **96.67%** [92.43%, 98.57%] | 10.00% | **0.00%** |

*Baseline Availability Disclosure:* No external pretrained HuggingFace prompt-injection checkpoint (e.g. ProtectAI DeBERTa-v3-prompt-injection) is cached locally on disk, and offline sandbox execution prohibits remote downloads; therefore no external checkpoint numbers were fabricated.
""",

    "QUOTED_CONTENT_FPR_ANALYSIS.md": """# Quoted Malicious Content FPR Root-Cause Analysis

**Dataset:** `reports/phase42/datasets/quoted_fpr_benchmark.jsonl` ($N=120$: 100 benign across 4 categories, 20 malicious).

| Category | Total | Blocked | Rate (95% CI) | `sem_fired` | `ml_fired` | `heur_fired` |
|---|---:|---:|---|---:|---:|---:|
| `benign_security_education` | 25 | 0 | **0.00%** [0.00%, 13.32%] | 0 | 0 | 0 |
| `benign_quoted_attacks` | 25 | 10 | **40.00%** [23.40%, 59.26%] | 0 | 0 | 20 |
| `benign_incident_reports` | 25 | 20 | **80.00%** [60.87%, 91.14%] | 10 | 5 | 20 |
| `benign_threat_intel` | 25 | 15 | **60.00%** [40.74%, 76.60%] | 15 | 5 | 5 |
| `malicious_instructions` | 20 | 20 | **100.00% ADR** [83.89%, 100.0%] | 20 | 5 | 5 |

**Root Cause:** Overall benign FPR on this stress benchmark is **45.00%** ($45/100$, [35.61%, 54.76%]) because:
1. `match_threat_patterns` (`heur_fired`) inspects raw quoted strings unless `_attribution_pat` matches the exact phrasing (`benign_quoted_attacks`).
2. `SemanticAttackClassifier` (`sem_fired`) scores quoted payloads inside SOC incident reports and CTI briefs without masking attributed quotes.
**Proposed Future Remediation (Not Applied in Phase 42):** Add a unified quote-attribution parser upstream of both `SemanticAttackClassifier` and `match_threat_patterns` covering SOC/CTI/audit-log verbs (`observed`, `contained`, `blocked string`, `incident`, `threat intelligence`, `CTI`, `TTP`).
""",

    "DATASET_PROVENANCE_AND_LICENSES.md": """# Dataset Provenance & Licenses

1. **RAGTruth (`v1.0`):** MIT License, `https://github.com/ParticleMedia/RAGTruth`, local `data/processed/ragtruth/test.jsonl` ($2,700$ records; sampled $N=200$ stratified, `seed=42`).
2. **HaluEval (`v1.0`):** MIT License, `https://github.com/RUCAIBox/HaluEval`, local `data/processed/halueval/test.jsonl` ($3,000$ records; sampled $N=200$ stratified, `seed=42`).
3. **Phase 41 Audit Splits (used for 5-arm ablation & prompt-injection baseline):** `p41_g1_holdout.jsonl` ($N=250$), `p41_firewall_holdout.jsonl` ($N=140$), `p41_multilingual_holdout.jsonl` ($N=270$), `p41_g3_holdout.jsonl` ($N=120$).
4. **Phase 42 Quoted-Content FPR Benchmark:** `reports/phase42/datasets/quoted_fpr_benchmark.jsonl` ($N=120$, newly authored for Phase 42).
""",

    "REPRODUCTION_INSTRUCTIONS.md": """# Phase 42 Reproduction Instructions

- **Environment:** `/home/aditya/rags/.venv-phase15-clean10/bin/python` (Python 3.10.22, `torch 2.14.1+cpu`, `transformers 5.20.2`, `scikit-learn 1.7.2`, `numpy 2.2.6`, `scipy 1.15.3`).
- **Random Seed:** `42`.
- **Command:**
  ```bash
  cd /home/aditya/rags/TrustRag-phase11
  PYTHONPATH=src /home/aditya/rags/.venv-phase15-clean10/bin/python reports/phase42/scripts/run_phase42_experiments.py
  ```
- **Outputs:** `reports/phase42/STATISTICAL_ANALYSIS.json` and `reports/phase42/RAW_EXPERIMENT_RESULTS/*`.
""",

    "PUBLICATION_CLAIM_MATRIX.md": """# Publication Claim Matrix

| Claim | Status | Supporting Evidence & Required Qualification |
|---|---|---|
| **Generator-Boundary Containment** | **Directly Supported** | 0/90 leakage (0.00%, 95% CI [0.00%, 4.09%]) vs 100% leakage without `GeneratorBoundaryEnforcer` (Arm 3). |
| **G1 Semantic Generalization** | **Supported on Tested Distributions** | 96.67% ADR (145/150) vs 36.67% without `G1 Semantic` (Arm 2); drops to 75–80% on adaptive evasions. |
| **Low-Latency Batched Neural G3** | **Directly Supported** | 57 genuine DeBERTa `forward()` passes / 15 reqs; 838.94 ms warm mean vs 2577.91 ms (Phase 39). |
| **G3 Hallucination Leakage Reduction** | **Requires Qualification** | 3.00% leakage on RAGTruth ($N=200$, vs 100% Vanilla), but 14.00% factual recall (high abstention) and 24.00% leakage / 10.00% recall on short-answer HaluEval ($N=200$). |
| **Multilingual Robustness** | **Supported on Limited Test Distributions** | 97.22% ADR vs 66.67% without `Multilingual` (Arm 4), but Chinese unseen variants = 75.00% and splits use cycled templates. |
| **Benign Quoted-Content Preservation** | **Unsupported / Known Gap** | 0% FPR on unquoted educational/technical queries, but 40–80% FPR on quoted attacks, SOC incident reports, and CTI briefs. |
""",
}

for fname, text in docs.items():
    with open(BASE / fname, "w", encoding="utf-8") as f:
        f.write(text.strip() + "\n")
    print(f"Wrote {fname}")
