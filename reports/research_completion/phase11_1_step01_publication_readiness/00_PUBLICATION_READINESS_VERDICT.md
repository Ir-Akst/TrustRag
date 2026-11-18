# TrustRAG — Phase 11.1, Step 1: Publication Readiness Plan
## 00 — Publication Readiness Verdict & Executive Summary

- **Audit Date:** 2026-11-14T18:15:00Z
- **Role:** Principal Research Scientist, Independent ML Experimental Auditor & Academic Publication Reviewer
- **Target Repository:** `/home/aditya/rags/TrustRag-phase11` (`phase-11` @ `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)
- **Baseline Repository:** `/home/aditya/rags/TrustRag` (`phase-10` @ `e65bcc80aac634900d1f8e343880fddf66cec168`, strictly immutable)

---

### 1. Final Publication-Readiness Verdict

$$\mathbf{PUBLICATION\; READINESS\; VERDICT:\; NOT\_READY\_FOR\_SUBMISSION\; (SUBMISSION\_BLOCKED)}$$

| Review Dimension | Status | Reviewer Assessment |
| :--- | :--- | :--- |
| **Scientific Claim Defensibility** | **INSUFFICIENT** | Current empirical evidence cannot support broad claims of effective 3-class NLI verification (Contradiction Recall: **4.49%**). Attempting to submit with current model metrics would invite immediate peer-review rejection. |
| **Engineering Implementation** | **EXCELLENT** | Complete and robust software pipeline, class-balanced training harnesses, multi-chunk cross-encoders, and rigorous evidence governance (55 passing unit tests, 1 documented skip). |
| **End-to-End Evaluation** | **MISSING** | The trained neural verifiers (`deberta-v3-small-binary` and `deberta-v3-small-nli-remediated`) have **never been benchmarked inside `TrustRagPipeline`** against baseline RAG systems. |
| **Evaluation Completeness** | **PARTIAL** | Binary verification is solid on 1,000 samples (76.6% accuracy, 91.3% precision), but NLI verification is restricted to an under-converged 1,000-step pilot (~9.2% of data) with unlogged raw probabilities. |
| **Retrieval Evaluation** | **LOCAL-ONLY** | Evaluated only on 10 candidate snippets per query; full-corpus retrieval across 5.23M/8.84M collections remains blocked. |

---

### 2. Strongest Defensible Research Contribution Today

If constrained to submit a paper based strictly on **existing validated evidence**, the manuscript must be framed narrowly as a **Systems & Methodology / Empirical Case Study paper**:

> **"On the Mechanics and Hazards of Bounded Cross-Encoder Verifiers in RAG Pipelines: An Empirical Case Study of Degeneracy Remediation and Evidence Retention"**
> 
> *Core Defensible Claim:* Fine-tuning lightweight cross-encoders (141M DeBERTa-v3) for RAG verification on imbalanced human hallucination benchmarks triggers severe tail-starvation and false-majority collapse (0% Entailment recall), which can be structurally remediated via class-balanced sampling and hypothesis-preserving serialization. Binary verification provides robust out-of-domain discrimination (76.6% accuracy, 91.3% hallucination precision on 1,000 samples), but 3-way NLI requires substantially higher step budgets and focal supervision to overcome severe minority-class contradiction blindness.

---

### 3. Top Five Blocking Research Gaps (Pre-Submission Requirements)

1. **Failure of Contradiction Discrimination in 3-Way NLI:** The remediated pilot identifies only 16 of 356 true contradictions (4.49% recall), misclassifying 71.6% of contradictions as Neutral. Full-dataset training (10,815 samples) with focal loss or asymmetric class weighting is mandatory.
2. **Missing End-to-End Pipeline Evaluation:** Zero comparative benchmarks exist measuring `TrustRagPipeline` using trained neural verifiers against clean RAG, naive RAG, or commercial LLM verifiers.
3. **Missing Per-Sample Probability Dumps:** Raw softmax probability triples $[p_0, p_1, p_2]$ were discarded during Step 3.16 evaluation, rendering Brier score ($0.661$) and ECE-10 ($0.130$) not independently reproducible.
4. **Full-Corpus Retrieval Staging:** Retrieval evaluations remain restricted to 10-candidate snippet re-ranking because full 5.23M HotpotQA Wikipedia and 8.84M MS MARCO collections are not staged.
5. **Supervision Gap for 5-Outcome G3 Decisions:** The pipeline claims five G3 verification states (`SUPPORTED`, `CONTRADICTED`, `NEUTRAL`, `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`), but only a 3-class NLI model was trained. Partial support and insufficiency are heuristic rule-based aggregations without human-annotated ground-truth test splits.

---

### 4. Recommended Target Venue & Strategy

- **Premature Target (Would be Rejected):** ACL / EMNLP Main Conference (Long Paper) — Reviewers will reject based on 4.49% contradiction recall and lack of full-corpus / end-to-end RAG evaluations.
- **Defensible Target Post-Convergence (Phase 11.1 Execution):** EMNLP / NAACL System Demonstrations, EACL / COLING Short Paper, or NeurIPS Datasets and Benchmarks Track, framed around evidence-grounded verification architectures, boundary failure analysis, and calibrated abstention in RAG.

