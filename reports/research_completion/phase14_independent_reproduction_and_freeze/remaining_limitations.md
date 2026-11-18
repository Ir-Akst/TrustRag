# TrustRAG Phase 14: Remaining Limitations & Risk Register

**Audit Role:** Independent Senior ML Research Auditor, RAG Security Engineer & Reproducibility Specialist  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-14` | **HEAD:** `aba5cc9d`  
**Evaluation Date:** November 18, 2026  

---

## 1. Executive Summary

While TrustRAG Phases 11–13 successfully eliminated all factual and prompt injection breaches on the evaluated $N=975$ benchmark ($100.0\%$ ADR), this document records the remaining architectural, computational, and open-world limitations that govern the project freeze.

---

## 2. Technical Limitations & Threat Vectors

### Limitation 1: Unanchored Web Retrieval Sybil Vulnerability
- **Mechanism:** TrustRAG's 3-tier consensus resolution protects verified reference documents from being outvoted by coordinated sybil documents ($3v1$).
- **Vulnerability:** When a RAG query retrieves evidence exclusively from open-web search results with **no registered authoritative documents** (all candidates Tier 3), the consensus algorithm falls back to unweighted peer clustering. If an adversary injects 3 colluding web pages against 1 legitimate web page, the consensus engine will treat the legitimate page as a minority outlier ($trust = 0.15$) and reward the sybils ($trust = 0.85$).
- **Mitigation Requirement:** Enterprise deployments must require at least one verified internal document anchor in every retrieval pool.

### Limitation 2: Open-Domain Narrative Contradiction Bounds
- **Mechanism:** G2 symbolic factual consistency ($S_5$) operates via explicit antonym/polarity matrices and numeric/unit parsing.
- **Vulnerability:** In narrative domains without numerical figures or registered antonyms (e.g. historical interpretations, legal analyses, geopolitical developments), symbolic detection drops to $\sim 10\%$. Downstream protection relies exclusively on DeBERTa-v3-small (141.9M parameters), whose validation contradiction precision is $63.8\%$.
- **Mitigation Requirement:** Periodic lexicographical expansion of domain polarity dictionaries or fine-tuning larger foundation models (e.g. 7B+ parameter verifiers).

### Limitation 3: Single-Sample CPU Neural Latency Bound
- **Mechanism:** Standalone unbatched neural NLI forward passes on CPU require $\sim 42\text{ ms}$ for short claims and $\sim 302\text{–}335\text{ ms}$ for full-length 512-token sequence pairs due to unquantized disentangled self-attention.
- **Operational Impact:** While symbolic fast-paths preserve a median pipeline latency of $5.56\text{ ms}$ for standard queries, queries that trigger full neural G3 verification experience a latency spike to $>300\text{ ms}$.
- **Mitigation Requirement:** Hardware acceleration (GPU / TPU) or asynchronous batched processing ($B \ge 16$, amortized $21.36\text{ ms}$) for high-throughput SLAs.

### Limitation 4: Single-Document Sparse Retrieval Denial-of-Removal
- **Mechanism:** `TrustAwareRetriever` enforces a bounded removal cap (`removal_cap_ratio = 0.5`, using `math.floor(len(docs) * ratio)`).
- **Vulnerability:** If only $K=1$ document is retrieved, `math.floor(1 * 0.5) = 0`, meaning no document can be removed by the retriever even if flagged as `POISONED` (unless total abstention is triggered).
- **Mitigation Requirement:** Configure minimum candidate retrieval $K \ge 2$, or enable absolute quarantine override when instruction risk exceeds $0.90$.

---

## 3. Operational Deployment Guidelines

To maintain security integrity under the documented limitations, deployers must adhere to the following rules:
1. **Never deploy in unsupervised autonomous settings** where LLM actions trigger irreversible physical, financial, or database state changes without human authorization.
2. **Always register authoritative internal documents** for critical vertical domains (medical guidelines, financial filings, cryptographic standards).
3. **Set minimum retrieval pool size $K \ge 3$** to ensure bounded removal caps function correctly.
4. **Monitor G3 latency percentiles** and configure fallbacks for neural timeout exceptions.

