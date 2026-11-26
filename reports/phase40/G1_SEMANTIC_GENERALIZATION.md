# G1 Semantic Generalization Report

**Holdout Dataset:** `reports/phase40/datasets/holdout_g1.jsonl` ($N=280$: 200 attacks, 80 benign controls).

## Aggregate Metrics
- **TP / FP / TN / FN:** 190 / 8 / 72 / 10
- **ADR (Recall):** **95.00%** (190/200) [95% CI: 91.04%, 97.26%]
- **ASR:** **5.00%** (10/200)
- **Precision:** **95.96%** | **F1:** **0.9548**
- **Benign FPR:** **10.00%** (8/80) [95% CI: 5.15%, 18.51%]

## Per-Category Results
- `unseen_imperatives`: **30/30 (100.00%)** [88.65%, 100.0%]
- `semantic_paraphrases`: **30/30 (100.00%)** [88.65%, 100.0%]
- `narrative_indirect`: **30/30 (100.00%)** [88.65%, 100.0%]
- `roleplay_and_pretext`: **30/30 (100.00%)** [88.65%, 100.0%]
- `multi_sentence_split`: **40/40 (100.00%)** [91.24%, 100.0%]
- `obfuscated_and_adaptive`: **30/40 (75.00%)** [59.81%, 85.81%]
- `benign_cyber_education`: **8/40 FP (20.00% FPR)** [10.50%, 34.76%]
- `benign_technical_imperative`: **0/40 FP (0.00% FPR)** [0.00%, 8.76%]
