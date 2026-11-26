# G3 Factual Recall & Abstention Root-Cause Analysis

## 1. HaluEval Diagnosis (`data/processed/halueval/test.jsonl`, $N=200$, `seed=42`)
- **Short-Claim Filtering:** **70/200** claims had `< 3 words` and were dropped by `extract_atomic_claims`.
- **Raw Answer Eval:** Coverage **17.00%**, Abstention **83.00%**, Factual Recall **10.00%** ($10/100$, [5.52%, 17.44%]), Precision **29.41%**, Hallucination Leakage **24.00%** ($24/100$, [16.69%, 33.23%]), TP/FP/TN/FN = 10/24/76/90.
- **Full-Sentence QA Wrapper Eval (`"The answer to '<q>' is <a>."`):** Coverage **47.00%**, Abstention **53.00%**, Factual Recall **52.00%** ($52/100$, [42.32%, 61.54%]), Precision **55.32%**, Hallucination Leakage **42.00%** ($42/100$, [32.80%, 51.79%]), TP/FP/TN/FN = 52/42/58/48.

## 2. RAGTruth Stratified Diagnosis (`data/processed/ragtruth/test.jsonl`, `seed=42`)
- **Dataset Accounting:** 2,700 total test records; **1,800 records** (`QA` and `Data2txt`) were excluded because their `document` field is a structured `dict` rather than prose.
- **RAGTruth `Summary` ($N=50$: 25 FACTUAL, 25 HALLUCINATED):**
  - Coverage: **12.00%** | Abstention: **88.00%** | Factual Precision: **66.67%**
  - Factual Recall: **16.00%** ($4/25$, [6.40%, 34.65%]) | Hallucination Leakage: **8.00%** ($2/25$, [2.22%, 24.97%])
  - **Root Causes of 21/25 FACTUAL Summary Abstentions:** `entity_sub` fired **29 times**, `neural_con >= 0.20` fired **20 times**, `num_conflict` fired **5 times** when abstractive summary sentences synthesized entities from multiple document sentences.

## 3. Seven-Regime Controlled G3 Breakdown
- `short_factual_sentence` ($N=20$): **100.00%** [83.89%, 100.0%]
- `multi_sentence_supported` ($N=20$): **100.00%** [83.89%, 100.0%]
- `supported` ($N=30$): **100.00%** [88.65%, 100.0%]
- `partially_supported` ($N=20$): **100.00%** [83.89%, 100.0%]
- `unsupported` ($N=25$): **100.00%** [86.68%, 100.0%]
- `geo_contradiction` ($N=12$), `entity_contradiction` ($N=11$), `numerical_contradiction` ($N=11$), `implicit_contradiction` ($N=11$): **100.00%** across all 4 contradiction classes.
