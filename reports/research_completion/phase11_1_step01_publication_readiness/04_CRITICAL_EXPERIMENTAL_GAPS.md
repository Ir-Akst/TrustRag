# TrustRAG — Phase 11.1, Step 1: Publication Readiness Plan
## 04 — Critical Experimental Gaps & Scientific Failure Analysis

- **Audit Date:** 2026-11-14T18:15:00Z
- **Auditor:** Principal Research Scientist & Academic Publication Reviewer

---

### 1. In-Depth Diagnosis of Gap A: NLI Contradiction Blindness

#### Empirical Symptoms in Step 3.16
In Step 3.16 (`training_results.json`), after 1,000 optimizer steps with a class-balanced sampler:
- **True Contradiction Count:** 356 samples in validation set.
- **Predicted as Contradiction:** 16 samples (**Recall: 4.49%**).
- **Misclassified as Neutral:** 255 samples (**71.6% of contradictions**).
- **Misclassified as Entailment:** 85 samples (**23.9% of contradictions**).

#### Root-Cause Analysis
1. **Severe Imbalance in Raw RAGTruth Supervision:**  
   In `data/processed/sft_v2/nli/train.jsonl`, the unweighted distribution is 6,707 ENTAILMENT (62.0%), 2,688 NEUTRAL (24.9%), and only 1,420 CONTRADICTION (13.1%).
2. **Subtle vs. Evident Contradiction Semantics:**  
   In RAGTruth, contradictions frequently hinge on a single conflicting date, named entity, or numeric quantity embedded in a 400-word premise. In an unweighted cross-entropy loss, the model minimizes loss fastest by classifying ambiguous or complex pairs as `NEUTRAL` (the majority "safe" class when entailment is uncertain).
3. **Pilot Budget Insufficiency:**  
   1,000 steps with $B=1$ exposed the model to only 1,000 samples (~9.25% of the 10,815 training samples). While 1,000 steps was sufficient for binary classification (where any conflict maps to Hallucinated), distinguishing subtle contradiction from unmentioned neutral information requires fine-grained token-level cross-attention that takes multiple full-dataset epochs to converge.
4. **Hypothesis vs. Premise Length Asymmetry:**  
   Hypotheses average 25–40 tokens, whereas premises average 280–450 tokens. Even with 384-token windowing, the attention weights over the single conflicting sentence are diluted across hundreds of non-contradictory premise tokens.

#### Remediation Requirement for Publication
To achieve publication-grade contradiction detection:
- Transition from unweighted cross-entropy to **Class-Weighted Cross-Entropy** or **Focal Loss** ($\gamma = 2.0$) with class weight vector $w = [1.0, 3.5, 1.5]$.
- Scale training from a 1,000-step pilot to **3 full epochs over the complete 10,815 dataset** (~32,445 optimizer steps, or ~8,110 steps at effective batch size 4).
- Minimum acceptance gate for publication: **Contradiction Recall $\ge 65.0\%$ and Macro F1 $\ge 0.650$**.

---

### 2. Diagnosis of Gap B: Binary Verifier Generalization & Test Isolation

- **Current Evidence:** 76.6% accuracy on 1,000 validation samples (500 HaluEval + 500 RAGTruth).
- **Experimental Gap:** The complete validation split in `data/processed/sft_v2/binary/validation.jsonl` contains **5,984 samples** (2,966 HaluEval + 3,018 RAGTruth). The 1,000-sample test was an ad-hoc subset.
- **Reviewer Requirement:** Academic reviewers will require evaluation over the **entire 5,984 validation split**, broken down by sub-task (HaluEval QA vs Dialogue vs Summarization; RAGTruth News vs COVID vs Yelp), accompanied by 95% bootstrap confidence intervals.

---

### 3. Diagnosis of Gap C: End-to-End RAG Pipeline Integration

- **Current Evidence:** Zero end-to-end runs have been conducted using `deberta-v3-small-binary` or `deberta-v3-small-nli-remediated` inside `TrustRagPipeline`.
- **Reviewer Requirement:** A credible paper must present an end-to-end comparative table:

$$\begin{pmatrix}
\text{Pipeline Configuration} & \text{Exact Match} & \text{ROUGE-L} & \text{Faithfulness (\%)} & \text{Hallucination Rate (\%)} & \text{Abstention Rate (\%)} & \text{P95 Latency (s)} \\
\text{Standard RAG (No verifier)} & - & - & - & - & 0.0\% & - \\
\text{RAG + Heuristic Verifier (Phase 10)} & - & - & - & - & - & - \\
\text{RAG + Binary Neural Verifier (Ours)} & - & - & - & - & - & - \\
\text{RAG + 3-Way NLI Verifier (Ours)} & - & - & - & - & - & - \\
\text{RAG + GPT-4o Zero-Shot Verifier} & - & - & - & - & - & -
\end{pmatrix}$$

Without these numbers, reviewers will dismiss the work as disconnected modular training exercises rather than an integrated RAG system.

---

### 4. Diagnosis of Gap D: Five-Outcome G3 Supervision

- **Current Reality:** In `src/trustrag/verification/output_verifier.py`, `PARTIALLY_SUPPORTED` and `INSUFFICIENT_EVIDENCE` are deterministic rule aggregations.
- **Reviewer Requirement:** If the paper claims a 5-outcome verification framework, the authors must either:
  a) Explicitly describe G3 as a **two-stage hybrid architecture** (neural claim verification $\to$ deterministic answer aggregation), which is scientifically defensible.
  b) Or conduct an empirical human evaluation measuring agreement between G3 rule verdicts and human annotators across 200 multi-claim answers (Cohen's $\kappa \ge 0.70$).

---

### 5. Diagnosis of Gap E: Full-Corpus Retrieval Staging

- **Current Reality:** Step 2.4 evaluated candidate re-ranking on 10 snippets. Full Wikipedia (5.23M passages, ~2.5 GB) and MS MARCO (8.84M passages, ~3.2 GB) collections are missing on disk.
- **Reviewer Requirement:** If the paper claims retrieval contributions, it must evaluate against the official `qrels.dev.small.tsv` for MS MARCO and the official HotpotQA distractor/fullwiki benchmark splits. Otherwise, the paper must restrict its claims strictly to "Candidate Verification and Reranking".

---

### 6. Diagnosis of Gap F: Calibration & Selective Prediction Artifacts

- **Current Reality:** Step 3.16 recorded scalar ECE ($0.130$) and Brier ($0.661$), but raw probabilities were discarded, preventing verification or plotting reliability diagrams.
- **Reviewer Requirement:** Future evaluation runs must serialize `predictions.jsonl` containing `[p_ent, p_con, p_neu]`. The paper must report Risk-Coverage curves (Selective Classification) demonstrating that abstaining on low-confidence samples monotonically decreases error rate.

