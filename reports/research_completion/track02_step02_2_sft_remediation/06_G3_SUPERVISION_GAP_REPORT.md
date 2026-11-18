# TrustRAG Track 2, Step 2.2: G3 Supervision Gap & Human Annotation Protocol Report

## 1. Executive Position & Core Policy

**Readiness Verdict:** **`BLOCKED (NO DATASET FABRICATION)`**

In accordance with strict scientific integrity rules, **zero synthetic five-outcome G3 training records have been fabricated** in `sft_v2`.

The project formally rejects the automated conversion of heuristic or binary labels into five-way G3 targets:
- We **do not** automatically map baseless information to `INSUFFICIENT_EVIDENCE`.
- We **do not** automatically map hallucinated answers to `CONTRADICTED`.
- We **do not** automatically map mixed responses to `PARTIALLY_SUPPORTED`.
- We **do not** automatically map missing annotations to `UNCERTAIN`.

---

## 2. Deep Supervision Gap Analysis Across Five G3 Outcomes

The TrustRAG Output Guardrail (G3) specification defines five mutually exclusive decision semantics for verifying atomic claims against retrieved evidence:

### 2.1 Outcome 1: `SUPPORTED`
- **Definition:** Evidence explicitly and completely entails the generated claim.
- **Status in Raw Data:** **Available.**
- **Source:** RAGTruth factual summaries (8,369 records) and HaluEval right answers (8,500 records) provide valid, human-verified evidence entailment.

### 2.2 Outcome 2: `CONTRADICTED`
- **Definition:** Evidence explicitly contradicts or refutes the generated claim.
- **Status in Raw Data:** **Available (Subset Only).**
- **Source:** RAGTruth pure conflict annotations (1,776 records) provide direct, human-verified evidentiary contradictions.

### 2.3 Outcome 3: `PARTIALLY_SUPPORTED`
- **Definition:** Multi-clause or complex claims where a subset of propositions is entailed by evidence, but other key qualifiers or clauses lack evidence or conflict.
- **Status in Raw Data:** **Zero Valid Supervision (0 records).**
- **The Gap:** Neither RAGTruth nor HaluEval performs propositional sub-clause decomposition. RAGTruth annotates character spans, but does not provide claim-level partial entailment scores.
- **Why Automated Mapping Fails:** Assigning `PARTIALLY_SUPPORTED` to mixed conflict/baseless responses would confuse the model, because a response that directly contradicts an explicit fact should often be rejected as `CONTRADICTED` rather than accepted as partially supported.

### 2.4 Outcome 4: `INSUFFICIENT_EVIDENCE`
- **Definition:** Evidence lacks the necessary facts to prove or disprove the claim.
- **Status in Raw Data:** **Partial / Unverified.**
- **The Gap:** RAGTruth `Evident Baseless Info` marks information unmentioned in the source document. However, in abstractive summarization, models frequently introduce stylistic paraphrases or common-sense connectors that annotators marked as "new information" but which are not intended to represent retrieval-failure insufficient evidence queries.
- **Why Automated Mapping Fails:** True `INSUFFICIENT_EVIDENCE` in RAG systems occurs when a retriever fails to surface the document containing the answer. Training this requires negative retrieval evidence, which is absent from summarization tasks.

### 2.5 Outcome 5: `UNCERTAIN`
- **Definition:** Evidence is ambiguous, contradictory across sources, or too vague to support a truth determination.
- **Status in Raw Data:** **Zero Valid Supervision (0 records).**
- **The Gap:** Neither RAGTruth nor HaluEval was constructed to evaluate conflicting multi-document retrieval.

---

## 3. Human Annotation Protocol Required for Full G3 Readiness

To legitimately train a 5-outcome G3 verification model in future development tracks, the following three-stage annotation protocol must be executed:

```
Stage 1: Atomic Proposition Decomposition
  Candidate Response: y ───► Claims: {c_1, c_2, ..., c_m}
                                 │
Stage 2: Independent Claim-Level Verification
  For each c_i against Passage D:
  ├── Entailed          ──► SUPPORTED
  ├── Refuted           ──► CONTRADICTED
  ├── Absent / Missing  ──► INSUFFICIENT_EVIDENCE
  └── Ambiguous         ──► UNCERTAIN
                                 │
Stage 3: Deterministic G3 Aggregation Function
  Coverage Cov(y, D) = |Supported| / |Total Claims|
  ├── If any c_i == CONTRADICTED           ──► Final Verdict: CONTRADICTED
  ├── If Cov == 1.0                        ──► Final Verdict: SUPPORTED
  ├── If 0.0 < Cov < 1.0 (no contradiction)──► Final Verdict: PARTIALLY_SUPPORTED
  ├── If all c_i == INSUFFICIENT_EVIDENCE  ──► Final Verdict: INSUFFICIENT_EVIDENCE
  └── If any c_i == UNCERTAIN              ──► Final Verdict: UNCERTAIN
```

### Protocol Prerequisites
1. **Annotation Workforce:** Minimum 2 independent annotators per claim with adjudication by a third expert for disagreements.
2. **Negative Evidence Sampling:** Constructing paired queries with non-relevant distractors sampled from MS MARCO to provide genuine `INSUFFICIENT_EVIDENCE` instances.
3. **Conflicting Corpus Construction:** Introducing multi-document conflicting assertions to supervise `UNCERTAIN`.

Until this protocol is executed and verified, **no model training should be attempted under the claim of 5-outcome G3 readiness**.

