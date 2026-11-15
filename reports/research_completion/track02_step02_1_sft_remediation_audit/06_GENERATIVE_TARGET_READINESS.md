# TrustRAG Track 2, Step 2.2.1: Generative Target Readiness Audit Report

## 1. Audit Scope & Verification Mandate

This report independently evaluates the capabilities that can legitimately be trained using the generative targets in `data/processed/sft_v2/`.

The audit specifically examines whether the datasets contain **structured reasoning supervision** or merely **binary classification labels serialized as JSON**.

---

## 2. Assessment of Five Generative Capabilities

| Generative Capability | Target Supervision in `sft_v2` | Training Authorized? | Auditor Assessment & Deficit Analysis |
| :--- | :---: | :---: | :--- |
| **1. Direct Binary JSON Generation** | **YES** | **YES** | The schema provides valid JSON serialization (`binary_label: "FACTUAL" \| "HALLUCINATED"`). Models can learn to output structured JSON verdicts directly. |
| **2. Atomic Claim Decomposition** | **NO** | **NO (BLOCKED)** | The dataset does **not** contain ground truth proposition tuples $\langle s, r, o \rangle$ or segmented claim lists. Attempting to train claim extraction will fail due to lack of target supervision. |
| **3. Evidence Citation Generation** | **NO** | **NO (BLOCKED)** | Passages are not segmented into numbered citation anchors (e.g. `[1]`, `[2]`), and targets do not include citation markers. |
| **4. Five-Outcome Verdict Generation** | **NO** | **NO (BLOCKED)** | The targets contain only binary labels. Zero supervision exists for `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`, or `UNCERTAIN`. |
| **5. Chain-of-Thought Reasoning (`<think>`)** | **NO** | **NO (BLOCKED)** | Upstream raw human datasets contain **zero** chain-of-thought traces. Fabricating pseudo-reasoning traces without teacher distillation is strictly forbidden. |

---

## 3. The Distinction: JSON Serialization vs. Structured Reasoning

> [!WARNING]
> Serializing a binary label into a JSON string (e.g. `{"binary_label": "FACTUAL"}`) does **not** constitute structured reasoning supervision.
> 
> Training an autoregressive LLM on direct JSON outputs will train the model to format its predictions as JSON, but will **not** train the model to perform verifiable multi-step deduction, atomic claim verification, or evidence citation.

---

## 4. Auditor Readiness Verdict

**Generative Structured Verification:** **`CONDITIONALLY_READY`**

- **Authorized Use:** Training models to generate direct structured JSON verdicts for binary classification (`{"binary_label": ...}`).
- **Unauthorized / Blocked:** Claiming readiness for chain-of-thought `<think>` reasoning, claim decomposition, or evidence citation generation.

