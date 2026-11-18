# TrustRAG — Track 2, Step 3.19: Final Closure Audit
## 04 — Remaining Research Gaps & Recommended Next Phase

- **Audit Date:** 2026-11-14T18:05:00Z
- **Auditor:** Independent Research Auditor & Final Evidence-Governance Reviewer

---

### 1. Ordered Research Gaps (By Priority)

The following outstanding gaps prevent Track 2 from being declared research-complete. They are ordered strictly by scientific and architectural importance:

#### Priority 1: Contradiction Classification Collapse & Full-Dataset NLI Convergence
- **The Gap:** The current NLI pilot was bounded to exactly 1,000 steps (~9.25% of the 10,815 available training samples). While class-balanced sampling successfully prevented total single-class collapse, the model failed to learn minority-class contradiction features, resulting in a catastrophic **4.49% Contradiction Recall** (16 of 356 true contradictions identified).
- **Required Work:** Full-dataset training over all 10,815 samples, utilizing focal loss, asymmetric cross-entropy weighting, or hard-negative mining to force the model to attend to contradiction cues.

#### Priority 2: End-to-End Pipeline Benchmarking with Trained Neural Verifiers
- **The Gap:** Neither `deberta-v3-small-binary-pilot1000` nor `deberta-v3-small-nli-remediated` has ever been benchmarked inside `TrustRagPipeline`. All existing pipeline evaluations in `reports/evaluation/` rely on historical Phase 10 mocks or heuristic verifiers.
- **Required Work:** Configure `TrustRagPipeline` to instantiate the trained neural cross-encoders, execute the Phase 10 benchmark suite (Clean RAG, Knowledge Poisoning, Hallucination Eval), and statistically compare downstream faithfulness against baseline RAG.

#### Priority 3: Full-Corpus Retrieval Staging & Evaluation
- **The Gap:** Canonical 5.23M Wikipedia (HotpotQA) and 8.84M MS MARCO passage archives remain missing from disk. Retrieval evaluations in Step 2.4 were restricted to 10-candidate snippet re-ranking.
- **Required Work:** Acquire and stage the canonical passage collections and evaluate true open-corpus retrieval (BM25 + neural re-ranking) across the complete corpus.

#### Priority 4: Persistence of Raw Prediction Probabilities for Full Reproducibility
- **The Gap:** Continuous probability triples $[p_0, p_1, p_2]$ and sample IDs were discarded during evaluation, preventing independent verification of Brier score, ECE-10, and cross-entropy loss without re-executing inference.
- **Required Work:** Update `train_nli_classifier.py` and evaluation scripts to serialize raw probability predictions (`predictions.jsonl`) alongside summary metrics.

#### Priority 5: Five-Outcome G3 Supervision & Premise Evidence Spans
- **The Gap:** The pipeline claims five G3 verification outcomes (`SUPPORTED`, `CONTRADICTED`, `NEUTRAL`, `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`), but only 3-class NLI supervision exists. Human annotations in RAGTruth lack premise-level character spans.
- **Required Work:** Curate or synthetically generate premise-level evidence span annotations and multi-claim examples covering true partial support and insufficiency.

#### Priority 6: Generative Reasoning & Auditable Proof-Traces
- **The Gap:** The project has zero trained generative models and zero supervised chain-of-thought datasets. Rationale generation exists solely as prompt schemas for third-party commercial APIs.
- **Required Work:** Construct supervised rationale datasets and fine-tune an autoregressive generator to output step-by-step verifiable proof-traces.

---

### 2. Explicitly Unauthorized Work

Under the current project boundary, the following actions remain **STRICTLY PROHIBITED**:
- **NO model training, fine-tuning, optimizer steps, or backward passes.**
- **NO modification or overwriting of existing model checkpoints.**
- **NO new full-dataset evaluation runs or benchmark campaigns.**
- **NO modifications to source code, configurations, or historical reports.**
- **NO Git operations (commit, push, merge, reset, checkout, branch change).**
- **NO initiation of Track 3.**

---

### 3. Recommended Next Phase: Phase 11.1 (Targeted Empirical Convergence)

When the project owner chooses to grant new authorization, work should proceed under a clearly scoped **Phase 11.1: Empirical Verification Convergence**:

1. **Authorization Scope:** A multi-epoch training authorization for full-dataset NLI training (10,815 samples) with class-weighted cross-entropy on GPU or dedicated compute.
2. **Success Gate:** Achieving a Contradiction Recall $\ge 65.0\%$ and Macro F1 $\ge 0.650$ on the 2,662 validation set.
3. **Integration Gate:** Successful end-to-end execution of `TrustRagPipeline` using the trained model on the Phase 10 benchmark suite with measured reduction in hallucinated responses.

Until such authorization is explicitly granted, Track 2 remains formally closed and frozen.

