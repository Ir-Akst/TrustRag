# Track 2, Step 3.0: Objective-Specific Training Architecture & Design

**Audit Date:** November 14, 2026  
**Auditor:** ML Infrastructure Auditor  

---

## 1. Architectural Blueprint Across Objectives

We specify the exact loss formulation, model head, token formatting, and training dynamics for each objective:

```
[ Objective A: Binary Cross-Encoder ]
Inputs: [CLS] Query [SEP] Context [SEP] Candidate Response [SEP]
Head: Linear(d_model -> 1)
Loss: BCEWithLogitsLoss()

[ Objective B: 3-Way NLI Cross-Encoder ]
Inputs: [CLS] Premise (Evidence Context) [SEP] Hypothesis (Candidate Response) [SEP]
Head: Linear(d_model -> 3)
Loss: CrossEntropyLoss()

[ Objective C: Fine-Grained Span Token Classifier ]
Inputs: [CLS] Context [SEP] Candidate Response [SEP]
Head: Linear(d_model -> 3) [Tags: O, B-HALLUCINATION, I-HALLUCINATION]
Loss: Masked CrossEntropyLoss() (ignoring [CLS], Context, [SEP], and [PAD])

[ Objective D: G3 5-Outcome Classifier ]
Status: BLOCKED pending LLM teacher pseudo-label generation.

[ Objective E: Generative Structured SRM ]
Inputs: Prompt with Question + Evidence + Candidate Answer
Target: <think> Reasoning Trace </think> + JSON schema
Status: BLOCKED on host hardware (OOM) and dataset CoT trace absence.
```

---

## 2. Objective A: Binary Hallucination Classification

- **Target Task:** Predict whether a candidate response is faithful (`0`) or hallucinated (`1`) given query and context.
- **Recommended Architecture:** `microsoft/deberta-v3-small` (44M parameters) or `distilbert-base-uncased` (66M parameters).
- **Input Formatting:**
  `[CLS] Question: {q} [SEP] Context: {c} [SEP] Response: {r} [SEP]`
- **Loss Function:** Binary Cross-Entropy with Logits (`torch.nn.BCEWithLogitsLoss`).
  - Class balancing: Since training split has 13,000 positive and 13,054 negative examples (balanced 50/50), `pos_weight = 1.0`.
- **Optimization Strategy:**
  - Optimizer: AdamW (`lr=2e-5`, `weight_decay=0.01`).
  - Warmup: 10% linear warmup.
  - Precision: FP32 on CPU (or BF16 if supported via AVX-VNNI).
  - Batch Size: 16 (or batch size 8 with gradient accumulation steps = 2).
- **Expected CPU Training Duration:** ~6.5 to 9.0 hours per epoch on Intel Core i7-1355U (6 active threads). Total 3 epochs: ~22–27 hours.

---

## 3. Objective B: 3-Way Evidence-Grounded NLI

- **Target Task:** Classify premise-hypothesis relationship into `0: Entailment`, `1: Neutral`, `2: Contradiction`.
- **Recommended Architecture:** `microsoft/deberta-v3-small` or `roberta-base`.
- **Input Formatting:**
  `[CLS] Premise: {evidence} [SEP] Hypothesis: {candidate_sentence} [SEP]`
- **Loss Function:** Multi-class Cross-Entropy (`torch.nn.CrossEntropyLoss`).
  - Label weights: Inverted class frequencies to account for RAGTruth distribution:
    - Entailment: 7,858 examples ($\approx 72.7\%$)
    - Contradiction: 2,757 examples ($\approx 25.5\%$)
    - Neutral: 200 examples ($\approx 1.8\%$)
  - Balanced class weighting: $w_c = \frac{N}{K \cdot N_c}$ to penalize majority bias.
- **Optimization Strategy:**
  - Optimizer: AdamW (`lr=3e-5`, `weight_decay=0.01`).
  - Batch Size: 16 (gradient accumulation = 2).
- **Expected CPU Training Duration:** ~3.5 to 5.0 hours per epoch (10,815 examples). Total 3 epochs: ~12–15 hours.

---

## 4. Objective C: Fine-Grained Span Detection (Token Classification)

- **Target Task:** Identify character start and end offsets of hallucinated tokens in the candidate response.
- **Recommended Architecture:** `AutoModelForTokenClassification` with `deberta-v3-base` or `distilbert-base-uncased`.
- **Tagging Scheme:** BIO Scheme (3 classes: `O` = Outside, `B-HALL` = Begin Hallucination, `I-HALL` = Inside Hallucination).
- **Token Alignment Protocol:**
  - Tokenize using fast tokenizer with `return_offsets_mapping=True`.
  - Mask all tokens belonging to Context or Question with label `-100` so loss is strictly computed over Candidate Response tokens.
  - Map character spans $[s_i, e_i)$ to token indices where token interval overlaps span.
- **Loss Function:** Masked Cross-Entropy (`ignore_index=-100`).
- **Sliding Window:** Stride = 128 tokens for candidate responses exceeding 512 tokens.
- **Expected CPU Training Duration:** ~4.0 to 6.0 hours per epoch (12,072 examples). Total 3 epochs: ~14–18 hours.

---

## 5. Objectives D & E: Blocked Objectives Analysis

| Parameter | Objective D (G3 5-Outcome) | Objective E (Generative Structured SRM) |
| :--- | :--- | :--- |
| **Supervision Availability** | ❌ **0 records** (Supervision Gap) | ❌ **0 reasoning traces** (Only ground truth text) |
| **Base Model Required** | Cross-Encoder or Causal LM | Causal LM (Qwen2.5-1.5B or 7B) |
| **Minimum VRAM / RAM Required**| 2 GB (Encoder) / 16 GB (Causal) | 16 GB to 32 GB VRAM |
| **Host Feasibility** | Architecture feasible; Data absent | **Physically Infeasible on Host CPU/RAM** |
| **Prerequisite Resolution Path** | Distill 5-class labels from teacher LLM | Offline cloud GPU training (A10G / A100) |
