# TrustRAG — Phase 11.1, Step 2.1: Probability Calibration & Prediction Provenance

## 1. Probability Calibration Metrics (Step 0 Baseline)

Calibration metrics quantify the degree to which predicted confidence values reflect true empirical accuracy.

### 1.1 Brier Score
The multi-class Brier score measures the mean squared deviation between predicted probability distributions and one-hot ground truth vectors:
$$\text{BS} = \frac{1}{N} \sum_{i=1}^N \sum_{k=1}^K (p_{ik} - y_{ik})^2$$
- **Step 0 Baseline Brier Score:** **0.662933**
- **Evaluation:** High calibration error, characteristic of an untrained classification head where predicted probabilities do not align with true class probabilities.

### 1.2 Expected Calibration Error (ECE-10)
ECE partitions the predicted confidence interval $[0, 1]$ into 10 equally spaced bins and computes the weighted absolute difference between bin accuracy and bin confidence:
$$\text{ECE} = \sum_{m=1}^{10} \frac{|B_m|}{N} |\text{acc}(B_m) - \text{conf}(B_m)|$$
- **Step 0 Baseline ECE-10:** **0.151797** (15.18%)
- **Pre-Registered Target:** $\le 0.1000$ (10.00%)
- **Evaluation:** Unmet on baseline; post-training ECE could not be evaluated due to mid-epoch abortion.

---

## 2. Validation Prediction Provenance & Storage

The training runner was enhanced to serialize sample-level inferences to `predictions_val.jsonl` containing:
- `sample_id`: Unique example identifier from dataset.
- `true_label`: Ground truth text label (`ENTAILMENT`, `CONTRADICTION`, `NEUTRAL`).
- `true_label_idx`: Integer label ID (0, 1, 2).
- `predicted_label`: Model prediction label.
- `predicted_label_idx`: Model prediction integer ID.
- `logits`: Raw unnormalized logit triplet $[z_0, z_1, z_2]$.
- `probabilities`: Softmax normalized probability distribution $[\sigma_0, \sigma_1, \sigma_2]$.
- `is_correct`: Boolean classification flag.

Because execution was interrupted at Step 325 prior to final model validation, no final prediction artifact was generated for a completed model.

