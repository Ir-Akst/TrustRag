# TrustRAG Phase 41 — Independent Final Research Audit

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
