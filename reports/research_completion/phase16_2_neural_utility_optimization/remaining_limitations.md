# TrustRAG Phase 16.2: Remaining Limitations & Operational Disclosures

**Role:** Senior ML Optimization Engineer, NLI Calibration Specialist & Independent Research Auditor  
**Date:** 2026-11-19T00:54:30+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Working Branch:** `phase-16`  
**Parent Release:** `531bff32745ede1bd1b38609cc6daf653d3eff24` (Tag: `trustrag-v1.0.0-rc1`)  
**Frozen Model Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  

---

## 1. Operational Safeguards & High-Stakes Disclaimer

> [!WARNING]
> While Phase 16.2 successfully eliminates the clean false-alarm anomaly and reduces CPU latency by 38.4%, this evaluation does NOT authorize autonomous production deployment in safety-critical domains (e.g., medical prescribing or automated financial execution) without human oversight.

---

## 2. Technical Limitations & Reality Disclosures

### 2.1 External Public Benchmark Validation Remains BLOCKED
- **Status:** Public benchmarks (RAG Security Benchmark RSB arXiv:2505.18543, PoisonedRAG USENIX Security 2024) have no open unauthenticated direct download links and external downloading is prohibited under sandboxed execution constraints.
- **Limitation:** All empirical results in Phase 16.2 derive from the audited 2,000-record synthetic and curated security benchmark (`raw_train.jsonl`) and the 2,662 validation predictions (`predictions_val.jsonl`). Real-world web-scale knowledge bases exhibit noisier syntactic constructions and uncurated domain dialects that must be tested once external benchmarks are imported.

### 2.2 Latency Disparity Between G2 and G3
- **Status:** Single-query latency for G1+G2 is **3.36 ms**, whereas G1+G2+G3 is **59.17 ms** on 2 CPU threads.
- **Limitation:** For high-throughput indexing pipelines or strict sub-10ms latency SLAs, running deep transformer forward passes per query is a throughput constraint. G1+G2 should remain the primary real-time defense, with Neural G3 serving as the claim grounding verifier.

### 2.3 Reliance on Deterministic Normalization
- **Status:** The elimination of the 125 false alarms relied on `strip_citations(doc.text)` to symmetrically remove bracketed prefix metadata (`[Conflicting Scientific Evidence - Item 1]`).
- **Limitation:** If clean corpora contain legitimate brackets that represent semantic content (e.g. mathematical notation `[a, b]` or chemical formulas `[Fe(CN)6]4-`), aggressive bracket stripping could remove domain-relevant text.

### 2.4 Frozen Checkpoint Scope
- **Status:** Checkpoint weights remain strictly read-only and immutable.
- **Limitation:** No fine-tuning or domain adaptation was performed. The underlying DeBERTa-v3-small model retains whatever inherent domain biases exist from its Phase 11.1 full 3-epoch training.

