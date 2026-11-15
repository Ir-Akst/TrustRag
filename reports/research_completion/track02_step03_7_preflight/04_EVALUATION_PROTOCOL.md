# TrustRAG — Track 2, Step 3.7: Validation & Evaluation Protocol

## 1. Validation Dataset Policy

In accordance with strict auditor standards:
- **Validation Dataset:** The **ORIGINAL IMBALANCED VALIDATION SPLIT** (`data/processed/sft_v2/nli/validation.jsonl`, N=2,662) will be used for both Step 0 baseline evaluation and Step 1,000 final post-training evaluation.
- **Non-Distortion:** The balanced training sampler is strictly forbidden from being applied to the validation set.

---

## 2. Mandatory Metric Suite

1. **Overall Performance:**
   - Classification Accuracy
   - Balanced Accuracy (Macro Average of Class Recalls)
   - Macro F1 Score
   - Weighted F1 Score
   - Cross-Entropy Validation Loss
2. **Per-Class Metrics (ENTAILMENT, CONTRADICTION, NEUTRAL):**
   - Precision
   - Recall
   - F1 Score
   - Support
3. **Confusion Analysis:**
   - Complete 3×3 Confusion Matrix `cm[true_idx][pred_idx]`
   - **False Entailment Analysis:** True CONTRADICTION or NEUTRAL incorrectly classified as ENTAILMENT (Type I acceptance of ungrounded text).
   - **False Contradiction Analysis:** True ENTAILMENT or NEUTRAL incorrectly classified as CONTRADICTION (Type I false alarm).
   - **Neutral-vs-Contradiction Confusion:** Mutual confusion between unsupported additions and direct factual conflicts.
4. **Calibration & Reliability:**
   - Multi-class Brier Score: $\frac{1}{N} \sum_{i=1}^N \sum_{c=1}^3 (p_{ic} - y_{ic})^2$
   - Expected Calibration Error (ECE, 10 equal bins)

---

## 3. Comparison Baselines (Imbalanced Validation N=2,662)

| Baseline Model | Accuracy | Balanced Acc | Macro F1 | Weighted F1 | Note |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Majority Class (Always Entailment)** | **62.43%** | 33.33% | 0.2562 | 0.4800 | Predicts label 0 for all instances |
| **Uniform Random Guessing (1/3)** | 33.33% | 33.33% | 0.3333 | 0.3333 | Equal chance across classes |
| **Stratified Class Prior Guessing** | 46.62% | 33.33% | 0.3333 | 0.4662 | Samples from validation prior |
