# Phase 27 — Ablation Review

---

## 1. Experimental Setup

The controlled ablation study evaluated $N=100$ balanced prompts (50 adversarial query injections, 50 benign controls) across different guardrail configurations:
- **Full Defense**: G1 (Input) + G2 (MSD Retrieval) + G3 (Output)
- **No G1**: G2 + G3 active (G1 disabled)
- **G1 Only**: G1 active (G2 + G3 disabled)
- **No Guardrails**: Raw baseline RAG

---

## 2. Empirical Findings

| Configuration | Query ADR (%) | Clean Delivery (%) | Mean Query Latency (ms) | Poison Pruning Active |
| :--- | :--- | :--- | :--- | :--- |
| **Full Defense (G1 + G2 + G3)** | **72.0%** | **100.0%** | $1.42$ | Yes (MSD clustering) |
| **No G1 (G2 + G3 Only)** | **0.0%** | **100.0%** | $1.31$ | Yes (MSD clustering) |
| **G1 Only (No G2 / G3)** | **72.0%** | **100.0%** | $0.11$ | No (retrieval uninspected) |
| **No Guardrails** | **0.0%** | **100.0%** | $0.00$ | No |

---

## 3. Critical Analytical Insights

1. **G1 is the Sole Defense Against Direct Prompt Injection**:
   When G1 is disabled, query attack detection drops to **0.0%**. Neither G2 (which inspects retrieved documents, not queries) nor G3 (which inspects generated text against source documents) intercepts prompt injections directed at the query interface.
2. **G2 is Strictly Document-Centric**:
   G2 MSD clustering operates exclusively on the embedding space of retrieved passages. It has zero capability to detect or block adversarial user prompts.
3. **Defense-in-Depth Reality**:
   The guardrails form an orthogonal multi-layer defense rather than a redundant one:
   - G1 owns query sanitation.
   - G2 owns corpus poisoning defense.
   - G3 owns hallucination and ungrounded output suppression.
