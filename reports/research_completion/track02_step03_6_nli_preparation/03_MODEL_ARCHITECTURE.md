# TrustRAG — Track 2, Step 3.6: NLI Model Architecture Specification

## 1. Architectural Configuration

- **Base Backbone:** `microsoft/deberta-v3-small` (disentangled attention, 6 hidden layers, 12 attention heads, hidden dimension 768).
- **Model Class:** `DebertaV2ForSequenceClassification`
- **Output Head:** Linear projection from pooled hidden state (768) to 3 logits:
  * `classifier.weight`: `torch.Size([3, 768])`
  * `classifier.bias`: `torch.Size([3])`
- **Total Parameters:** **141,897,219** (141.9M)
- **Trainable Parameters:** 141,897,219 (Backbone + Classification Head)
- **Numerical Precision:** FP32 (`torch.float32`) across all layers and embeddings.
- **Label Mapping:**
  ```json
  {
    "id2label": {"0": "ENTAILMENT", "1": "CONTRADICTION", "2": "NEUTRAL"},
    "label2id": {"ENTAILMENT": 0, "CONTRADICTION": 1, "NEUTRAL": 2}
  }
  ```

---

## 2. Checkpoint Separation & Protection

| Checkpoint Identifier | Location | Architecture | Protection Status |
| :--- | :--- | :---: | :---: |
| Pretrained Base Snapshot | `/home/aditya/rags/models/pretrained/deberta-v3-small` | Pretrained Masked LM | **READ_ONLY_LOCKED** |
| Accepted Binary Classifier | `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` | 2-class Head | **IMMUTABLE_PRESERVED** |
| Target NLI Checkpoint | `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot` (Future) | 3-class Head | **PENDING_AUTHORIZATION** |

The training runner enforces strict path guards: any attempt to write to or overwrite the pretrained directory or the accepted binary checkpoint raises a `SecurityViolationError`.
