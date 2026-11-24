# Phase 28 — Reviewer A: Security Novelty & Threat Model Evaluation

**Reviewer Role:** USENIX Security / ACM CCS Program Committee Member (Specialization: LLM Red-Teaming, Prompt Injection, RAG Poisoning)  
**Target Manuscript:** `research/manuscript/TrustRAG_Research_Paper.md`  
**Overall Recommendation:** **Borderline / Weak Reject**

---

## 1. Summary of the Work

The paper proposes TrustRAG, a multi-tier defense framework for Retrieval-Augmented Generation (RAG) systems consisting of three components:
1. G1: An input query guardrail.
2. G2: A multi-signal retrieval detector (MSD) employing robust K-means clustering to discard poisoned retrieval candidates.
3. G3: An output evidence-answer verification guardrail.

The paper reports an empirical evaluation across 500 unseen adversarial prompts (71.80% Attack Detection Rate) and 500 benign controls (0.00% False Positive Rate), accompanied by an evaluation of retrieval poisoning pruning up to an 80% Sybil poisoning ratio.

---

## 2. Strengths

1. **Unusually Candid Evaluation**: Unlike typical security submissions that claim ~100% defense rates, the authors openly report a statistically significant 28.20% drop in generalization (from 100% in earlier internal benchmarks down to 71.80%), documenting specific blind-spots in non-Latin scripts (0.0% ADR) and fictional framing (7.5% ADR).
2. **Explicit Availability Trade-Off**: The paper acknowledges and models the Sybil removal cap ($C_r = 0.50$), proving that capping outlier pruning at 50% forces residual poison (1–2 passages) into context under extreme attacks (60–80%) to prevent context starvation.
3. **Rigorous Uncertainty Quantification**: The evaluation provides exact Wilson score confidence intervals for binomial metrics ($[67.70\%, 75.57\%]$ for ADR, $[0.00\%, 0.76\%]$ for FPR) and bootstrap confidence intervals for F1 ($[80.77\%, 86.19\%]$).

---

## 3. Major Weaknesses (Novelty & Threat Model)

1. **Limited Algorithmic Novelty in G1 & G2**:
   - **G1 is Heuristic Regular Expressions**: The input guardrail is entirely composed of compiled regular expressions and lexical normalizers (`input_guardrail.py`). While fast ($0.11$ ms), pattern matching against prompt injections is well known to be fragile (Armstrong et al., 2023; Kumar et al., 2024). Once an attacker alters keywords or uses non-English languages, the defense collapses to 0%. This is not a novel security primitive.
   - **G2 MSD vs. FilterRAG**: The retrieval defense relies on robust K-Means clustering and cosine distance thresholding over passage embeddings. FilterRAG (Zou et al., USENIX Security 2025) already established frequency-density and embedding-space clustering for retrieval filtering. The manuscript must provide a clear, head-to-head experimental ablation comparing MSD against FilterRAG under identical embedding representations, rather than relying on qualitative conceptual distinctions.
2. **Mismatched Threat Model for G1/G2 Synergy**:
   - The paper frames TrustRAG as a unified defense against both direct prompt injection and retrieval poisoning. However, the ablation study (Section 6.1) shows that G1 and G2 operate in completely disjoint spaces: G1 detects 0% of corpus poisoning, and G2 detects 0% of prompt injections. There is no feedback loop or cross-layer signal propagation between G1, G2, and G3.
   - If an attacker injects a second-order prompt injection into a retrieved document (indirect prompt injection), G1 cannot see it. Does G2 cluster it out? If the indirect injection is semantically similar to the query, G2's distance filter will retain it. G3 then inspects factuality, not execution safety. This leaves a severe vulnerability gap in the threat model.
3. **Absence of Adaptive White-Box Attacks**:
   - The evaluation tests black-box prompt variants, but does not evaluate an adaptive adversary who knows the regex dictionary (for G1) or the clustering threshold $\epsilon$ (for G2). Against regexes, an adaptive adversary trivially circumvents G1 with 100% ASR by inserting innocuous homoglyphs or minor spelling perturbations not covered in the static ruleset.

---

## 4. Minor Weaknesses

1. **G3's Concrete Role is Underspecified**: The paper discusses G3 as an evidence verifier, but in the empirical evaluation of Section 5, only G1 and G2 are evaluated under the 1000-sample test suite. The performance of G3 on hallucination detection under attack is missing from the primary generalization tables.
2. **Misleading Nomenclature**: Calling G1 a "neural-adjacent guardrail" or implying heavy ML machinery in early drafts obscures what is fundamentally a high-performance regex engine.

---

## 5. Required Experiments for Top-Tier Publication

1. **Head-to-head empirical comparison with FilterRAG & ML-FilterRAG**:
   Run FilterRAG and MSD on the exact same poisoned benchmark corpus (e.g. PoisonedRAG / NQ / HotpotQA) and report Precision, Recall, and Clean Recall under identical retrieval settings.
2. **Adaptive White-Box Adversary Evaluation**:
   Formulate a gradient-based or greedy coordinate search (GCG) attack against the regex/embedding boundary to establish empirical minimum edit distance required to bypass G1.
3. **Indirect Prompt Injection Suite**:
   Evaluate 200 indirect prompt injections placed inside top-k retrieved documents to determine whether G2 or G3 provides any defense against retrieval-mediated execution hijacking.

---

## 6. Questions to Authors

1. When an adversary embeds a jailbreak payload into a high-relevance document (indirect prompt injection), which guardrail is responsible for intercepting it, and what is its measured ADR?
2. Why should the security community adopt G1 regex rules over open-source semantic guardrails (e.g., Llama Guard, NeMo Guardrails) despite the severe 0% multilingual blind spot?
