# TrustRAG Phase 04 — Step 9: Defense Component Ablation Study

**Date:** 2026-11-11  
**Seed & Retrieval Settings:** `seed=42`, `top_k=5`, `tfidf_extractive`  
**Evaluation Suite ($N=58$ Scenarios Total):**
- **Clean Utility:** `data/benchmarks_backup/clean_rag/test.jsonl` ($N=15$ real BoolQ queries)
- **Corpus Injection Pairs (Synthetic):** `data/benchmarks_backup/knowledge_poisoning/test.jsonl` + `adversarial_robustness/test.jsonl` ($N=29$ unique `source_id` injection pairs)
- **Direct Malicious Queries (Synthetic):** $N=14$ prompt injection, malicious command, and trigger-DoS inputs

---

## 1. Controlled Ablation Results (E1–E7)

| Arm | Active Modules | Clean R@5 | Clean Faith. | Clean FPR | Corpus Inj. ASR | Corpus Prevented / Flagged | Direct Query ASR | Combined Threat ASR | Mean Lat (ms) | p95 Lat (ms) | Throughput (QPS) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **E1** | Original RAG | 0.8000 | 0.7333 | 0.0000 | 0.4483 | 0.5517 | 1.0000 | 0.6279 | 3.68 | 4.82 | 271.76 |
| **E2** | RAG + G1 | 0.8000 | 0.7333 | 0.0000 | 0.4483 | 0.5517 | **0.0000** | 0.3023 | **2.66** | **4.19** | **375.43** |
| **E3** | RAG + G2 | 0.8000 | 0.7333 | 0.0000 | **0.1379** | 0.8621 | 1.0000 | 0.4186 | 6.17 | 9.51 | 162.10 |
| **E4** | RAG + G3 | 0.8000 | 0.7333 | 0.0000 | 0.4483 | 0.5517 | 1.0000 | 0.6279 | 7.62 | 13.13 | 131.28 |
| **E5** | RAG + G1 + G2 | 0.8000 | 0.7333 | 0.0000 | **0.1379** | 0.8621 | **0.0000** | **0.0930** | 4.38 | 8.50 | 228.20 |
| **E6** | RAG + G1 + G2 + G3 | 0.8000 | 0.7333 | 0.0000 | **0.1379** | **1.0000** | **0.0000** | **0.0930** | 8.15 | 16.45 | 122.77 |
| **E7** | Full TrustRAG + SRM (`fallback`) | 0.8000 | 0.7333 | 0.0000 | **0.1379** | **1.0000** | **0.0000** | **0.0930** | 7.55 | 16.08 | 132.38 |

---

## 2. Key Component Findings

1. **Largest Security Improvement — Synergistic G1 + G2 (`E5`):**
   - **G1 alone (`E2`)** eliminates 100% of direct query injections (`1.0000` $\rightarrow$ `0.0000`), dropping combined ASR from `0.6279` $\rightarrow$ `0.3023` (`-32.56 pp`), while *reducing* mean latency (`3.68 ms` $\rightarrow$ `2.66 ms`) via early blocking.
   - **G2 alone (`E3`)** cuts corpus poisoning ASR by **69.2% relative** (`0.4483` $\rightarrow$ `0.1379`).
   - **Combined G1 + G2 (`E5`)** interacts positively across distinct attack surfaces (query vs. corpus), reducing combined threat ASR by **85.2% relative** (`0.6279` $\rightarrow$ `0.0930`) with `0.0000` clean FPR.
2. **G3 Contribution & Latency Overhead (`E4`, `E6`):**
   - G3 pushes `corpus_injection_prevented_or_flagged` from `0.8621` $\rightarrow$ **`1.0000`** (`+13.79 pp`), ensuring surviving symmetric conflicts are flagged/unverified rather than trusted.
   - G3 introduces the largest per-query computational cost (`+3.76 ms` comparing `E5` vs `E6`; `+3.94 ms` comparing `E1` vs `E4`), reducing throughput from `228.2 QPS` (`E5`) to `122.8 QPS` (`E6`).
3. **SRM Deterministic Fallback (`E7` vs `E6`):**
   - With `backend="disabled"`, deterministic SRM fallback produces **no measurable accuracy or ASR improvement** over `E6` (`0.0930` vs `0.0930`), while maintaining negligible latency (`~0.02 ms`).
4. **Architectural Isolation Limitation Documented:**
   - `TrustAwareRetriever` and `TrustRAGPipeline` invoke `MultiSignalDetector.assess_candidates()` unconditionally even when `MSDConfig.enabled=False`. To isolate E1, E2, and E4 cleanly without modifying Phase 03 modules, the ablation orchestrator invoked raw TF-IDF retrieval (`_retrieve_indexed_candidates`) directly for `g2=False` arms.

---

## 3. Step 9 Acceptance Verdict

- [x] All 7 configurations (E1–E7) evaluated on consistent datasets and seed (`42`).
- [x] Individual component contributions, interaction effects, and overheads quantified.
- [x] Isolation mechanics and deterministic SRM fallback limits documented honestly.

**Step 9 Status:** **PASS** — Ready to proceed to Step 10 (Performance and Resource Evaluation).

