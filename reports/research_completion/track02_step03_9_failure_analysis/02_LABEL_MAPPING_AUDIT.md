# TrustRAG — Track 2, Step 3.9: Label Mapping & Pipeline Integrity Audit

## 1. Specification vs. Implementation Audit

The intended label schema specified by Track 2:
- `ENTAILMENT` = 0
- `CONTRADICTION` = 1
- `NEUTRAL` = 2

Forensic code audit was performed across all six stages of the pipeline:

### Stage 1: Raw JSONL Records
- Inspected `data/processed/sft_v2/nli/train.jsonl` and `validation.jsonl`.
- String labels present: `"ENTAILMENT"`, `"CONTRADICTION"`, `"NEUTRAL"`.
- Verified 0 invalid labels across all 13,477 records.

### Stage 2: In-Memory Mapping Dictionary
- Defined in `train_nli_classifier.py`:
  ```python
  NLI_LABEL_MAP = {
      "ENTAILMENT": 0,
      "CONTRADICTION": 1,
      "NEUTRAL": 2,
  }
  ID_TO_NLI_LABEL = {v: k for k, v in NLI_LABEL_MAP.items()}
  ```
- Integrity: `ID_TO_NLI_LABEL[0] == "ENTAILMENT"`, `ID_TO_NLI_LABEL[1] == "CONTRADICTION"`, `ID_TO_NLI_LABEL[2] == "NEUTRAL"`.

### Stage 3: DeBERTa Config Serialization
- Verified `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000/config.json`:
  ```json
  "id2label": {
    "0": "ENTAILMENT",
    "1": "CONTRADICTION",
    "2": "NEUTRAL"
  },
  "label2id": {
    "CONTRADICTION": 1,
    "ENTAILMENT": 0,
    "NEUTRAL": 2
  },
  "num_labels": 3
  ```

### Stage 4: Tensor Conversion & Loss Computation
- In training loop:
  ```python
  target_label = NLI_LABEL_MAP[rec["nli_label"]]
  labels = torch.tensor([target_label], dtype=torch.long)
  outputs = model(input_ids=..., attention_mask=..., labels=labels)
  loss = outputs.loss
  ```
- PyTorch HuggingFace `DebertaV2ForSequenceClassification` executes:
  `loss_fct = CrossEntropyLoss()`
  `loss = loss_fct(logits.view(-1, 3), labels.view(-1))`
- Target index directly corresponds to class logit dimension.

### Stage 5: Evaluation Argmax Decoding
- In validation loop:
  ```python
  y = NLI_LABEL_MAP[rec["nli_label"]]
  pred_cls = int(torch.argmax(out.logits[0], dim=-1).item())
  preds.append(pred_cls)
  targets.append(y)
  ```

### Stage 6: Metric Aggregation
- In `compute_nli_metrics()`:
  `cm[yt][yp] += 1` correctly maps index 0 to ENTAILMENT, index 1 to CONTRADICTION, index 2 to NEUTRAL.

---

## 2. Conclusion on Label Mapping

**Finding:** The label mapping is 100% mathematically and structurally consistent. There is **NO label inversion, NO off-by-one error, and NO silent permutation** in the code or checkpoints.
