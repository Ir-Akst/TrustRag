# TrustRAG Track 2, Step 2: Paper Target Format Verification Report

## 1. Scope & Research Objective

This report investigates the target format requirements across the foundational research papers supporting TrustRAG to establish whether Supervised Fine-Tuning (SFT) mandates:
1. Evidence-grounded response generation.
2. Structured JSON outputs.
3. Citation references.
4. Chain-of-thought `<think>` tags or intermediate reasoning traces.
5. Verification/classification targets.

---

## 2. Research Paper Target Format Analysis

### Paper B: TrustRAG (RAG Security & Multi-Tier Guardrails)
- **Document Source:** `TrustRAG_RAG_Security_Paper.pdf`
- **Primary Section:** Section 6.3 "Output Guardrail (G3)" (Page 5)
- **Key Methodology & Specification:**
  - **Atomic Claim Decomposition:** G3 operates by decomposing candidate generation responses into discrete, testable atomic claims:
    $$\mathcal{C}(y) = \{c_1, c_2, \dots, c_m\}$$
  - **Evidence Grounding:** Each claim $c_i$ is evaluated against retrieved evidence passages $\mathcal{D} = \{d_1, \dots, d_k\}$ to determine an alignment status:
    - `SUPPORTED`: Entailed by evidence.
    - `CONTRADICTED`: Directly refuted by evidence.
    - `UNMENTIONED` / `UNCERTAIN`: Absent from evidence passages.
  - **Evidence Coverage Check:** TrustRAG computes factual support coverage $\text{Cov}(y, \mathcal{D})$:
    $$\text{Cov}(y, \mathcal{D}) = \frac{|\{c \in \mathcal{C}(y) : \text{verdict}(c) = \text{SUPPORTED}\}|}{|\mathcal{C}(y)|}$$
    - Paper Page 5 empirical observations: Mean coverage is **0.93** for factual responses and **0.63** for hallucinated responses.
  - **Target Format Finding:** The paper specifies a **verification and evidence coverage framework**, NOT generative `<think>` reasoning traces. Structured outputs detailing claim verdicts and span conflicts are directly aligned with Section 6.3.

---

### Paper A: HalluGuard (Evidence-Grounded Self-Correction)
- **Document Source:** `HalluGuard: Evidence-Grounded Self-Correction for In-Context Hallucination Mitigation`
- **Methodology & Target Requirements:**
  - HalluGuard utilizes evidence grounding to detect factual inconsistencies in context-dependent generation.
  - It contrasts hallucinated candidate outputs against grounding evidence, requiring models to identify contradictory claims or spans.
  - **Intermediate Reasoning finding:** While generative teacher models can produce explanatory traces, downstream fine-tuning targets in HalluGuard center on detecting grounding status and generating faithful, corrected responses grounded in the context.

---

### Paper C: FilterRAG (Context Filtering & Verification)
- **Document Source:** `FilterRAG: Robust Retrieval-Augmented Generation`
- **Methodology & Target Requirements:**
  - Emphasizes contextual precision, filtering ungrounded or distractor passages prior to generation, and post-generation consistency verification.
  - Verification targets are formulated as NLI / entailment relations (`SUPPORTED` vs `CONTRADICTED`).

---

## 3. Mandatory Research Requirements vs. Implementation Choices

| Capability | Mandatory Research Requirement? | Empirical Evidence from Literature | TrustRAG `sft_v1` Implementation |
| :--- | :---: | :--- | :--- |
| **Evidence Grounding** | **YES** (Mandatory) | TrustRAG Sec 6.3; HalluGuard Sec 3 | Each example pairs query, context document, candidate response, and grounding label. |
| **Structured JSON Format** | **YES** (Standard) | TrustRAG Sec 6.3; Automated evaluation | All targets serialized as deterministic JSON with `verdict`, `grounding_status`, and conflict details. |
| **Span-Level Conflicts** | **YES** (For RAGTruth) | RAGTruth (Niu et al., 2024) | For hallucinated RAGTruth examples, all annotated human conflict spans are preserved in the target JSON. |
| **Citation References** | **NO** (Optional for G3) | TrustRAG Sec 6.3 | Document source IDs and query metadata are preserved in the schema. |
| **Generative `<think>` Traces** | **NO** (Implementation Choice) | DeepSeek-R1 / Qwen-CoT style | **Omitted in `sft_v1`**. The raw human datasets do not contain CoT traces. Synthesizing unverified traces would violate data integrity rules. |

---

## 4. Conclusion & Research Compliance

The `sft_v1` target schema conforms strictly to TrustRAG Section 6.3 G3 output verification. All target fields are grounded in authoritative human annotations without speculative synthetic data generation.

