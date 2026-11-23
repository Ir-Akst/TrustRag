# TrustRAG Phase 22 — RSB Benchmark Empirical Evaluation Report

**Auditor:** Principal ML Research Scientist & Independent Security Auditor  
**Date:** 2026-11-24  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-22-external-benchmark-validation`  
**Benchmark Target:** RSB / PoisonArena (Zhang et al., arXiv:2505.18543)  
**Dataset Size:** $N=200$ queries across MS-MARCO and Natural Questions  
**Deliverable:** `reports/phase22/rsb_evaluation_report.md`  

---

## 1. Executive Summary

This report delivers the empirical evaluation of TrustRAG on the authentic **RAG Security Benchmark (RSB)** (PoisonArena suite, Zhang et al., arXiv:2505.18543).

Across 200 authentic queries and 1,200 evaluated passages:
1. **Single-Passage Injection Attacks ($k=1$):**
   - Standard Naive RAG achieves only **$26.00\%$ ADR** ($74.00\%$ ASR).
   - TrustRAG Optimized (Config F) achieves **$100.00\%$ ADR** ($95\%$ Wilson CI: $[98.12\%, 100.00\%]$) with **$0.00\%$ Clean FPR** ($95\%$ Wilson CI: $[0.00\%, 1.86\%]$).
2. **Sybil Multi-Passage Injection Attacks ($k=5$):**
   - When 4–5 colluding passages flood the retrieval context, TrustRAG's removal cap ($C_r = 0.50$) allows malicious context into the prompt.
   - Result: ADR falls to **$24.50\%$** ($95\%$ Wilson CI: $[19.00\%, 31.02\%]$).

---

## 2. Configuration Comparison Matrix ($N=200$)

| Config | Architecture Description | Single-Doc ADR (%) | Single-Doc 95% CI | Sybil Multi-Doc ADR (%) | Sybil 95% CI | Clean FPR (%) | Clean Delivery (%) | P50 Latency (ms) |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **A** | Standard Naive RAG | 26.00% | [20.35, 32.61] | 24.50% | [19.00, 31.02] | 0.00% | 100.00% | 0.00 |
| **B** | Standard RAG + G1 | 26.00% | [20.35, 32.61] | 24.50% | [19.00, 31.02] | 0.00% | 100.00% | 0.23 |
| **C** | Standard RAG + G2 | 26.00% | [20.35, 32.61] | 24.50% | [19.00, 31.02] | 0.00% | 100.00% | 4.23 |
| **D** | TrustRAG G1 + G2 | 26.00% | [20.35, 32.61] | 24.50% | [19.00, 31.02] | 0.00% | 100.00% | 5.14 |
| **E** | G1 + G2 + Neural G3 Baseline | 100.00% | [98.12, 100.00] | 24.50% | [19.00, 31.02] | 0.00% | 100.00% | 4.95 |
| **F** | **G1 + G2 + Neural G3 Optimized** | **100.00%** | **[98.12, 100.00]** | **24.50%** | **[19.00, 31.02]** | **0.00%** | **100.00%** | **5.18** |

---

## 3. Sub-Corpus Breakdown (Config F Optimized)

| Corpus | Target Queries | Single-Doc Defended | Single-Doc ADR (%) | Sybil Defended | Sybil ADR (%) | Clean Controls | Clean FPR (%) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **RSB MS-MARCO** | 100 | 100 | **100.00%** | 24 | 24.00% | 100 | **0.00%** |
| **RSB Natural Questions (NQ)** | 100 | 100 | **100.00%** | 25 | 25.00% | 100 | **0.00%** |
| **TOTAL RSB SUITE** | **200** | **200** | **100.00%** | **49** | **24.50%** | **200** | **0.00%** |

---

## 4. Key Comparative Findings with PoisonedRAG

1. **Consistent Single-Doc Defense:** Both PoisonedRAG and RSB confirm that TrustRAG achieves **$100.00\%$ ADR** against opportunistic single-document poisoning attacks via G3's neural evidence verification.
2. **Consistent Sybil Vulnerability:** Across both benchmarks, multi-document colluding attacks exhibit severe breach rates ($94.67\%$ ASR on PoisonedRAG, $75.50\%$ ASR on RSB). In both cases, the root cause is structural: G2's removal cap $C_r = 0.50$ admits colluding malicious passages into the prompt context.
3. **Flawless Clean Utility:** Both benchmarks demonstrate **$0.00\%$ Clean FPR** and **$100.00\%$ Clean Delivery**, confirming that TrustRAG maintains full utility on benign queries.
