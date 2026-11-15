# TrustRAG — Track 2, Step 1: Independent Neural Training Readiness Audit
# 03 — Supervised Fine-Tuning (SFT) Data Readiness Audit

**Audit Objective:** Determine whether valid, well-formed Supervised Fine-Tuning (SFT) training examples can actually be constructed from existing repository datasets to train an evidence-grounded Small Reasoning Model (SRM).

---

## 1. Candidate SFT Training Pools

| Source Dataset | Available Train Records | Factual Records | Hallucinated Records | Input Document Available? | Claim / Answer Available? | Target Reasoning Chain Available? | SFT Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **RAGTruth Train** | 15,090 | 8,369 (55.5%) | 6,721 (44.5%) | YES (Source Text) | YES (Generated Claim) | **NO (Only span offsets)** | **RAW ONLY** |
| **HaluEval Train** | 14,000 | 7,000 (50.0%) | 7,000 (50.0%) | YES (Context Passage)| YES (Answer String) | **NO (Binary label only)** | **RAW ONLY** |
| **Total Usable Raw**| **29,090** | **15,369 (52.8%)**| **13,721 (47.2%)**| **YES** | **YES** | **NO** | **BLOCKED FOR SRM SFT** |

---

## 2. Training Target Format Gap: Classification vs Reasoning SFT

### 2.1 The Two Potential SFT Paradigms

1. **Paradigm A: Simple Discriminative / Sequence Classification SFT (e.g. DeBERTa-v3 NLI)**
   - **Input:** `[CLS] Premise: <document> [SEP] Hypothesis: <claim> [SEP]`
   - **Target:** Class index $y \in \{0: \text{CONTRADICTED}, 1: \text{SUPPORTED}\}$.
   - **Data Feasibility:** **100% READY**. Both RAGTruth and HaluEval have complete premise, hypothesis, and binary ground-truth labels for all 29,090 records.

2. **Paradigm B: Autoregressive Generative SRM Reasoning SFT (HalluGuard Specification)**
   - **Prompt:**
     ```
     You are a rigorous evidence-grounded verifier. Cross-examine the following claim against the document.
     Document: {document}
     Claim: {claim}
     Output step-by-step reasoning within <think>...</think>, followed by a JSON decision.
     ```
   - **Required Target:**
     ```
     <think>
     The claim asserts that X occurred on date Y. Looking at paragraph 2 of the document, the text explicitly states "Z occurred on date Y". Therefore, X is unsupported and conflicts directly with the text.
     </think>
     {
       "verdict": "CONTRADICTED",
       "hallucination_type": "EVIDENT_CONFLICT",
       "cited_spans": ["Z occurred on date Y"],
       "confidence": 0.95
     }
     ```
   - **Data Feasibility:** **BLOCKED**. Neither RAGTruth nor HaluEval contains pre-generated `<think>` natural language reasoning rationales. While RAGTruth provides character offsets for hallucinated spans, translating those into coherent, fluent reasoning justifications requires an intermediate data-synthesis pipeline (distillation via an offline teacher LLM).

---

## 3. Exclusion Analysis & Preprocessing Deficits

1. **Zero Exclusion on Raw Data:**
   - 0 records in RAGTruth train have null or missing documents/claims.
   - 0 records in HaluEval train have null or missing context/answers.
   - All 29,090 raw records are syntactically valid JSON objects.
2. **Missing Tokenizer Collators:**
   - The repository contains no PyTorch `Dataset` or `DataCollatorForSeq2Seq` classes to tokenize documents and claims with proper max sequence lengths (e.g., 2048 or 4096 tokens).
   - Long documents in RAGTruth (which often exceed 1,500 words) will be naively truncated without attention to where the claim or hallucination span appears unless a dedicated truncation collator is built.
3. **Empty Validation Split on RAGTruth:**
   - As established in Report 02, `data/processed/ragtruth/validation.jsonl` is 0 bytes.
   - Without an intermediate validation split, SFT cannot monitor cross-entropy loss against validation perplexity or implement early stopping to prevent overfitting.

---

## 4. SFT Data Readiness Conclusion

- If the objective is **Sequence Classification (Cross-Encoder / NLI)**: The data is **READY** (29,090 examples available).
- If the objective is **Generative Small Reasoning Model (HalluGuard SRM)**: The data is **BLOCKED** because target reasoning traces (`<think>` chains) have not been synthesized or formatted.
- In either case, training cannot proceed until an SFT data formatting and splitting pipeline is implemented.

