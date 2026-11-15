# TrustRAG Track 2, Step 2.1: G3 Five-Outcome Compatibility Audit Report

## 1. TrustRAG G3 Output Guardrail Decision Semantics

The TrustRAG architectural specification defines the **G3 Output Guardrail** as an evidence-grounded verification system operating on decomposed atomic claims $\mathcal{C}(y) = \{c_1, \dots, c_m\}$ against retrieved evidence passages $\mathcal{D}$.

The authoritative G3 decision framework specifies five mutually exclusive outcomes:
1. **`SUPPORTED`**: The evidence passage explicitly entails the claim.
2. **`CONTRADICTED`**: The evidence passage directly refutes the claim.
3. **`PARTIALLY_SUPPORTED`**: Part of a multi-clause claim is entailed, but key qualifiers or clauses lack evidence or conflict.
4. **`INSUFFICIENT_EVIDENCE`**: The evidence passage neither entails nor refutes the claim; necessary premises are absent.
5. **`UNCERTAIN`**: The evidence is ambiguous, vague, or internally inconsistent, precluding a definitive factual determination.

---

## 2. Empirical Mapping in `sft_v1`

Independent audit of all 32,090 records in `data/processed/sft_v1/` shows the following distribution of target verdicts:

| G3 Target Verdict | Train Count (26,072) | Train % | Val Count (6,018) | Val % | Total Records (32,090) | Total % | Presence in `sft_v1` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`SUPPORTED`** | 13,660 | 52.40% | 3,209 | 53.32% | 16,869 | 52.57% | Fully Represented |
| **`CONTRADICTED`** | 12,412 | 47.60% | 2,809 | 46.68% | 15,221 | 47.43% | Over-Represented |
| **`PARTIALLY_SUPPORTED`** | **0** | **0.00%** | **0** | **0.00%** | **0** | **0.00%** | **Completely Missing** |
| **`INSUFFICIENT_EVIDENCE`** | **0** | **0.00%** | **0** | **0.00%** | **0** | **0.00%** | **Completely Missing** |
| **`UNCERTAIN`** | **0** | **0.00%** | **0** | **0.00%** | **0** | **0.00%** | **Completely Missing** |

---

## 3. Critical Compatibility Defects

### 3.1 Total Absence of 3 of the 5 Outcomes (60% Taxonomy Void)
The `sft_v1` dataset provides **zero training examples** for:
- `PARTIALLY_SUPPORTED` (0 examples)
- `INSUFFICIENT_EVIDENCE` (0 examples)
- `UNCERTAIN` (0 examples)

If a neural network is fine-tuned on `sft_v1` with a 5-way classification head, the cross-entropy loss will never backpropagate gradients for these three classes. The resulting model will:
1. Suffer from degenerate softmax collapse, predicting only `SUPPORTED` or `CONTRADICTED`.
2. Exhibit a 0.00% recall on partial support, insufficient evidence, and uncertainty in production evaluation.

### 3.2 Pathological Equivalence: Hallucination $\equiv$ Contradiction
By forcing all non-factual records into `CONTRADICTED`, the dataset trains models to adopt an unsound epistemic policy:
$$\forall c, \mathcal{D}: \quad (\mathcal{D} \not\models c) \implies (\mathcal{D} \models \neg c)$$
In formal logic and RAG security, **lack of evidence is not proof of contradiction**.

In real-world RAG deployments, the vast majority of retrieval failures produce passages where the user's answer is simply *missing* or *unmentioned* (e.g. an outdated company policy document or a missing medical record). Under the current `sft_v1` training regime, the model will report `CONTRADICTED` (refuted) instead of correctly reporting `INSUFFICIENT_EVIDENCE`.

### 3.3 Loss of Uncertainty Preservation
In RAGTruth, annotators labeled spans as `Subtle Baseless Info` (2,527 spans) and `Subtle Conflict` (201 spans) where evidence was borderline or nuanced. The Step 2 pipeline erased this subtlety, mapping them to hard binary verdicts.

---

## 4. Auditor Conclusion on G3 Training Feasibility

| Training Objective | Feasibility on `sft_v1` | Auditor Verdict |
| :--- | :---: | :---: |
| **Binary Faithfulness Detector** ($y \in \{0, 1\}$) | Supported by 32,090 balanced records. | **FEASIBLE** |
| **Evidence-Grounded NLI Verifier** (Entailment vs Non-Entailment) | Supported as binary entailment. | **FEASIBLE (Binary Only)** |
| **Standard 3-Way NLI** (Entailment, Neutral, Contradiction) | Blocked by conflation of Neutral and Contradiction. | **NOT FEASIBLE** |
| **Full Five-Outcome G3 Verifier** | Blocked by total absence of 3 out of 5 classes. | **NOT FEASIBLE (BLOCKED)** |

**Definitive Auditor Statement:**  
Claims that TrustRAG is ready to train a full G3 five-outcome verifier on `sft_v1` are **factually incorrect and rejected**.

