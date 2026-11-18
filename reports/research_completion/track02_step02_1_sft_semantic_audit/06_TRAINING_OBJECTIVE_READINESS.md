# TrustRAG Track 2, Step 2.1: Training Objective Readiness Report

## 1. Executive Summary

This report establishes definitive readiness verdicts for five distinct training objectives that could be attempted using `data/processed/sft_v1/`.

A passing JSONL schema test confirms syntactic correctness, but does not constitute proof of semantic supervision suitability. Each training objective is evaluated on the validity of its underlying supervision signals.

---

## 2. Objective-by-Objective Readiness Audit

### Objective 1: Binary Hallucination Classification
- **Task Formulation:** Predict whether a candidate response is faithful to the context:
  $$f(x_{\text{query}}, x_{\text{context}}, x_{\text{candidate}}) \rightarrow y \in \{\text{FACTUAL}, \text{HALLUCINATED}\}$$
- **Available Supervision:**
  - Train: 26,072 examples (13,660 FACTUAL, 12,412 HALLUCINATED).
  - Validation: 6,018 examples (3,209 FACTUAL, 2,809 HALLUCINATED).
  - Derived from authoritative human span annotations (RAGTruth) and verified QA benchmarks (HaluEval).
- **Missing Labels:** None.
- **Required Additional Annotations:** None.
- **Usable Without Modification?** **YES.**
- **Readiness Verdict:** **`VERIFIED`**

---

### Objective 2: Evidence-Grounded Natural Language Inference (NLI)
- **Task Formulation:** 3-way inference classification:
  $$f(x_{\text{premise}}, x_{\text{hypothesis}}) \rightarrow y \in \{\text{ENTAILMENT}, \text{NEUTRAL}, \text{CONTRADICTION}\}$$
- **Available Supervision:**
  - Entailment (`SUPPORTED`): 16,869 examples.
  - Genuine Contradiction: 1,776 RAGTruth pure conflict examples + ~1,200 HaluEval entity swaps.
- **Missing Labels:**
  - `NEUTRAL / UNSUPPORTED` is currently mislabeled as `CONTRADICTED` in 3,332 RAGTruth records (Pure Baseless Info) and ~8,800 HaluEval QA records (Unmentioned entities).
- **Required Additional Annotations:**
  - Relabel RAGTruth `Evident Baseless Info` records from `CONTRADICTED` to `NEUTRAL` (or `INSUFFICIENT_EVIDENCE`).
  - Filter or re-annotate HaluEval unmentioned cases.
- **Usable Without Modification?** **NO.** Using `sft_v1` as-is forces models to treat missing evidence as contradiction.
- **Readiness Verdict:** **`CONDITIONALLY_VERIFIED (BLOCKED AS-IS)`**

---

### Objective 3: Span-Level Hallucination Detection
- **Task Formulation:** Token-level sequence labeling or span extraction:
  $$f(x_{\text{context}}, x_{\text{candidate}}) \rightarrow \{(s_i, e_i, \text{conflict\_type})\}$$
- **Available Supervision:**
  - RAGTruth contains **14,289 human annotated character spans** with start/end offsets and conflict descriptions.
- **Missing Labels:**
  - HaluEval QA (17,000 records across train/val) contains **0 span annotations**. In `sft_v1`, all HaluEval hallucinated records have `"hallucination_spans": []`.
- **Required Additional Annotations:**
  - Token-level cross-entropy loss must be masked out for all HaluEval records, OR the span detection objective must be restricted exclusively to the RAGTruth subset.
- **Usable Without Modification?** **NO.** Training naively across the entire `sft_v1` file will penalize the model for predicting spans on 17,000 HaluEval hallucinated examples where spans are empty.
- **Readiness Verdict:** **`CONDITIONALLY_VERIFIED (RAGTruth Subset Only)`**

---

### Objective 4: Full Five-Outcome G3 Verification
- **Task Formulation:** TrustRAG G3 Output Guardrail decision classification:
  $$y \in \{\text{SUPPORTED}, \text{CONTRADICTED}, \text{PARTIALLY\_SUPPORTED}, \text{INSUFFICIENT\_EVIDENCE}, \text{UNCERTAIN}\}$$
- **Available Supervision:**
  - `SUPPORTED`: 16,869 records.
  - `CONTRADICTED`: 15,221 records (including mislabeled baseless info).
- **Missing Labels:**
  - `PARTIALLY_SUPPORTED`: **0 records (0.00%)**.
  - `INSUFFICIENT_EVIDENCE`: **0 records (0.00%)**.
  - `UNCERTAIN`: **0 records (0.00%)**.
- **Required Additional Annotations:**
  - Re-map RAGTruth baseless info to `INSUFFICIENT_EVIDENCE`.
  - Introduce decomposed multi-clause examples with partial grounding to supervise `PARTIALLY_SUPPORTED`.
  - Introduce ambiguous/subtle examples to supervise `UNCERTAIN`.
- **Usable Without Modification?** **NO.** Training a 5-class head on a dataset missing 3 classes will cause model collapse.
- **Readiness Verdict:** **`NOT_VERIFIED (BLOCKED)`**

---

### Objective 5: Generative Structured Verification
- **Task Formulation:** Autoregressive generation of structured verification targets:
  $$x \rightarrow \text{JSON}(\text{verdict}, \text{spans}, \text{metadata})$$
- **Available Supervision:**
  - All 32,090 records contain valid serialized JSON strings with deterministic keys.
- **Missing Labels:**
  - Intermediate reasoning traces (e.g. `<think>` chains of thought) are completely absent.
- **Required Additional Annotations:**
  - If reasoning traces are mandated (DeepSeek-R1 / Qwen-CoT style), a teacher distillation pipeline with frozen verifiers must be authorized and executed.
- **Usable Without Modification?**
  - **YES** for direct structured JSON generation without `<think>` reasoning traces.
  - **NO** for chain-of-thought reasoning models.
- **Readiness Verdict:** **`CONDITIONALLY_VERIFIED`**

---

## 3. Summary Readiness Matrix

| Objective | Readiness Verdict | Safe for Model Training Now? | Key Restriction / Action Required |
| :--- | :---: | :---: | :--- |
| **1. Binary Hallucination Classification** | **`VERIFIED`** | **YES** | Ready for training binary baseline models. |
| **2. Evidence-Grounded NLI** | **`CONDITIONALLY_VERIFIED`** | **NO** | Must relabel baseless info to Neutral before training. |
| **3. Span-Level Detection** | **`CONDITIONALLY_VERIFIED`** | **CONDITIONAL** | Restrict training loss to `source_dataset == 'ragtruth'`. |
| **4. Full 5-Outcome G3** | **`NOT_VERIFIED`** | **NO** | Missing 3 of 5 classes; must not be attempted on `sft_v1`. |
| **5. Generative Structured** | **`CONDITIONALLY_VERIFIED`** | **CONDITIONAL** | Safe for direct JSON; blocked for `<think>` reasoning traces. |

