# TrustRAG — Phase 11.1, Step 2.1: Training Harness Remediation & Architectural Enhancements

## 1. Blocker Diagnosis & Failure Mode in Step 2

In Phase 11.1 Step 2, preflight execution was aborted before any training steps were taken due to two critical harness defects:

### 1.1 Sampler Quota Exhaustion Crash
The previous implementation of `load_nli_dataset()` hardcoded `strategy="stratified_class_balanced"`, which partitioned the target sample budget into three equal quotas:
$$\text{quota per class} = \left\lfloor \frac{10,815}{3} \right\rfloor = 3,605$$
However, inspection of the actual training split (`data/processed/sft_v2/nli/train.jsonl`) revealed an empirical class distribution of:
- **Entailment:** 6,707 samples (62.0%)
- **Neutral:** 2,688 samples (24.9%)
- **Contradiction:** 1,420 samples (13.1%)

Because only 1,420 Contradiction instances existed in the dataset, the sampler entered a persistent starvation loop and raised `RuntimeError: Starvation threshold exceeded for label CONTRADICTION`.

### 1.2 Double-Compensation Hazard
Furthermore, combining artificial 1:1:1 balanced sampling with loss weights of $[1.0, 3.5, 1.5]$ created a compound penalization distortion:
$$\text{Effective Penalty} = \frac{10,815 / 3}{1,420} \times 3.5 = 2.539 \times 3.5 \approx \mathbf{8.89\times}$$
This massive distortion would have driven the model into pathological hyper-sensitivity, degrading precision and skewing posterior probability calibration.

---

## 2. Engineering Remediation Applied to `train_nli_classifier.py`

File modified: [`tools/training/train_nli_classifier.py`](file:///home/aditya/rags/TrustRag-phase11/tools/training/train_nli_classifier.py)

### 2.1 Configuration & CLI Exposure
`NLITrainingConfig` and `parse_args()` were updated to expose all core hyperparameters dynamically:
- `--sampler-strategy`: choices `["stratified_class_balanced", "sequential"]` (default: `stratified_class_balanced`).
- `--epochs`: integer epoch count (default: 1).
- `--gradient-accumulation-steps`: integer accumulation window (default: 1).
- `--class-weights`: 3-float tuple `[w_entailment, w_contradiction, w_neutral]`.
- `--save-predictions`: boolean flag to persist sample-level validation inferences.

### 2.2 Sequential Natural Distribution Sampling
When `strategy="sequential"` is selected, `load_nli_dataset()` streams records in their natural corpus distribution without imposing artificial class quotas:
```python
if strategy == "sequential":
    records = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            validate_nli_record(rec)
            records.append(rec)
            if max_samples and len(records) >= max_samples:
                break
    return records
```
This enables full consumption of all 10,815 natural training examples while allowing the loss function's explicit weights to regulate minority class sensitivity without distortion.

### 2.3 Class-Weighted Cross-Entropy Loss
The loss function was parameterized with explicit class weighting aligned to label index IDs:
- Index 0: `ENTAILMENT` $\rightarrow 1.0$
- Index 1: `CONTRADICTION` $\rightarrow 3.5$
- Index 2: `NEUTRAL` $\rightarrow 1.5$

```python
if config.class_weights is not None:
    weights_tensor = torch.tensor(config.class_weights, dtype=torch.float, device="cpu")
    loss_fct = torch.nn.CrossEntropyLoss(weight=weights_tensor)
```

### 2.4 Gradient Accumulation & Step Arithmetic
To maintain numerical stability on CPU without excessive memory overhead, batch size was set to 1 with gradient accumulation across 4 steps:
- Total forward-backward passes per epoch: $10,815$
- Optimizer steps per epoch: $\lceil 10,815 / 4 \rceil = 2,704$ steps (2,703 batches of 4 + 1 trailing batch of 3)
- Total optimizer steps over 3 epochs: $2,704 \times 3 = \mathbf{8,112\text{ steps}}$

```python
loss = raw_loss / config.gradient_accumulation_steps
loss.backward()
accum_count += 1
if accum_count == config.gradient_accumulation_steps or is_last_sample_of_epoch:
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=config.max_grad_norm)
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    opt_step += 1
    accum_count = 0
```

### 2.5 Best Model Tracking and Prediction Serialization
The training harness was restructured with an outer epoch loop, tracking validation Macro F1 at each epoch boundary and serializing full inference records:
- Fields: `sample_id`, `true_label`, `true_label_idx`, `predicted_label`, `predicted_label_idx`, `logits`, `probabilities`, `is_correct`.

---

## 3. Verification & Regression Testing

Prior to execution, the test suite was executed against the modified codebase:
- **Test Command:**
  ```bash
  cd /home/aditya/rags/TrustRag-phase11 && PYTHONPATH=. /home/aditya/rags/.venv/bin/pytest tests/unit/test_track02_step03_6_nli_training_runner.py tests/unit/test_track02_step03_14_supervision_readiness.py
  ```
- **Result:**
  ```
  tests/unit/test_track02_step03_6_nli_training_runner.py ................ ....s........................ [ 80%]
  tests/unit/test_track02_step03_14_supervision_readiness.py ........... [100%]
  ======================== 55 passed, 1 skipped in 0.07s =========================
  ```
- **Outcome:** 55 passed, 1 skipped, 0 regressions. All safety guards and serialization logic verified.

