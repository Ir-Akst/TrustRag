# TrustRAG — Track 2, Step 3.14: Original NLI Supervision Audit

### 1. Dataset Breakdown & Provenance

The NLI dataset in `data/processed/sft_v2/nli/` was derived strictly from RAGTruth human annotations (`data/processed/ragtruth/train.jsonl`):

| Split | Records | ENTAILMENT | NEUTRAL | CONTRADICTION | Unique Documents |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Train (`train.jsonl`)** | 10,815 | 6,707 (62.02%) | 2,688 (24.85%) | 1,420 (13.13%) | 2,011 |
| **Validation (`validation.jsonl`)** | 2,662 | 1,662 (62.43%) | 644 (24.19%) | 356 (13.37%) | 503 |
| **Total** | 13,477 | 8,369 (62.10%) | 3,332 (24.72%) | 1,776 (13.18%) | 2,514 |

- **Exclusions:** 1,613 mixed records (`RAGTRUTH_MIXED_CONFLICT_AND_BASELESS_INFO`) containing both contradiction and unmentioned info were quarantined. HaluEval was 100% quarantined.
- **Split Isolation:** 0 document overlap, 0 example ID overlap between train and validation.

---

### 2. Evidence Localization Reality: Hypothesis vs Premise

The audit conducted an exhaustive inspection of the underlying RAGTruth ground truth:
1. **Hypothesis Spans:** Annotations (`start`, `end`, `text`, `label_type`) reside **strictly within the hypothesis text**.
   - Example `ragtruth_2`: Claim length = 970 chars; conflict span `[636:653]` = `"February 7, 2022."`.
2. **Premise Spans: ZERO.**
   - In RAGTruth, the premise is the full source document (`document` field, avg ~587 tokens, up to 3,000+ tokens).
   - Human annotators entered free-form notes in `meta` (e.g. `"Original: February 7 (1945)"`), but **no character offsets, token boundaries, or sentence indices were annotated on the source document**.
3. **Implication for NLI:**
   - At the *example level* (`premise` + `hypothesis`), the 3-way label is mathematically sound.
   - At the *chunk level*, premise evidence is unlocalized.
