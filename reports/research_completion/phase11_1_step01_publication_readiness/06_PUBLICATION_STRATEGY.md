# TrustRAG — Phase 11.1, Step 1: Publication Readiness Plan
## 06 — Publication Strategy, Framing & Venue Selection

- **Audit Date:** 2026-11-14T18:15:00Z
- **Auditor:** Principal Research Scientist & Academic Publication Reviewer

---

### 1. Most Defensible Publication Framing

Attempting to sell TrustRAG as a "breakthrough foundation model" or "state-of-the-art NLI classifier" will lead to immediate rejection by reviewers who will compare it to 70B LLMs or 5M-example alignment models (AlignScore).

Instead, the paper must be framed around **System Trustworthiness, Verification Engineering, and Failure Boundary Analysis**:

#### Recommended Paper Category
**Systems & Empirical Methodology Paper** (or **Empirical Evaluation / Datasets & Benchmarks Track**)

#### Working Title Options
- **Option 1 (Systems Track — Recommended):**  
  *"TrustRAG: Calibrated Multi-Stage Verification and Adversarial Guardrails for Trustworthy Retrieval-Augmented Generation"*
- **Option 2 (Empirical Findings Track):**  
  *"When Compact Verifiers Fail: Remediating Degeneracy and Class Starvation in RAG Claim Verification"*
- **Option 3 (Security & Trustworthiness Track):**  
  *"Defending Retrieval-Augmented Generation Against Hallucination and Knowledge Poisoning via Calibrated Neural Cross-Encoders"*

---

### 2. Narrative Arc for the Paper

1. **Introduction:**  
   The vulnerability of RAG systems to hallucination and knowledge poisoning. The tradeoff between expensive frontier LLM verifiers (latency, cost) and compact cross-encoders.
2. **System Architecture:**  
   TrustRAG’s modular defense: G1 input guardrails, G2 multi-source diversity, G3 neural verification, and selective prediction.
3. **The Engineering Challenge of Verifier Training (Empirical Core):**  
   Exposing the hidden hazards of training cross-encoders on imbalanced human hallucination data. Demonstrating how naive cross-entropy leads to catastrophic collapse (Step 3.8). Presenting the mathematical remediation (Step 3.10) that stabilizes multi-class gradients.
4. **Experimental Results (Post-Phase 11.1 Execution):**  
   - Binary verification out-of-domain robustness (HaluEval + RAGTruth).
   - NLI multi-class verification and multi-chunk scaling.
   - Calibration, Brier scores, and Risk-Coverage abstention curves.
5. **End-to-End Pipeline Evaluation:**  
   Comparative benchmarks against naive RAG and Phase 10 baselines on clean and poisoned benchmarks.
6. **Reproducibility & Governance:**  
   Cryptographic audit trails, split leak isolation, and open-source artifacts.

---

### 3. Venue Ranking & Match Analysis

| Target Venue | Paper Type | Acceptance Fit | Strategic Recommendation | Key Reviewer Expectations |
| :--- | :--- | :--- | :--- | :--- |
| **EMNLP 2025 / ACL 2025 (System Demonstrations)** | Short Paper / Demo (6 pages) | **HIGH (Post Phase 11.1)** | **Primary Target for System Framing.** | Working end-to-end open-source pipeline, CLI, clean API, latency/throughput benchmarks. |
| **NeurIPS 2025 (Datasets & Benchmarks Track)** | Full Paper (9 pages) | **MODERATE-HIGH** | **Strong Target if focusing on boundary failures & benchmarks.** | Exhaustive dataset documentation, leak audits, baseline comparisons, reproducible artifacts. |
| **NAACL / EMNLP 2025 (Main Conference - Short)** | Short Paper (4-5 pages) | **MODERATE** | **Ideal for the verifier failure/remediation narrative.** | Tight, focused empirical contribution showing the collapse phenomenon and its fix. |
| **ACM CCS / USENIX Security (Security Track)** | Full Paper (12 pages) | **MODERATE (Requires strong G1/G2 experiments)** | **Viable if emphasizing Knowledge Poisoning defense.** | Formal threat model, adaptive attacker evaluations, certifiable defense baselines. |
| **ACL / EMNLP Main Conference (Long Paper)** | Long Paper (8 pages) | **LOW (Currently Unrealistic)** | **Not recommended without multi-epoch GPU training.** | Reviewers expect state-of-the-art performance across 5+ benchmarks and 1B+ models. |

---

### 4. What Would Cause Paper Rejection? (Reviewer Pitfalls to Avoid)

1. **Asserting 5-Outcome ML Classification:** If the text claims a 5-outcome machine learning model when the classifier outputs 3 logits, reviewers will issue a technical rejection for misrepresentation. (Must be framed as neural claim verification + rule-based aggregation).
2. **Submitting with Contradiction Recall < 50%:** A claim verification paper with low contradiction detection cannot pass peer review.
3. **Omitting Standard Baselines:** Missing comparisons to AlignScore, MiniCheck, and standard off-the-shelf DeBERTa MNLI.
4. **Lack of Statistical Significance:** Reporting raw accuracy improvements without bootstrap confidence intervals or McNemar's tests.
5. **Vagueness on Hardware / Compute:** Hiding that training ran on CPU with small step budgets. Reviewers appreciate honest resource documentation (e.g., "accessible training on commodity CPU").

