# TrustRAG Phase 16: Remaining Limitations & Risk Disclosure

**Auditor:** Senior RAG Security Research Engineer, Red-Team Evaluator & Independent ML Auditor  
**Date:** 2026-11-19T00:31:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Output Directory:** `reports/research_completion/phase16_independent_poisoning_validation/`  

---

## 1. Overview & Operational Caveats

While Phase 16 establishes that TrustRAG v1.0.0-rc1 achieves superior knowledge-base poisoning defense compared to Standard RAG (100.0% vs 14.29% ADR) and heuristic baselines (100.0% vs 42.86% ADR), significant technical and operational limitations remain.

> [!WARNING]
> Under no circumstances does this evaluation authorize unsupervised or autonomous production deployment in high-stakes mission-critical domains (such as autonomous medical diagnosis or automated financial execution) without human oversight.

---

## 2. Exhaustive List of Remaining Limitations

### 2.1 External Public Benchmark Reality Gap
- **Finding:** Neither the RAG Security Benchmark (RSB, arXiv:2505.18543) nor the PoisonedRAG evaluation suite could be acquired or executed due to lack of public direct download URLs and strict sandboxed execution boundaries.
- **Consequence:** While TrustRAG achieved 100.0% ADR on the audited 2,000-record synthetic and curated security benchmark, real-world web-scale knowledge bases exhibit noisier linguistic patterns, contradictory non-adversarial perspectives, and emergent poisoning vectors not fully captured in controlled synthetic pairs. External public benchmark validation remains formally **BLOCKED**.

### 2.2 Clean Utility Penalty of Neural G3 (12.50% Clean FPR)
- **Finding:** In Configuration D (Full TrustRAG with Neural G3), clean query delivery dropped from 100.0% to 87.50%, representing an empirical False Positive Rate of **12.50%** [95% CI: 10.59%, 14.70%].
- **Consequence:** For one out of every eight benign queries, the system refuses or abstains because sentence-level DeBERTa NLI cannot prove logical entailment for valid approximations or paraphrased assertions under `nli_neutral_policy = "insufficient"`. In enterprise environments requiring high answer availability, Configuration C (G1+G2 alone) provides 100% clean delivery with zero FPR, albeit without claim-level verification of LLM generation.

### 2.3 CPU Latency Disparity
- **Finding:**
  - Standard RAG: **3.29 ms** P50
  - TrustRAG G1+G2: **3.36 ms** P50 (+0.07 ms overhead)
  - Full TrustRAG (G1+G2+G3): **96.06 ms** P50 (~28x overhead)
- **Consequence:** Although 96 ms remains acceptable for interactive user queries, it creates a throughput bottleneck for batch indexing or sub-10ms API SLAs on CPU-only infrastructure.

### 2.4 Reliance on Pre-Generation Evidence Gating
- **Finding:** By mathematical definition, the retrieval removal cap is bounded by $\lfloor K/2 \rfloor$. If an attacker injects multiple poisoned passages that occupy more than 50% of top-$K$ retrieval slots (e.g., 3 out of 5), the retriever *must* admit at least one poisoned candidate into the candidate pool.
- **Mitigation Status:** The newly integrated `Pre-Generation Evidence Gate` (line 190 of `trustrag_pipeline.py`) successfully quarantines any surviving POISONED or UNCERTAIN documents before generation. However, if the gate were bypassed or disabled, the removal cap alone would be insufficient against majority-poisoned candidate pools.

### 2.5 Multi-Paragraph Narrative Poisoning
- **Finding:** DeBERTa-v3-small operates on sentence/passage pairs up to 512 tokens. An adversary who distributes deceptive claims across lengthy multi-page documents where individual sentences appear completely benign can bypass sentence-level NLI contradiction detection.

### 2.6 Consensus Dependency on Peer Presence
- **Finding:** G2 signal $F_5$ (consensus deviation) requires at least two candidate documents retrieved for the same query to perform cross-document consensus. If a user query retrieves only a single document from an isolated corpus, cross-document consensus cannot fire, leaving the detector dependent on $F_4$ instruction risk and $F_6$ provenance.

