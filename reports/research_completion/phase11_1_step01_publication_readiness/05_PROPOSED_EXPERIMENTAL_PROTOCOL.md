# TrustRAG — Phase 11.1, Step 1: Publication Readiness Plan
## 05 — Proposed Experimental Protocol & Pre-Registration

- **Audit Date:** 2026-11-14T18:15:00Z
- **Auditor:** Principal Research Scientist & Reproducibility Engineer

---

### 1. Experimental Protocol Principles

To avoid post-hoc hypothesizing and metric shopping, the following three core experiments are formally pre-registered with hypotheses, baseline comparisons, fixed random seeds, and strict failure criteria.

---

### 2. Experiment 1: Full-Dataset NLI Convergence & Contradiction Remediation (Essential)

- **Research Question:** Does full-dataset training with class-weighted focal loss resolve the minority-class contradiction blindness observed in the 1,000-step pilot?
- **Hypothesis:** Scaling from 1,000 steps to 3 full epochs (10,815 samples, effective batch size 4, 8,110 steps) with class weights $w = [1.0, 3.5, 1.5]$ will increase Contradiction Recall from 4.49% to $\ge 65.0\%$ and Macro F1 from 0.297 to $\ge 0.650$.
- **Dataset & Split:** `data/processed/sft_v2/nli/train.jsonl` (10,815) and `validation.jsonl` (2,662).
- **Baselines:** 
  1. Step 0 Unadapted Model (24.19% Acc, 0% Contradiction Recall).
  2. Step 3.8 Collapsed Run (24.12% Acc, 19.10% Contradiction Recall, 0% Entailment Recall).
  3. Step 3.16 Remediated Pilot (38.05% Acc, 4.49% Contradiction Recall).
  4. Off-the-shelf DeBERTa-v3-small MNLI zero-shot baseline.
- **Model Architecture:** DeBERTa-v3-small (`deberta-v2`, 141.9M parameters, FP32).
- **Hyperparameters:** Max sequence length: 384; Learning rate: $2\times 10^{-5}$; Warmup steps: 500; Weight decay: 0.01; Gradient clipping: 1.0; Seed: `42`.
- **Primary Metrics:** Contradiction Recall, Macro F1, Balanced Accuracy, ECE-10, Brier Score. (All with 95% bootstrap confidence intervals, $N=1,000$ iterations).
- **Failure Criterion:** If Contradiction Recall remains $< 50.0\%$ after 3 epochs, the hypothesis is refuted; RAGTruth alone is insufficient, requiring auxiliary NLI data (MNLI/ANLI).
- **Required Persisted Artifacts:** `model.safetensors`, `training_meta.json`, `predictions_val.jsonl` (with raw logits, probability triples, and sample IDs).

---

### 3. Experiment 2: Full Validation Split Binary Benchmark (Essential)

- **Research Question:** What is the true generalization accuracy of the trained binary cross-encoder across all task domains in HaluEval and RAGTruth?
- **Hypothesis:** Evaluated over the full 5,984 validation split (2,966 HaluEval + 3,018 RAGTruth), the binary verifier maintains an overall accuracy $\ge 75.0\%$ and Hallucination Precision $\ge 88.0\%$.
- **Dataset & Split:** Full `data/processed/sft_v2/binary/validation.jsonl` (5,984 records).
- **Sub-Task Breakdowns:**
  - HaluEval QA, Dialogue, Summarization.
  - RAGTruth News, COVID-19 QA, Yelp Data2Text.
- **Baselines:**
  1. Majority-class baseline (52.56% Factual).
  2. Lexical ROUGE-1 / ROUGE-L overlap thresholding.
  3. Pretrained DeBERTa-v3-small zero-shot classifier.
- **Primary Metrics:** Accuracy, Balanced Accuracy, Precision/Recall/F1 per class, ROC-AUC, PR-AUC, ECE-10, Risk-Coverage Curve.
- **Failure Criterion:** If Hallucination Recall drops below $50.0\%$ on the full validation split, the binary verifier is deemed too conservative for production deployment.
- **Required Persisted Artifacts:** `binary_full_val_results.json`, `predictions_binary_val.jsonl`.

---

### 4. Experiment 3: End-to-End Pipeline Verification Benchmark (Essential for System Paper)

- **Research Question:** Does integrating the trained binary and NLI cross-encoders into `TrustRagPipeline` measurably reduce downstream hallucination rates without inducing excessive false abstentions?
- **Hypothesis:** TrustRAG with trained cross-encoders reduces response hallucination rate by $\ge 40\%$ relative to naive RAG on poisoned and hallucination evaluation suites, while maintaining an abstention rate $< 25\%$ on clean queries.
- **Benchmark Suites:** 
  1. Clean RAG Test (`clean_rag_test`).
  2. Knowledge Poisoning Test (`knowledge_poisoning_test`, multi-poison 2x).
  3. Hallucination Test (`hallucination_test`).
- **Configurations Compared:**
  1. `Naive-RAG`: BM25 retrieval + Generator LLM (no verifier).
  2. `FilterRAG`: BM25 + Heuristic keyword filter.
  3. `TrustRAG-Phase10`: Pipeline with Phase 10 heuristic verifiers.
  4. `TrustRAG-Neural-Binary`: Pipeline with trained binary verifier.
  5. `TrustRAG-Neural-NLI`: Pipeline with remediated 3-way NLI verifier.
- **Primary Metrics:** Answer Exact Match (EM), ROUGE-L, Faithfulness Rate (%), Hallucination Rate (%), Abstention Rate (%), End-to-End P95 Latency (s).
- **Statistical Significance:** Paired bootstrap test ($p < 0.01$) and McNemar’s test on binary correctness.
- **Failure Criterion:** If neural verification increases clean query abstention $> 35\%$ or fails to achieve a statistically significant ($p < 0.05$) reduction in hallucination rate on poisoned suites.
- **Required Persisted Artifacts:** `end_to_end_benchmark_results.json`, per-sample pipeline execution traces.

---

### 5. Experiment 4: Multi-Chunk vs. Single-Window Verification Ablation (Important Supporting)

- **Research Question:** Does sliding-window multi-chunk inference (`nli_multi_chunk.py`) outperform single-window 384-token truncation on long documents?
- **Hypothesis:** On premises $> 400$ tokens ($N \approx 850$ samples), multi-chunk inference with `CONTRADICTION_PRIORITY` detects $\ge 25\%$ more contradictions than single-window truncation.
- **Dataset:** Long-premise slice of `data/processed/sft_v2/nli/validation.jsonl`.
- **Ablation Settings:**
  - Setting A: Single Window 128 (Step 3.8 baseline).
  - Setting B: Single Window 384 (Step 3.16 baseline).
  - Setting C: Multi-Chunk 384 (stride 320) with Mean Pooling.
  - Setting D: Multi-Chunk 384 (stride 320) with `CONTRADICTION_PRIORITY`.
- **Metrics:** Contradiction Recall, False Positive Rate, Inference Latency per document.

