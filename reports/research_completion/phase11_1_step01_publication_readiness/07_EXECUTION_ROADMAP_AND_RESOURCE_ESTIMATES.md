# TrustRAG — Phase 11.1, Step 1: Publication Readiness Plan
## 07 — Execution Roadmap, Dependency Graph & Resource Estimates

- **Audit Date:** 2026-11-14T18:15:00Z
- **Auditor:** Principal Research Scientist, ML Training Architect & Reproducibility Engineer

---

### 1. Phase 11.1 Execution Roadmap & Dependency Graph

To transition TrustRAG from an engineering prototype to a publication-grade submission, work must proceed through four strictly sequenced stages. Each stage is gated by explicit empirical acceptance criteria.

```
+---------------------------------------------------------------------------------------------------+
| Phase 11.1 Dependency Graph                                                                       |
+---------------------------------------------------------------------------------------------------+
|  [Stage 1: Model Convergence]                                                                     |
|  Full-Dataset NLI Training (10,815 samples, 3 epochs, Focal Loss)                                 |
|  Gate: Contradiction Recall >= 65.0%, Macro F1 >= 0.650                                           |
|       |                                                                                           |
|       v                                                                                           |
|  [Stage 2: Offline Multi-Task Benchmark & Ablation]                                               |
|  - Full Binary Validation Benchmark (5,984 samples)                                               |
|  - Multi-Chunk vs Single-Window Long-Premise Ablation                                             |
|  - Raw Probability Serialization (predictions.jsonl, ECE, Brier, RC Curves)                       |
|  Gate: Full Binary Acc >= 75.0%, Multi-Chunk Latency <= 250ms/sample                              |
|       |                                                                                           |
|       v                                                                                           |
|  [Stage 3: End-to-End Pipeline Evaluation]                                                        |
|  - Benchmark TrustRagPipeline with Neural Verifiers on Phase 10 Suites                            |
|  - Comparative Evaluation vs Naive RAG, FilterRAG, and Heuristic Baselines                        |
|  Gate: Hallucination Rate reduction >= 40% (p < 0.01), Clean Abstention < 25%                      |
|       |                                                                                           |
|       v                                                                                           |
|  [Stage 4: Manuscript Preparation & Evidence Packaging]                                          |
|  - Artifact freeze, open-source model checkpoints, reproducibility scripts                        |
|  - Final Peer-Review Audit and Manuscript Finalization                                            |
+---------------------------------------------------------------------------------------------------+
```

---

### 2. Stage-by-Stage Implementation Plan

#### Stage 1: Full-Dataset NLI Convergence
- **Task:** Train `deberta-v3-small` on `data/processed/sft_v2/nli/train.jsonl` (10,815 samples) for 3 full epochs (~8,110 optimizer steps at effective batch size 4).
- **Remediations Active:** Class-balanced sampler, class-weighted cross-entropy loss ($w = [1.0, 3.5, 1.5]$), hypothesis preservation (seq len 384), learning rate $2\times 10^{-5}$ with cosine decay.
- **Hardware Requirement:** 
  - *Option A (CPU):* ~21.2 hours on existing 10-core i7-1355U ($8,110\text{ steps} \times 9.4\text{ s/step}$).
  - *Option B (Single GPU, e.g. T4 / RTX 3090 / A10G):* ~45–75 minutes ($B=16$, mixed precision FP16).
- **Mandatory Deliverable:** Checkpoint `models/trained/deberta-v3-small-nli-converged/`, evaluation results on 2,662 validation set, serialized `predictions_val.jsonl`.
- **Approval Gate 1:** Contradiction Recall $\ge 65.0\%$, Macro F1 $\ge 0.650$.

#### Stage 2: Offline Multi-Task Benchmark & Ablation
- **Task 2.1:** Evaluate binary checkpoint on the complete 5,984 validation split (`sft_v2/binary/validation.jsonl`). Record domain-wise splits (HaluEval vs RAGTruth) and serialize `predictions_binary_val.jsonl`.
- **Task 2.2:** Execute multi-chunk vs. single-window ablation on long premises ($> 400$ tokens) using `nli_multi_chunk.py`.
- **Task 2.3:** Generate calibrated reliability diagrams, Brier score curves, and Risk-Coverage curves.
- **Compute Requirement:** ~3.5 hours CPU inference (or 15 min GPU).
- **Approval Gate 2:** Binary accuracy $\ge 75.0\%$ across all domains; Risk-Coverage curve monotonically decreasing.

#### Stage 3: End-to-End Pipeline Evaluation
- **Task:** Integrate trained binary and NLI models into `TrustRagPipeline`. Execute Phase 10 benchmark suite:
  - `clean_rag_test` (500 queries)
  - `knowledge_poisoning_test` (500 queries)
  - `hallucination_test` (500 queries)
- **Comparisons:** Naive RAG (no verifier) vs. Phase 10 heuristic verifiers vs. TrustRAG Neural.
- **Compute Requirement:** ~6.0 hours CPU pipeline execution.
- **Approval Gate 3:** Statistically significant ($p < 0.01$) reduction in hallucination rate on poisoned/hallucination suites.

#### Stage 4: Manuscript Preparation & Evidence Packaging
- **Task:** Assemble experimental tables, LaTeX figures, Risk-Coverage plots, and artifact checksums. Package model weights and open-source evaluation scripts.

---

### 3. Resource Requirements Summary

| Resource Category | Detailed Requirement | Availability Status | Missing Permissions / Assets |
| :--- | :--- | :--- | :--- |
| **Compute (CPU)** | ~31.0 hours total CPU runtime on host i7-1355U (or ~2.0 hours if GPU access granted). | **AVAILABLE LOCALLY** (Host has 10 cores, 16 GB RAM). | Requires explicit user authorization to execute long-running compute. |
| **Compute (GPU)** | 1x NVIDIA GPU (>= 16 GB VRAM) for accelerated training. | **NOT CONFIGURED** (Current environment is PyTorch CPU 2.14.1). | GPU compute not present in current shell sandbox. |
| **Storage** | ~2.5 GB additional disk space (Checkpoints: ~1.2 GB; Prediction logs: ~300 MB; Benchmark traces: ~1.0 GB). | **AVAILABLE** (Workspace has > 25 GB free disk space). | None. |
| **Datasets** | Existing SFT v2 splits (26,054 binary train, 10,815 NLI train). | **AVAILABLE LOCALLY** in `data/processed/sft_v2/`. | Full HotpotQA 5.23M and MS MARCO 8.84M missing (only needed for full retrieval). |
| **Human Annotations** | 200 multi-claim answers for 5-outcome G3 human agreement evaluation. | **OPTIONAL / DESIRABLE** | Requires human labeling if 5-outcome agreement is claimed. |

---

### 4. Explicit Authorization Protocol

In accordance with independent research governance:
- **No stage in this roadmap may be initiated autonomously.**
- Each stage requires **prior explicit user authorization**.
- If any stage fails its designated Approval Gate, the execution must **halt immediately for failure review** rather than proceeding blindly to the next stage.

