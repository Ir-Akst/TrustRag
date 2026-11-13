# TrustRAG Phase 13 Step 11 — Remaining Work & Research Roadmap

**Target Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Auditor:** Independent Senior Software Architect & ML Research Evaluator  
**Audit Dimension:** Actionable Technical Roadmap for Research and Future Engineering  
**Evaluation Date:** 2026-11-13  

---

## 1. Executive Summary

While TrustRAG's deterministic software engine, REST API, UI dashboard, and input guardrails (G1) are complete and production-grade, significant technical work remains to fulfill the project's original academic research objectives and neural capabilities.

This roadmap details the remaining work across four prioritized categories:
1. **P1 — External Research Dataset Acquisition & Ingestion**
2. **P2 — Neural Model Training & Infrastructure Setup**
3. **P3 — Full-Scale Research Benchmark Execution**
4. **P4 — Advanced Post-Phase 13 Security Hardening**

---

## 2. Prioritized Technical Roadmap

### 2.1 Track 1: Dataset Acquisition & Indexing (Priority 1)
- **RAGTruth Full Ingestion:** Download canonical 18,000-record annotated hallucination corpus; replace the 5-row micro-fixture; validate split generation.
- **HaluEval & LLM-AggreFact Ingestion:** Download and parse the 35,000 HaluEval QA records and 11,000 AggreFact claims to evaluate span-level hallucination detection.
- **RAG Security Benchmark (RSB) Integration:** Download and standardize the RSB corpus to replace the synthetic 8-template `custom_security` dataset.
- **NQ, HotpotQA, and MS MARCO Corpora:** Ingest full-scale retrieval datasets and construct on-disk FAISS index partitions.

### 2.2 Track 2: Neural Models & Training Pipelines (Priority 2)
- **Deep Learning Framework Setup:** Install `torch`, `transformers`, `peft`, and `trl` in a GPU-accelerated container environment.
- **Small Reasoning Model (SRM) Training:**
  - Download `Qwen/Qwen2.5-3B-Instruct` base checkpoint.
  - Implement ORPO (Odds Ratio Preference Optimization) with LoRA rank 16 on `FineWeb -> Dclean -> HalluClaim`.
  - Persist fine-tuned weights to a local `models/` directory.
- **G2 Neural Signal Integration:**
  - Connect causal language model for F1 (Perplexity Anomaly) next-token loss calculation.
  - Connect dense transformer model for F2 (Embedding Norm Anomaly) vector extraction.
  - Connect live Small Language Model (SLM) for FilterRAG frequency density calculations ($a_j = \text{SLM}(q_i, d_j)$).
- **G3 Neural NLI Verifier:** Integrate a DeBERTa-v3 NLI cross-encoder alongside the existing rule-based verifier to achieve semantic entailment verification.

### 2.3 Track 3: Empirical Research Benchmark Replication (Priority 3)
- **ASR & Utility Evaluation:** Execute large-scale evaluations measuring Attack Success Rate (ASR) against RSB attacks alongside Clean-Query Utility on Natural Questions.
- **Paper Parity Verification:** Systematically reproduce the 28 experimental claims documented in `RESEARCH_COMPLIANCE_MATRIX.md` across Papers A, B, and C.
- **Statistical Significance Testing:** Compute 95% confidence intervals via 1,000-sample bootstrap for all published table metrics.

### 2.4 Track 4: Advanced Post-Phase 13 Security Hardening (Priority 4)
- **Recursive Base64 Unpacking:** Implement a depth-2 shallow recursive scanner for single large candidate tokens to detect nested Base64 payloads (`B64(B64(Attack))`).
- **High-Candidate Anomaly Scoring:** Add an input anomaly rule: queries containing $>32$ Base64 candidates receive an automatic $+0.2$ risk score increment to mitigate candidate starvation at position 65+.
- **Alternative Encodings Support:** Add optional decoders for RFC 4648 §6 Base32, Ascii85/Base85, and UUEncode.
- **G2 Semantic Poisoning Defense:** Harden G2 against stealth factual knowledge poisoning and coordinated 3-vs-1 repetition attacks once neural embeddings are active.

---

## 3. Estimated Resource Requirements for Full Research Completion

| Requirement Area | Specification / Hardware | Estimated Effort |
|---|---|---|
| **GPU Compute Infrastructure** | 1x NVIDIA A100 (80GB) or 2x RTX 4090 | 2 weeks cloud compute |
| **Storage Capacity** | $\approx 250\text{ GB}$ SSD (for MS MARCO, NQ, and model checkpoints) | Provisioned volume |
| **Engineering Effort** | 1 Senior ML Engineer + 1 Senior Security Researcher | 4–6 weeks |

---

## 4. Audit Conclusion

The software architecture was designed with modular extension points that make executing this roadmap straightforward. The software container, interfaces, and evaluation harnesses are completely ready to receive real data and trained weights.

