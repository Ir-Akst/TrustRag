# TrustRAG Research Completion — Track 1, Step 2: Experiment Protocol

## 1. Environmental & Execution Specification

To guarantee 100% reproducibility across research environments, the baseline evaluation was executed under strict isolation and deterministic settings.

- **Target Repository:** `/home/aditya/rags/TrustRag-phase11`
- **Git Branch:** `phase-11`
- **Commit HEAD:** `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`
- **Protected Baseline Repository:** `/home/aditya/rags/TrustRag` (HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Untouched)
- **Host OS:** Linux x86_64 (Kernel 7.2.14-arch1-1)
- **Python Runtime:** Python 3.14.9
- **Virtual Environment:** `/home/aditya/rags/.venv`
- **Execution Script:** `tools/evaluation/run_track02_benchmarks.py`
- **Execution Date:** 2026-11-13T21:39:00+05:30
- **Random Seed:** 42 (fixed; all baseline algorithms are deterministic)

---

## 2. Evaluated Systems & Configurations

### 2.1 Baseline Mode 1: No Verification (`no_verification`)
- **Description:** Simulates standard unverified RAG systems (vanilla LLM response delivery).
- **Behavior:** Accepts all generated claims unconditionally (`SUPPORTED`).
- **Purpose:** Establishes the lower bound for safety and upper bound for nominal acceptance.

### 2.2 Baseline Mode 2: TrustRAG Default G3 (`default_g3`)
- **Target Component:** `FactVerificationPipeline` in `src/trustrag/guardrails/output_guardrail.py`.
- **Claim Extraction:** Deterministic sentence boundary parsing with pronoun/token filtering.
- **Evidence Alignment:** TF-IDF cosine similarity between claim tokens and context sentences.
- **Verification Logic:**
  - Token overlap threshold: `0.6`
  - Polarity negation detection: active.
  - Abstention on insufficient evidence: active.
- **Verdict Mapping:**
  - `SUPPORTED` / `PARTIALLY_SUPPORTED` -> Predicted Factual (Negative for Hallucination)
  - `CONTRADICTED` -> Predicted Hallucinated (Positive for Hallucination)
  - `INSUFFICIENT_EVIDENCE` / `UNCERTAIN` -> Abstained / Fallback to Contradicted for safety classification.

### 2.3 Baseline Mode 3: TrustRAG Strict G3 (`strict_g3`)
- **Verification Logic:** Elevated token overlap threshold: `0.8`.
- **Purpose:** Measures the impact of higher conservative thresholds on false supported rates and false contradiction rates.

### 2.4 Baseline Mode 4: TrustAwareRetriever Candidate Re-ranking
- **Target Component:** `TrustAwareRetriever` in `src/trustrag/retrieval/retriever.py`.
- **Corpus Modes:**
  - HotpotQA: 10 distractor candidate paragraphs per query (2 gold, 8 negative distractors).
  - MS MARCO: 6-10 search result candidate snippets per query (average 10.0 passages).
- **Ranking Function:** Lexical BM25/TF-IDF token overlap scoring against candidate pools.
- **Evaluation Cutoffs:** k in {1, 5, 10}.

---

## 3. Metrics Definition

### 3.1 Hallucination Detection Metrics (G3)
- **Positive Class:** `HALLUCINATED`
- **Negative Class:** `FACTUAL`
- **True Positive (TP):** Ground truth is HALLUCINATED, verifier flags CONTRADICTED / INSUFFICIENT_EVIDENCE.
- **False Positive (FP):** Ground truth is FACTUAL, verifier flags CONTRADICTED / INSUFFICIENT_EVIDENCE (False Alarm).
- **True Negative (TN):** Ground truth is FACTUAL, verifier flags SUPPORTED / PARTIALLY_SUPPORTED.
- **False Negative (FN):** Ground truth is HALLUCINATED, verifier flags SUPPORTED / PARTIALLY_SUPPORTED (Safety Failure).
- **False Supported Rate (FSR):** $FSR = \frac{FN}{FN + TP} = \frac{\text{False Supported}}{\text{Total Hallucinated}}$
- **False Contradiction Rate (FCR):** $FCR = \frac{\text{Contradicted on Factual}}{\text{Total Factual}}$
- **Abstention Rate:** $\frac{\text{INSUFFICIENT\_EVIDENCE} + \text{UNCERTAIN}}{\text{Total Evaluated}}$

### 3.2 Retrieval Metrics
- **Recall@k:** Proportion of queries where at least one ground-truth passage appears in the top-k ranked candidates.
- **MRR@k:** Mean Reciprocal Rank of the highest-ranked relevant passage within the top-k candidates.
