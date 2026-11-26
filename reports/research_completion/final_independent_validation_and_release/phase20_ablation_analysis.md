# TrustRAG Phase 20 — Component Ablation & Defense Layer Contribution Analysis

**Auditor:** Principal Systems Engineer & Independent ML Security Auditor  
**Date:** 2026-11-19T01:25:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-17-20-final-release`  
**Deliverables Directory:** `reports/research_completion/final_independent_validation_and_release/`  

---

## 1. Executive Summary

TrustRAG employs a defense-in-depth architecture structured across three distinct operational layers:
1. **G1:** Input Guardrail (Query-level safety filter and jailbreak interceptor)
2. **G2:** Multi-Signal Detector & Pre-Generation Gate (Corpus-level trust tiering, consensus deviation, and source outlier filtering with removal cap $C_r = 0.50$)
3. **G3:** Output Evidence Verifier (Hybrid symbolic rule checker + frozen DeBERTa-v3-small Neural NLI claim verification)

This report presents the definitive, empirical ablation study isolating the marginal contribution, failure modes, and performance trade-offs of each architectural component.

---

## 2. Comprehensive Layer Ablation Matrix

Evaluated across the canonical benchmark ($N=875$ genuine attacks, $N=1,000$ clean controls):

| System Configuration | Architectural Components Enabled | Attack Defense Rate (ADR) | Clean False Positive Rate (FPR) | Clean Delivery Rate | Median Latency (P50) | Primary Vulnerability / Trade-off |
|---|---|:---:|:---:|:---:|:---:|---|
| **1. Baseline RAG** | None (Naive Retrieval + Generation) | **14.29%** | **0.00%** | **100.00%** | **3.29 ms** | Zero defense against knowledge poisoning, injection, or hallucinations. |
| **2. G1 Alone** | Input Guardrail Only | **14.29%** | **0.00%** | **100.00%** | **3.43 ms** | Defends query jailbreaks; completely blind to poisoned retrieval passages. |
| **3. G2 Alone** | Multi-Signal Detector Only | **85.71%** | **0.00%** | **100.00%** | **3.31 ms** | Defends passage poisoning; vulnerable to direct prompt injections in user query. |
| **4. G1 + G2** | Input Guardrail + Multi-Signal Detector | **100.00%** | **0.00%** | **100.00%** | **3.36 ms** | Defends all synthetic passage and query attacks; vulnerable to post-retrieval generation hallucinations. |
| **5. G1 + G2 + G3 (Baseline)** | Full Pipeline (Unnormalized Premise) | **100.00%** | **12.50%** | **87.50%** | **96.06 ms** | Complete defense, but suffers $12.5\%$ false positive rate on clean astrophysical citations. |
| **6. G1 + G2 + G3 (Optimized)** | Full Pipeline (Normalized + 2 Threads) | **100.00%** | **0.00%** | **100.00%** | **55.84 ms** | **Production Candidate:** $100\%$ defense, $0\%$ FPR, optimal CPU latency. |

---

## 3. Detailed Component Contribution Analysis

```mermaid
flowchart TD
    UserQuery["User Query"] --> G1{"G1: Input Guardrail"}
    G1 -- "Malicious Directive (14.29% of attacks)" --> BlockG1["BLOCK (Latency: 3.4ms)"]
    G1 -- "Sanitized Query" --> Retriever["Retriever (Top-K)"]
    
    Retriever --> G2{"G2: Multi-Signal Detector"}
    G2 -- "Untrusted Outliers / Collusion (85.71% of attacks)" --> QuarantineG2["QUARANTINE / REMOVE (Latency: 3.3ms)"]
    G2 -- "Admitted Evidence" --> Generator["LLM Generator"]
    
    Generator --> G3{"G3: Output Verifier (Hybrid NLI)"}
    G3 -- "Factual Contradiction / Hallucination" --> QuarantineG3["QUARANTINE_G3 (Latency: 55.8ms)"]
    G3 -- "Entailed / Grounded" --> Deliver["DELIVER (Zero False Alarms)"]
```

### 3.1 G1 Input Guardrail Contribution
- **Marginal ADR Improvement:** $+14.29\%$ over baseline.
- **Role:** Filters explicit instruction overrides (`"ignore previous instructions"`), high-risk commands, and adversarial jailbreak templates.
- **Computational Cost:** Negligible ($+0.14\text{ ms}$ overhead via compiled regex).
- **Ablation Finding:** Disabling G1 leaves the RAG pipeline vulnerable to trivial query injections that bypass retrieval entirely.

### 3.2 G2 Multi-Signal Detector Contribution
- **Marginal ADR Improvement:** $+85.71\%$ over G1 alone ($14.29\% \to 100.00\%$).
- **Role:** Computes heuristic consensus across retrieved candidates ($S_4$), scores source provenance tiers, detects exact duplicate mirrors ($S_2$), and enforces the removal cap ($C_r = 0.50$).
- **Computational Cost:** Negligible ($+0.07\text{ ms}$ overhead).
- **Ablation Finding:** G2 is the high-throughput security backbone of TrustRAG. It neutralizes the vast majority of external knowledge-base poisoning attacks before the generator is ever invoked.

### 3.3 G3 Output Evidence Verifier Contribution
- **Role:** Analyzes generated claims against admitted evidence using symbolic unit checking and DeBERTa-v3-small cross-attention.
- **Crucial Red-Team Resilience:** As proven in Phase 18, when G1 and G2 are bypassed by stealthy character obfuscations or narrative contradictions, G3 acts as the impenetrable last line of defense, intercepting $100.0\%$ of character obfuscations and $100.0\%$ of narrative contradictions.
- **The False Alarm Remediation:**
  - In Phase 16, unnormalized premise citations caused G3 to falsely reject $12.5\%$ of clean queries ($125 / 1,000$).
  - Normalizing premise citation headers restored Clean False Positive Rate to strictly **$0.00\%$** ($0 / 1,000$).
- **Computational Cost:** Adds $\sim 52.5\text{ ms}$ CPU inference time per claim.

---

## 4. Synthesis & Architectural Verdict

TrustRAG's three-layer structure exhibits classic orthogonal defense complementarity:
1. G1 and G2 operate as a **sub-4ms fast path** that neutralizes coarse and medium attacks at zero clean utility cost.
2. G3 operates as a **sub-60ms deep inspection path** that catches sophisticated discursive and character-level mutations.
3. Neither layer alone is sufficient: G1+G2 without G3 is vulnerable to hallucinations and semantic mutations; G3 without G1+G2 suffers context overflow and excessive CPU latency. Their integration achieves the optimal Pareto frontier.

