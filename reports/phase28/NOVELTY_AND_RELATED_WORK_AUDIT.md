# Phase 28 — Novelty & Related-Work Audit

---

## 1. Context & Prior Literature Landscape

Retrieval-Augmented Generation (RAG) defenses fall into three broad classes:
1. **Pre-Retrieval Input Filtering**: Guardrails that inspect user input before document retrieval (e.g., Llama Guard, NeMo Guardrails, keyword/regex sanitizers).
2. **Retrieval-Stage Corpus Filtering**: Algorithms that remove poisoned, conflicting, or adversarial passages fetched from external knowledge corpora (e.g., FilterRAG, ML-FilterRAG, RobustRAG, Cert-RAG).
3. **Post-Generation Factuality Verification**: Models that decompose generated answers into atomic claims and verify NLI entailment against retrieved context (e.g., HalluGuard, Self-CheckGPT, RAGTruth verifiers).

---

## 2. Component-by-Component Novelty Dissection

### 2.1 G1 Input Guardrail
- **Established Prior Work**: Lexical filtering, regex pattern matching, and prompt sanitization are standard industry baselines (OWASP Top 10 for LLMs, 2023; Inan et al., Llama Guard, 2023).
- **TrustRAG Adaptation**: A compiled collection of regular expressions covering delimiters, system prompt extraction, and known jailbreak pretexts (`src/trustrag/guardrails/input_guardrail.py`).
- **Original Contribution**: None algorithmically. Its value is purely operational: ultra-low latency ($0.20$ ms) and zero false positives on standard technical queries.
- **Verdict**: Heuristic baseline. Must not be claimed as an algorithmic novelty.

### 2.2 G2 Multi-Signal Detector (MSD) & Robust Clustering
- **Established Prior Work**:
  - FilterRAG (Zou et al., USENIX Security 2025): Filters poisoned passages by identifying dense frequency clusters in embedding space.
  - RobustRAG (Yuan et al., 2024): Certifiable RAG defense aggregating isolated generation votes across passage subsets.
- **TrustRAG Adaptation**:
  - Employs Robust K-Means clustering and cosine distance thresholding over passage embeddings.
  - Imposes an explicit **Removal Cap ($C_r = 0.50$)** to avoid context starvation under denial-of-service conditions.
- **Genuine Original Contribution**:
  - Demonstrating that unconstrained outlier pruning in RAG causes denial-of-service when an adversary floods the top-k with poison.
  - The empirical characterization of the "Sybil Frontier": formalizing the trade-off where a system must choose between admitting residual poison or starving the generator of context.
- **Claims Requiring Stronger Evidence**:
  - Claiming MSD is superior to FilterRAG without a direct experimental comparison on the same dataset.

### 2.3 G3 Output Guardrail & HalluGuard SRM
- **Established Prior Work**:
  - HalluGuard (2024): Sentence-level claim decomposition and NLI classification using an ORPO-trained SLM.
- **TrustRAG Adaptation**:
  - Synthesizes retrieval evidence signals and answer text into a 5-class structured taxonomy (`ENTAILED`, `CONTRADICTED`, `UNGROUNDED`, `PARTIALLY_GROUNDED`, `MALICIOUS_EXECUTION`).
- **Production Truth vs. Manuscript Claim**:
  - The manuscript attributes high-level NLI reasoning to G3. However, the production repository runs `DeterministicFallbackBackend` (`is_real_model = False`). The trained DeBERTa-v3 checkpoint is not wired into the live serving path.
- **Genuine Original Contribution**:
  - The cross-layer synthesis: showing that post-generation NLI fails when the retrieved premise itself is poisoned (since the LLM faithfully generates entailed poison).

---

## 3. Summary Novelty Matrix

| Component | Technical Implementation | Novelty Level | Publication Stance |
| :--- | :--- | :--- | :--- |
| **G1 Input** | Compiled Regex & Keyword Rules | Low (Standard Engineering) | Characterize as low-latency first-line heuristic, not novel algorithm |
| **G2 Retrieval** | Robust K-Means + Removal Cap ($C_r=0.50$) | Moderate (Novel Sybil trade-off analysis) | Genuine contribution if framed around availability-security frontier |
| **G3 Output** | HalluGuard-inspired Fallback / DeBERTa NLI | Low–Moderate (NLI verification adaptation) | Must disclose deterministic runtime fallback in production |
| **Unified Pipeline** | 3-Tier Multi-Layer Defense-in-Depth | Moderate | System-level integration contribution rather than single breakthrough |
