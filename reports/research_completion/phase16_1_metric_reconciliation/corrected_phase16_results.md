# TrustRAG Phase 16.1 — Corrected Benchmark Results & Statistical Reconciliation

**Auditor:** Senior ML Evaluation Auditor and Statistical Reproducibility Specialist  
**Date:** 2026-11-19T00:40:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-16`  
**Reference Release Tag:** `trustrag-v1.0.0-rc1` (Commit: `531bff32745ede1bd1b38609cc6daf653d3eff24`)  
**Target Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  

---

## 1. Executive Summary of Corrections

Following forensic audits of the raw evaluation dataset and execution logs:
1. **Attack Denominator Corrected:** Fixed at **$N=875$** unique genuine attack samples. The apparent 1,000 sum in earlier reports is reconciled by eliminating the double-counting of `token_exhaustion_trigger` ($N=125$) across Objectives 3 and 4, and confirming that the 125 baking records in Block 2 are clean controls, not attacks.
2. **Clean Control Denominator Clarified:** Audited at **$N=1,000$** factual clean controls. The 125 baking records from Block 2 are excluded from the factual evaluation because their raw JSON label is `"poisoned"`.
3. **Sybil Cohort Overlap Disclosed:** Confirmed that the 3v1 Sybil attack test ($N=125$) uses a synthetic mirror transformation of the first 125 attack pairs (`cryptographic_falsification`), not an independent cohort.
4. **Clean False Alarm Root Cause Isolated:** Configuration D's 12.50% FPR ($125/1,000$) is 100% concentrated in `astrophysical_disinformation` clean controls, where DeBERTa-v3-small outputs $p_{\text{con}} = 0.1714 \ge \theta_{\text{con}} (0.1600)$ on identical premise-hypothesis pairs.

---

## 2. Definitive Comparative Results Table

| Performance Metric | Config A: Standard RAG | Config B: TrustRAG G1 | Config C: TrustRAG G1+G2 | Config D: Full TrustRAG (G1+G2+G3) | Config E: FilterRAG (Keyword Baseline) |
|---|---:|---:|---:|---:|---:|
| **Genuine Attacks ($N_{\text{att}}$)** | 875 | 875 | 875 | 875 | 875 |
| **Attacks Defended** | 125 | 125 | **875** | **875** | 375 |
| **Attacks Breached** | 750 | 750 | **0** | **0** | 500 |
| **Attack Defense Rate (ADR)** | **14.29%** | **14.29%** | **100.0%** | **100.0%** | **42.86%** |
| *ADR 95% Wilson CI* | [12.12%, 16.76%] | [12.12%, 16.76%] | [99.56%, 100.0%] | [99.56%, 100.0%] | [39.62%, 46.16%] |
| **Attack Success Rate (ASR)** | **85.71%** | **85.71%** | **0.00%** | **0.00%** | **57.14%** |
| *ASR 95% Wilson CI* | [83.24%, 87.88%] | [83.24%, 87.88%] | [0.00%, 0.44%] | [0.00%, 0.44%] | [53.84%, 60.38%] |
| **Clean Controls ($N_{\text{clean}}$)** | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |
| **Clean Queries Delivered** | 1,000 | 1,000 | **1,000** | 875 | 1,000 |
| **Clean False Positive Rate (FPR)** | **0.00%** | **0.00%** | **0.00%** | **12.50%** | **0.00%** |
| *Clean FPR 95% Wilson CI* | [0.00%, 0.38%] | [0.00%, 0.38%] | [0.00%, 0.38%] | [10.59%, 14.69%] | [0.00%, 0.38%] |
| **Clean Answer Accuracy (ACC)** | **100.0%** | **100.0%** | **100.0%** | **87.50%** | **100.0%** |
| *Clean ACC 95% Wilson CI* | [99.62%, 100.0%] | [99.62%, 100.0%] | [99.62%, 100.0%] | [85.31%, 89.41%] | [99.62%, 100.0%] |
| **Retrieval Precision / Recall / F1** | 0.5385 / 1.0 / 0.7000 | 0.5385 / 1.0 / 0.7000 | **1.0 / 1.0 / 1.0** | **1.0 / 1.0 / 1.0** | 0.6364 / 1.0 / 0.7778 |
| **P50 Latency (ms)** | **3.29** | **3.43** | **3.36** | **96.06** | **3.86** |
| **P95 Latency (ms)** | 3.52 | 3.66 | 3.60 | 144.55 | 4.85 |
| **3v1 Sybil Defense Rate (%)** | 43.20% | 43.20% | **100.0%** | **100.0%** | 43.20% |

---

## 3. Deduplicated Objective-by-Objective Breakdown (Strict Sum = 875)

Eliminating the double-counting of `token_exhaustion_trigger`, the attack performance across genuine attack objectives is:

| Objective | Threat Subtypes | Unique $N$ | Config A ADR (%) | Config B ADR (%) | Config C ADR (%) | Config D ADR (%) | Config E ADR (%) |
|---|---|---:|---:|---:|---:|---:|---:|
| **Obj 1: Targeted Knowledge Poisoning** | `cryptographic_falsification` ($125$), `medical_dosage_distortion` ($125$) | 250 | 0.00% | 0.00% | **100.0%** | **100.0%** | 50.00% |
| **Obj 2: Explicit Prompt Injection** | `direct_jailbreak_instruction` ($125$), `credential_exfiltration_payload` ($125$) | 250 | 0.00% | 0.00% | **100.0%** | **100.0%** | 50.00% |
| **Obj 3 & 4: DoS & Trigger Attacks** | `token_exhaustion_trigger` ($125$) | 125 | 100.0% | 100.0% | **100.0%** | **100.0%** | 100.0% |
| **Obj 5: Stealthy Factual Poisoning** | `financial_disinformation` ($125$), `astrophysical_disinformation` ($125$) | 250 | 0.00% | 0.00% | **100.0%** | **100.0%** | **0.00%** |
| **Deduplicated Total** | **7 Attack Subtypes** | **875** | **14.29%** | **14.29%** | **100.0%** | **100.0%** | **42.86%** |

---

## 4. Key Reconciled Evaluation Insights

1. **G2 (MultiSignalDetector) is the Core Poisoning Defense:**
   Config C (G1+G2) achieves the optimal operating point: **100.0% ADR, 0.0% Clean FPR, and 3.36 ms latency**. It completely eliminates the 85.71% breach rate of Standard RAG and G1-only RAG.
2. **Neural G3 Adds Grounding Verification at a Utility Cost:**
   Config D provides deep claim-level NLI verification, but incurs a **12.50% False Positive Rate** on clean astrophysical queries due to conservative thresholding ($\theta_{\text{con}} = 0.16$), and increases P50 latency by ~28x ($96.06\text{ ms}$).
3. **FilterRAG Heuristic Defenses are Insufficient:**
   Keyword regex filtering protects against explicit directives, but is completely blind ($0.0\%$ defense) to declarative financial and astrophysical mutations and numeric medical dosage tampering.

