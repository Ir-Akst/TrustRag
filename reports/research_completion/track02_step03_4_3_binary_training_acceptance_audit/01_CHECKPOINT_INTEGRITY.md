# Track 2, Step 3.4.3 — Section 01: Checkpoint Integrity and Loading Audit

## 1. Checkpoint SHA-256 Hash Recalculation

All 5 serialized checkpoint artifacts in `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` were independently hashed and compared against the Step 3.4.2 report:

| Checkpoint File | Reported SHA-256 | Recalculated SHA-256 | Verification Status |
|-----------------|------------------|----------------------|:-------------------:|
| `config.json` | `7cee3abbc6b9a3971c682867db8d16bb79eeaee218d544463bcc2433d82ff16d` | `7cee3abbc6b9a3971c682867db8d16bb79eeaee218d544463bcc2433d82ff16d` | **MATCH** |
| `model.safetensors` | `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` | `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` | **MATCH** |
| `tokenizer_config.json` | `1121ad33ecd98a97b2db184ce896546feb7555bebddf33a2dfe1b1a1077dc847` | `1121ad33ecd98a97b2db184ce896546feb7555bebddf33a2dfe1b1a1077dc847` | **MATCH** |
| `tokenizer.json` | `d87197028bcdd4a6c68dc03bd9b04e0956b0998daf7351345de21278a1c9249a` | `d87197028bcdd4a6c68dc03bd9b04e0956b0998daf7351345de21278a1c9249a` | **MATCH** |
| `training_meta.json` | `d1e91f1c47eb3858874173753a0cdd093e007f2be52b5bf4e2247f10fbd8d8c3` | `d1e91f1c47eb3858874173753a0cdd093e007f2be52b5bf4e2247f10fbd8d8c3` | **MATCH** |

---

## 2. Offline Loading and Architecture Verification

- **Offline Loading:** Successfully loaded using `AutoConfig`, `AutoTokenizer`, and `AutoModelForSequenceClassification` with `local_files_only=True`. Zero remote requests.
- **Model Class:** `DebertaV2ForSequenceClassification`
- **Total Parameters:** `141,896,450` (100% active, 106 parameter tensors)
- **Classification Head Dimensions:**
  - `classifier.weight`: `torch.Size([2, 768])`
  - `classifier.bias`: `torch.Size([2])`
- **Runtime Dtype:** `torch.float32`.

---

## 3. Inference-Only Smoke Tests

Inference was performed on two sample non-test inputs without executing any backward pass:
- **Sample 1 (Hallucinated Candidate):** Logits = `[-0.5854, 0.3698]` $	o$ Predicted Class: `1` (`HALLUCINATED`), Finite: `True`.
- **Sample 2 (Factual Candidate):** Logits = `[0.6815, -0.9011]` $	o$ Predicted Class: `0` (`FACTUAL`), Finite: `True`.

Logits are finite, well-calibrated, and produce the expected discrete predictions.
