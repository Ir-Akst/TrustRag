# Phase 28 — Missing Experiments & Reviewer Blockers

This document prioritizes the missing empirical experiments identified during peer review, categorizing them by their criticality to publication success.

---

## 1. Priority Tier 1: Essential for Scientific Correctness (Reviewer Blockers)

Without these revisions/experiments, the paper will receive an immediate rejection from top-tier security reviewers.

1. **Direct Empirical Comparison with FilterRAG on the Same Dataset**:
   - *Issue*: The paper claims advantages over FilterRAG without a shared empirical benchmark.
   - *Experiment*: Run FilterRAG (frequency density filtering) and TrustRAG MSD (robust K-means) on the exact same 500-passage corpus under identical embedding representations (e.g. `all-MiniLM-L6-v2` or `bge-small-en-v1.5`).
   - *Metrics to Report*: Poison Precision, Poison Recall, Clean Passage Retention, and Latency.
2. **Correcting the Two-Proportion $z$-test Presentation**:
   - *Issue*: Applying a two-sample hypothesis test across different benchmark datasets (Phase 25 vs. Phase 26) violates statistical independence and distribution assumptions.
   - *Action*: Remove the $z=7.62$ hypothesis test. Present the 28.20% drop as an empirical distribution shift between unit regression testing and diverse red-teaming.
3. **Decoupled Architecture Latency Profiling**:
   - *Issue*: Reporting $1.42$ ms pipeline latency while discussing DeBERTa neural weights misleads reviewers.
   - *Action*: Report two separate columns in the performance table:
     - Profile A: Production CPU Fallback ($1.42$ ms).
     - Profile B: Live DeBERTa-v3 Neural NLI Serving ($\approx 65$ ms).

---

## 2. Priority Tier 2: Essential for Security Claims (Adversarial Robustness)

1. **Adaptive White-Box Adversary Against G1 Regexes**:
   - *Issue*: Static regex rules are trivially bypassed once known.
   - *Experiment*: Evaluate an adaptive adversary using automated character substitutions, zero-width homoglyphs, or semantic synonym replacement to determine the minimum perturbation budget required to bypass G1.
2. **Indirect Prompt Injection in Retrieved Context**:
   - *Issue*: If an attacker injects a prompt injection payload into a knowledge passage rather than the user query, G1 does not inspect it.
   - *Experiment*: Test whether G2 clusters out indirect prompt injections, or whether they pass unhindered to the generator.
3. **Non-Latin Multilingual Hardening Evaluation**:
   - *Issue*: G1 achieved 0.0% ADR on Cyrillic, Chinese, Hindi, Arabic, and Japanese.
   - *Experiment*: Evaluate whether simple unicode NFKC normalization or lightweight multilingual tokenizers can recover basic detection without inflating latency.

---

## 3. Priority Tier 3: Essential for Reproducibility

1. **Self-Contained Containerization (Dockerfile)**:
   - *Issue*: Current reproduction instructions rely on local virtual environment paths (`/home/aditya/rags/.venv-phase15-clean10`).
   - *Action*: Provide a standard `Dockerfile` or `environment.yml` to allow push-button verification by external artifact reviewers.
2. **Synthetic Template Bias Correction**:
   - *Issue*: 40% of benign queries contain repetitive artificial suffixes like `(Context aspect #1)`.
   - *Action*: Evaluate on a 100% natural conversational query corpus (e.g. MS MARCO natural user questions, LMSYS Chatbot Arena benign queries) to verify that Clean FPR remains $< 1.0\%$.

---

## 4. Priority Tier 4: Optional Future Work

1. Hardware acceleration benchmarks (NVIDIA TensorRT-LLM / ONNX Runtime) for the neural DeBERTa backend.
2. Dynamic adaptation of the removal cap $C_r$ based on corpus entropy.
