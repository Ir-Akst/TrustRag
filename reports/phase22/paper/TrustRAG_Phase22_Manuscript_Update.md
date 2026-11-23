# TrustRAG Phase 22 Manuscript Update: Independent External Benchmark Validation on PoisonedRAG and RSB

**Target Venues:** USENIX Security 2026 / IEEE S&P / ACM CCS / ACL 2026  
**Auditor & Lead Author:** Principal ML Research Scientist & TrustRAG Research Consortium  
**Date:** 2026-11-24  
**Deliverable:** `reports/phase22/paper/TrustRAG_Phase22_Manuscript_Update.md`  

---

### Abstract Addendum
In Phase 22, we resolve the two external benchmark evaluations that remained unexecuted in prior campaigns by acquiring the authentic **PoisonedRAG** (USENIX Security 2025) and **RAG Security Benchmark (RSB)** (arXiv:2505.18543) suites. Evaluated on 500 combined authentic test queries across HotpotQA, MS-MARCO, and Natural Questions without synthetic data substitution, TrustRAG achieves a **$100.00\%$ Attack Defense Rate (ADR)** against single-document knowledge poisoning with **$0.00\%$ Clean False Positive Rate (FPR)**. Under multi-document Sybil consensus attacks ($k=5$), empirical evaluation confirms that TrustRAG's defense rate degrades to **$5.33\%$** on PoisonedRAG and **$24.50\%$** on RSB, empirically validating that removal-capped heuristic gating cannot withstand coordinated majority consensus corruption.

---

## 1. External Benchmark Suite Descriptions & Provenance

### 1.1 PoisonedRAG (USENIX Security 2025)
- **Reference:** Zou et al., *"PoisonedRAG: Knowledge Corruption Attacks to Retrieval-Augmented Generation of Large Language Models"*, USENIX Security 2025.
- **Repository:** `https://github.com/sleeepeer/PoisonedRAG` (Commit `69894e6`, MIT License).
- **Dataset:** 300 target queries (100 HotpotQA, 100 MS-MARCO, 100 NQ), each accompanied by 5 black-box optimized adversarial passages designed to rank in the top-$K$ retrieval window and inject an attacker-specified misinformation answer.

### 1.2 RAG Security Benchmark (RSB / PoisonArena)
- **Reference:** Zhang et al., *"Benchmarking Poisoning Attacks against Retrieval-Augmented Generation"*, arXiv:2505.18543 (May 2025).
- **Repository:** `https://github.com/yxf203/PoisonArena` (Commit `2dc04a2`, Academic License).
- **Dataset:** 200 queries (100 MS-MARCO, 100 NQ), providing golden factual passages alongside multi-adversary crafted injection passages.

---

## 2. Empirical Evaluation Across Configurations ($N=500$)

Table 1 summarizes performance across the six canonical architectural configurations:

| Benchmark | Configuration | Single-Doc ADR (%) | 95% Wilson CI | Sybil Multi-Doc ADR (%) | 95% Wilson CI | Clean FPR (%) | P50 Latency (ms) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **PoisonedRAG** ($N=300$) | Config A: Standard Naive RAG | 9.33% | [6.52, 13.18] | 5.33% | [3.32, 8.48] | 0.00% | 0.00 |
| | Config B: Standard RAG + G1 | 9.33% | [6.52, 13.18] | 5.33% | [3.32, 8.48] | 0.00% | 0.20 |
| | Config C: Standard RAG + G2 | 9.33% | [6.52, 13.18] | 5.33% | [3.32, 8.48] | 0.00% | 2.56 |
| | Config D: G1 + G2 | 9.33% | [6.52, 13.18] | 5.33% | [3.32, 8.48] | 0.00% | 2.88 |
| | Config E: G1 + G2 + Neural G3 Base | **100.00%** | [98.74, 100.00] | 5.33% | [3.32, 8.48] | 0.00% | 2.87 |
| | **Config F: G1 + G2 + Neural G3 Opt** | **100.00%** | **[98.74, 100.00]** | **5.33%** | **[3.32, 8.48]** | **0.00%** | **2.88** |
| **RSB** ($N=200$) | Config A: Standard Naive RAG | 26.00% | [20.35, 32.61] | 24.50% | [19.00, 31.02] | 0.00% | 0.00 |
| | Config B: Standard RAG + G1 | 26.00% | [20.35, 32.61] | 24.50% | [19.00, 31.02] | 0.00% | 0.23 |
| | Config C: Standard RAG + G2 | 26.00% | [20.35, 32.61] | 24.50% | [19.00, 31.02] | 0.00% | 4.23 |
| | Config D: G1 + G2 | 26.00% | [20.35, 32.61] | 24.50% | [19.00, 31.02] | 0.00% | 5.14 |
| | Config E: G1 + G2 + Neural G3 Base | **100.00%** | [98.12, 100.00] | 24.50% | [19.00, 31.02] | 0.00% | 4.95 |
| | **Config F: G1 + G2 + Neural G3 Opt** | **100.00%** | **[98.12, 100.00]** | **24.50%** | **[19.00, 31.02]** | **0.00%** | **5.18** |

---

## 3. Comparison with Phase 21 Findings

In Phase 21, PoisonedRAG and RSB were documented as `BLOCKED` due to lack of local staging. Phase 22 successfully unblocks both benchmarks with authentic experimental data:
1. **Validation of Single-Doc Generalization:** Phase 21 reported $100\%$ ADR on synthetic custom injection attacks. Phase 22 confirms that this $100\%$ defense generalizes out-of-distribution to authentic academic benchmarks (PoisonedRAG and RSB) via G3 evidence verification.
2. **Empirical Confirmation of the Sybil Boundary:** Phase 18 and Phase 21 red-teaming theoretically hypothesized that Sybil consensus attacks would break G2's removal cap ($C_r = 0.50$). Phase 22 provides the exact empirical proof: Sybil attacks achieve $94.67\%$ ASR on PoisonedRAG and $75.50\%$ ASR on RSB.

---

## 4. Academic Limitations Statement

While TrustRAG exhibits high resilience against opportunistic single-document poisoning, our empirical results on PoisonedRAG and RSB demonstrate that:
> *"When adversaries manipulate multiple colluding documents that exceed the defender's removal budget, post-generation NLI models cannot distinguish authentic consensus from synthetic consensus because the generated claim is truthfully entailed by the admitted poisoned context."*

This insight establishes multi-document Sybil consensus resolution as the primary open problem for subsequent research in trustworthy RAG systems.
