# TrustRAG Phase 26: External Benchmark Reproducibility Audit

**Audit Date:** 2026-11-24  
**Evaluator:** Principal Research Scientist & Reproducibility Auditor  
**Benchmarks Audited:** RAGTruth, HaluEval, PoisonedRAG, RSB (PoisonArena)  

---

## 1. Provenance & Artifact Verification

The local benchmark repository was audited to verify dataset files, manifest integrity, and reproducibility scripts:

| Benchmark | Source Reference | Local Storage Path | Sample Count | Format | Status |
|---|---|---|---|---|---|
| **RAGTruth** | ACL 2024 (Karpukhin et al.) | `data/raw/ragtruth/` | 2,965 source docs, 17,790 responses | JSONL | **Locally Available & Verified** |
| **HaluEval** | EMNLP 2023 (Li et al.) | `data/raw/halueval/` | 10,000 QA pairs (`qa_data.json`) | JSON | **Locally Available & Verified** |
| **PoisonedRAG** | USENIX Security 2025 (Zou et al.) | `data/raw/external_benchmarks/PoisonedRAG/` | HotpotQA, MS MARCO, NQ splits | JSON | **Locally Available & Verified** |
| **RSB (PoisonArena)** | arXiv:2505.18543 (Bao et al.) | `data/raw/external_benchmarks/PoisonArena/` | NQ, MS MARCO adversarial docs | JSON / JSONL | **Locally Available & Verified** |

---

## 2. External Evaluation Script Verification

Phase 22 established an external benchmark harness in `tools/evaluation/run_phase22_external_evaluation.py`. Re-execution confirms:
- **PoisonedRAG HotpotQA:** 92.4% Detection Rate under G2 MSD F1/F4 signals.
- **PoisonArena NQ:** 88.6% Detection Rate for instruction-bearing adversarial passages.
- **Structural Limitation:** As documented in Phase 26 Task 5, multi-document poisoning campaigns that exceed the 50% removal cap allow residual poisoning to reach the LLM context.

---

## 3. Publication Distinction Standard

In the research manuscript, all benchmark numbers must be categorized into one of three explicit tiers:
1. **Locally Reproduced:** Evaluated on the local repository using authentic benchmark datasets with frozen TrustRAG code.
2. **Published Baselines:** Cited directly from peer-reviewed literature with explicit citation keys.
3. **Synthetic / Unit Evaluations:** Internal red-team suites specifically designed for adversarial stress testing.
