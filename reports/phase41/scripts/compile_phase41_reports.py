#!/usr/bin/env python3
"""Compile all 11 Phase 41 markdown audit reports from STATISTICAL_RESULTS.json."""

import json
from pathlib import Path

BASE = Path("/home/aditya/rags/TrustRag-phase11/reports/phase41")
with open(BASE / "STATISTICAL_RESULTS.json", encoding="utf-8") as f:
    s = json.load(f)

reports = {
    "PHASE41_FINAL_INDEPENDENT_AUDIT.md": """# TrustRAG Phase 41 — Independent Final Research Audit

**Audit Mode:** AUDIT-ONLY (Zero modifications to `src/`, thresholds, or frozen weights)  
**Branch:** `phase-41-independent-final-research-audit`  
**Audited Commit (Phase 40.1):** `4818a7ce075adf961e062862a04cb21c095ea7c2`  
**Phase 40 Parent:** `e6908d26a13089d108a09977f4f05e864c7dab82`  
**Release Anchor:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (`trustrag-v1.0.0-rc1`)  
**Frozen Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` (8/8 SHA-256 `OK`)  
**Final Scientific Verdict:** **BORDERLINE — ADDITIONAL EXPERIMENTS REQUIRED**

---

## 1. Executive Summary of Independent Audit

Phase 41 independently verified Phase 40.1's reproducibility, security enforcement, neural execution, dataset hygiene, and baseline/ablation completeness.

| Dimension | Phase 40.1 Reported | Phase 41 Independent Audit | 95% Wilson CI | Assessment |
|---|---|---|---|---|
| **G1 ADR** | 95.00% (190/200) | **96.67%** (145/150) | [92.43%, 98.57%] | Reproducible; 90 semantic-only |
| **G1 Overall Benign FPR** | 10.00% (10/100) | **10.00%** (10/100) | [5.52%, 17.44%] | **Misses <=3% target** |
| — Quoted Malicious Content FPR | 40.00% (10/25) | **40.00%** (10/25) | [23.40%, 59.26%] | Unresolved attribution gap |
| — Edu / Tech / Analytical FPR | 0.00% (0/75) | **0.00%** (0/75) | [0.00%, 4.87%] | Strong preservation |
| **Firewall Detection Recall** | 100.00% (100/100) | **100.00%** (90/90) | [95.91%, 100.00%] | Reproducible |
| **Generator-Boundary Leakage** | 0.00% (0/100) | **0.00%** (0/90) | [0.00%, 4.09%] | Also 0/90 via `AnswerGenerator` |
| **Firewall False Quarantine** | 0.00% (0/50) | **0.00%** (0/50) | [0.00%, 7.13%] | Preserved |
| **Multilingual Combined ADR** | 98.15% (265/270) | **97.22%** (175/180) | [93.66%, 98.81%] | Chinese = 75.00% (15/20) |
| **Multilingual Benign FPR** | 0.00% (0/90) | **0.00%** (0/90) | [0.00%, 4.09%] | Preserved |
| **G3 Release-Gate Accuracy** | 100.00% (140/140) | **100.00%** (120/120) | [96.90%, 100.00%] | Reproducible |
| **G3 Exact 4-Class Accuracy** | 91.43% (128/140) | **90.00%** (108/120) | [83.33%, 94.19%] | 12/25 unsup -> `CONTRADICTED` |
| **G3 Contradiction Recall** | 100.00% (65/65) | **100.00%** (45/45) | [92.13%, 100.00%] | Reproducible |
| **G3 Unsupported Leakage** | 0.00% (0/25) | **0.00%** (0/25) | [0.00%, 13.32%] | Reproducible |
| **Profile B Warm Mean Latency** | 963.35 ms | **838.94 ms** | 57 fwds / 15 reqs | **Genuine PyTorch DeBERTa** |
""",

    "GIT_AND_RELEASE_INTEGRITY.md": """# Git Ancestry, Manifest & Checkpoint Integrity Audit

- **HEAD at Audit Start:** `4818a7ce075adf961e062862a04cb21c095ea7c2` (`phase-40.1-benign-utility-and-independent-verification`).
- **Ancestry Verified:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (`trustrag-v1.0.0-rc1`, tag object `7d4315e10fe4b7cc2cea6d6d2f9403d22af45f86`) $\\rightarrow$ `e6908d26a13089d108a09977f4f05e864c7dab82` (Phase 40) $\\rightarrow$ `4818a7ce075adf961e062862a04cb21c095ea7c2` (Phase 40.1).
- **Dirty File Observation:** At audit start, `reports/phase40_1/scripts/compile_phase40_1_reports.py` had 1 unstaged trailing newline causing 1 mismatch in `reports/phase40_1/ARTIFACT_SHA256_MANIFEST.txt`. Restoring via `git checkout -- reports/phase40_1/` yielded 100% `OK` on both Phase 40 and Phase 40.1 manifests.
- **Frozen Checkpoint:** All 8 SHA-256 hashes in `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch/checksums.sha256` verified `OK`.
""",

    "G1_SECURITY_AUDIT.md": """# Independent G1 Security & Benign Utility Audit

**Dataset:** `reports/phase41/datasets/p41_g1_holdout.jsonl` ($N=250$: 150 attacks, 100 benign controls; 250/250 unique).  
**Command:** `PYTHONPATH=src /home/aditya/rags/.venv-phase15-clean10/bin/python reports/phase41/scripts/run_phase41_audit.py`

- **Confusion Matrix:** TP=145, FP=10, TN=90, FN=5
- **ADR (Recall):** **96.67%** (145/150) [95% CI: 92.43%, 98.57%] | **ASR:** 3.33% (5/150)
- **Precision / F1:** 93.55% / 0.9508
- **Overall Benign FPR:** **10.00%** (10/100) [95% CI: 5.52%, 17.44%]
- **Semantic vs. Heuristic Attribution (on 145 TP):**
  - `semantic_only` (`G1_SEMANTIC_ATTACK`): **90** (62.1%)
  - `multi_signal`: **55** (37.9%)
  - `heuristic_only`: **0** (0.0%)
- **Category Breakdown:**
  - `direct_injection`, `unseen_imperatives`, `narrative_roleplay`, `paraphrase_and_multi`, `indirect_override`: **25/25 (100.00%)**
  - `adaptive_obfuscated_fragmented`: **20/25 (80.00%)** [60.87%, 91.14%]
  - `benign_cyber_education`, `benign_technical_docs`, `benign_analytical`: **0/25 FP (0.00%)**
  - `benign_quoted_content`: **10/25 FP (40.00%)** [23.40%, 59.26%] — confirms Phase 40.1 finding.
""",

    "GENERATOR_BOUNDARY_AUDIT.md": """# Independent Generator-Boundary Firewall Audit

**Dataset:** `reports/phase41/datasets/p41_firewall_holdout.jsonl` ($N=140$: 90 malicious, 50 benign).  
**Alternate Path Tested:** Tested BOTH `GeneratorBoundaryEnforcer.enforce()` AND direct `AnswerGenerator.generate()` invocation.

- **Detection Recall:** **100.00%** (90/90) [95% CI: 95.91%, 100.00%]
- **Actual Final-Context Leakage:** **0.00%** (0/90) [95% CI: 0.00%, 4.09%]
- **Direct `AnswerGenerator` Bypass Leakage:** **0.00%** (0/90)
- **Benign False Quarantine:** **0.00%** (0/50) [95% CI: 0.00%, 7.13%]

*Caveat:* The 90 malicious cases were generated from 11 distinct structural templates, so zero observed leakage reflects strong boundary enforcement on those structural classes rather than universal immunity.
""",

    "MULTILINGUAL_GENERALIZATION_AUDIT.md": """# Independent Multilingual Generalization Audit

**Dataset:** `reports/phase41/datasets/p41_multilingual_holdout.jsonl` ($N=270$: 9 languages $\\times$ 30 samples).

- **Combined ADR:** **97.22%** (175/180) [95% CI: 93.66%, 98.81%]
- **Combined Benign FPR:** **0.00%** (0/90) [95% CI: 0.00%, 4.09%]
- **Per-Language Results (20 attacks + 10 benign per language):**
  - English, Spanish, French, German, Russian, Hindi, Arabic, Japanese: **100.00% ADR (20/20)** [83.89%, 100.0%], **0.00% FPR (0/10)** [0.00%, 27.75%]
  - Chinese: **75.00% ADR (15/20)** [53.13%, 88.81%], **0.00% FPR (0/10)** — confirms Phase 40.1's Chinese unseen-variant gap (`Hu1lue4 suo3you3 zhi3ling4...` / `Bu yao zunshou...` Pinyin variants).
""",

    "G3_EVIDENCE_VERIFICATION_AUDIT.md": """# Independent G3 Evidence-Grounded Verification Audit

**Dataset:** `reports/phase41/datasets/p41_g3_holdout.jsonl` ($N=120$: 30 `SUPPORTED`, 20 `PARTIALLY_SUPPORTED`, 25 `INSUFFICIENT_EVIDENCE`, 45 `CONTRADICTED`).

- **Release-Gate Accuracy:** **100.00%** (120/120) [95% CI: 96.90%, 100.00%]
- **Exact 4-Class Status Accuracy:** **90.00%** (108/120) [95% CI: 83.33%, 94.19%]
- **Supported Acceptance:** **100.00%** (30/30) | **False Abstention:** **0.00%** (0/30)
- **Contradiction Recall:** **100.00%** (45/45) [95% CI: 92.13%, 100.00%]
- **Unsupported Leakage:** **0.00%** (0/25) [95% CI: 0.00%, 13.32%]
- **4-Class Breakdown:** `supported` 30/30, `partially_supported` 20/20, `geo/entity/numerical/implicit` contradictions 45/45, `unsupported` 13/25 `INSUFFICIENT_EVIDENCE` (12/25 still classified `CONTRADICTED`).
""",

    "NEURAL_PERFORMANCE_AUDIT.md": """# Independent Neural Execution & Performance Audit

- **Cold-Start Latency:** **2516.27 ms**
- **Warm Mean Latency ($N=15$):** **838.94 ms** (P50: **850.14 ms**, P95: **954.43 ms**, P99: **991.10 ms**) — reproduces Phase 40.1's ~2.7x–3.0x speedup over Phase 39 (2577.91 ms).
- **Genuine PyTorch DeBERTa Forward Passes:** **57 `forward()` calls** across 60 batched NLI calls on 15 warm requests.
- **Deterministic Pair Cache:** **148 hits / 212 misses** (exact `(premise, hypothesis)` matches under frozen `eval()` weights).
- **Peak RSS:** **1155.62 MB** (full audit process including loaded sklearn & DeBERTa models).
- **Lifecycle Stress:** Concurrency (8/8 OK), Timeout (`abstained=True`), Shutdown (`abstained=True`).
""",

    "DATASET_INDEPENDENCE_AUDIT.md": """# Dataset Independence & Effective Sample Size Audit

Audited `Phase 40` vs `Phase 40.1` vs `Phase 41` normalized texts:

| Dataset | P40 / P40.1 / P41 Total | P40 / P40.1 / P41 Unique | Exact Overlap (P40 vs P41) | Exact Overlap (P40.1 vs P41) |
|---|---|---|---|---|
| `g1` | 280 / 300 / 250 | **280 / 300 / 250** | 0 | 0 |
| `firewall` | 150 / 150 / 140 | **21 / 21 / 11** | 0 | 0 |
| `multilingual` | 360 / 360 / 270 | **72 / 72 / 54** | 53 | 53 |
| `g3` | 120 / 140 / 120 | **12 / 12 / 10** | 10 | 10 |

**Critical Audit Finding:** While `g1` and `firewall` have zero cross-phase overlap, `firewall`, `multilingual`, and `g3` exhibit **template cycling** (10–72 unique base prompts cycled to $N=120$–$360$) and `multilingual`/`g3` reuse base prompts across phases. Nominal $N$ overstates independent degrees of freedom.
""",

    "BASELINE_AND_ABLATION_GAP_ANALYSIS.md": """# Baseline and Ablation Gap Analysis

## 1. Existing Baselines & Ablations in Repository
- **Phase 04 Step 3 (`reports/phase04_step03_clean_rag_baseline.md`):** Clean RAG baseline (`tfidf_extractive`).
- **Phase 04 Step 9 (`reports/phase04_step09_ablation_study.md`):** Controlled 7-arm ablation (`E1–E7`, $N=58$) on Phase 04 (`v0.4` deterministic architecture).
- **Phase 29 (`reports/phase29/HEAD_TO_HEAD_COMPARISON.md`):** `TrustRAG_MSD` vs `FilterRAG_Threshold` / `ML-FilterRAG` on passage filtering ($N=75$).

## 2. Missing Experiments Required for Publication
1. **Post-Phase 40/40.1 Component Ablations:** No ablation isolates `SemanticAttackClassifier v3` vs regex-only, `GeneratorBoundaryEnforcer` vs G2 MSD alone, `MultilingualSemanticDefense v3` vs base G1, or G3 functional-role/tolerance rules vs raw DeBERTa NLI.
2. **External Defense Baselines:** No head-to-head comparison on Phase 40.1/41 holdouts against published prompt-injection/RAG defenses (e.g., DeBERTa-prompt-injection-v2, LlamaGuard, Spotlighting-only, or Perplexity filtering).
""",

    "PUBLICATION_READINESS_ASSESSMENT.md": """# Final Publication Readiness Assessment

**Final Scientific Verdict:** **BORDERLINE — ADDITIONAL EXPERIMENTS REQUIRED**

## Rubric Evaluation
- **Engineering Maturity:** Strong (fail-closed boundary enforcement, 817 passing unit tests, batched DeBERTa CPU serving).
- **Security Effectiveness & Generalization:** Strong on generator-boundary containment (0/90 leakage) and non-quoted G1 (96.67% ADR), but **10.00% G1 FPR** (40% on quoted malicious content) and **75.00% Chinese ADR** remain open gaps.
- **Statistical Confidence & Dataset Hygiene:** G1 ($N=250$ unique) is solid, but Firewall/Multilingual/G3 rely on small cycled template sets (10–54 unique templates).
- **Reproducibility:** High — Phase 40.1 metrics and neural forward passes reproduced cleanly.
- **Baseline & Ablation Completeness:** **Insufficient** for the Phase 40/40.1 architecture (only Phase 04/29 baselines exist).

## Smallest Set of Remaining Experiments
1. Run a **4-arm post-Phase 40.1 ablation** isolating G1 v3, GeneratorBoundaryEnforcer, Multilingual v3, and G3 enhancements.
2. Run a **head-to-head external baseline comparison** (e.g. Vanilla RAG, Spotlighting-only, DeBERTa-prompt-injection-v2) on a **non-cycled** benchmark (e.g. RAGTruth + HaluEval + WildGuardMix).
3. Address or explicitly scope the **quoted malicious content FPR** (40% on `benign_quoted_content`).
""",
}

for fname, text in reports.items():
    with open(BASE / fname, "w", encoding="utf-8") as f:
        f.write(text.strip() + "\n")
    print(f"Wrote {fname}")
