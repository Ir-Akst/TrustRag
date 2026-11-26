# TrustRAG Phase 11.2 — Step 06: Annotation Protocol & Quality Gate

**Author:** Senior ML Evaluation Engineer & Independent Research Auditor  
**Date:** 2026-11-18  
**Repository:** `/home/aditya/rags/TrustRag-phase11` — Branch `phase-11`  
**Delivered For:** Phase 11.2 Clean RAG Benchmark Quality Verification

---

## 1. Principles of Defensible NLI Ground Truth

In natural language inference for RAG verification, assigning directional labels between retrieved evidence (premise $P$) and generated claim (hypothesis $H$) requires strict formal definitions:

1. **`ENTAILMENT` ($y = 0$):** A human evaluator confirms that every factual claim in $H$ is logically and semantically justified by $P$.
2. **`CONTRADICTION` ($y = 1$):** A human evaluator confirms that one or more claims in $H$ directly conflict with, refute, or contradict factual statements in $P$.
3. **`NEUTRAL` ($y = 2$):** $H$ introduces propositions, entities, or relations not mentioned or supported in $P$, but does not directly contradict any statement in $P$.

---

## 2. RAGTruth Human Annotation Protocol & Ground-Truth Derivation

The benchmark selected for Phase 11.2 Step 06 utilizes the gold-standard human annotations provided in RAGTruth (`data/processed/ragtruth/test.jsonl`).

### 2.1 Original Human Annotation Workflow
In the original RAGTruth study:
- Independent human annotators evaluated LLM-generated responses against reference source passages.
- Annotators marked exact character start-and-end spans for any hallucinated statements.
- Spans were categorized into specific hallucination typology:
  - `Evident Conflict`: Explicit factual contradiction against source text.
  - `Subtle Conflict`: Nuanced contradiction requiring contextual inference.
  - `Evident Baseless Info`: Extraneous assertion entirely unmentioned in source text.
  - `Subtle Baseless Info`: Plausible assertion unsupported by source text.

### 2.2 Derivation Rule for 3-Way NLI
To map RAGTruth records into rigorous 3-way NLI evaluation pairs:

$$\text{NLI Label} = \begin{cases} 
\text{ENTAILMENT} & \text{if } \text{label} = \text{"FACTUAL"} \text{ (zero hallucination spans)} \\
\text{CONTRADICTION} & \text{if } \text{spans contain } \text{"Conflict"} \text{ and NO } \text{"Baseless Info"} \\
\text{NEUTRAL} & \text{if } \text{spans contain } \text{"Baseless Info"} \text{ and NO } \text{"Conflict"} \\
\text{EXCLUDE} & \text{if spans contain BOTH } \text{"Conflict"} \text{ and } \text{"Baseless Info"}
\end{cases}$$

### 2.3 Quarantine of Mixed-Label Ambiguity
When an LLM response contains both a direct conflict span and an unmentioned baseless span within the same response, assigning a single atomic 3-way label introduces supervisory label noise. In strict accordance with the Track 2 remediation standard, **all 164 mixed cases were quarantined and excluded**.

---

## 3. Class Distribution & Quality Gate Results

| Class | Count | Percentage | Role in Clean Utility Audit |
| :--- | :---: | :---: | :--- |
| **`ENTAILMENT`** | **1,757** | **69.28%** | **Core Clean Evidence:** Grounded, correct retrieved passages. |
| **`NEUTRAL`** | **474** | **18.69%** | **Benign Peripheral Evidence:** Non-contradictory ungrounded claims. |
| **`CONTRADICTION`** | **305** | **12.03%** | **Security Control:** True semantic conflicts used to verify detector sensitivity. |
| **TOTAL VALID** | **2,536** | **100.00%** | **Complete Evaluation Benchmark** |
| *Clean Evidence Total* | *2,231* | *87.97%* | *Combined Entailment + Neutral (Substantially $> 1,000$)* |
| *Quarantined Mixed* | *164* | *—* | *Excluded from inference to prevent label contamination* |

---

## 4. Why QA Datasets (MS MARCO / HotpotQA) Were Not Pseudo-Labeled

During dataset discovery (Task A), candidate datasets such as MS MARCO and HotpotQA were audited for potential NLI derivation. Converting them via heuristic mapping was rejected:

1. **Relevance is Not Entailment:** A passage can be highly relevant to a query (e.g., discussing the same topic) while being non-committal or neutral regarding a specific answer claim.
2. **Negative Passages Are Not Pure Neutral:** Unselected passages in MS MARCO (`is_selected == 0`) may be redundant (containing the answer), out-of-date/contradictory, or irrelevant. Assuming all unselected passages are neutral without human review introduces pervasive false-negative and false-positive noise.
3. **Audit Integrity:** Heuristic pseudo-labeling violates the core constraint: *"Do not claim that QA relevance labels automatically constitute NLI entailment labels. Do not manufacture ground truth."*

---

## 5. Quality Gate Verdict

### Quality Gate Status: **`PASSED`**

The benchmark constructed from the RAGTruth held-out test split meets all criteria:
- Human-verified ground truth with character-level span backing.
- Exactly 2,536 valid pairs with clean 3-way semantics.
- 2,231 clean evidence pairs available for false-alarm utility testing.
- Document-disjoint from Phase 11.1 training and validation splits.
- Zero fabricated or pseudo-labeled instances.

