# TrustRAG — Track 2, Step 3.8: Checkpoint Integrity & Offline Verification

## 1. Generated Checkpoint Checksums

Output Directory: `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000`

| File Name | Size (Bytes) | SHA-256 Checksum | Offline Status |
| :--- | :---: | :--- | :---: |
| `config.json` | 1,096 | `38370396a4e2988a14226b6b8875766e660ab8bbd1374b9e23a6e0c7a05ef385` | **VERIFIED** |
| `model.safetensors` | 567,601,628 | `500832fa1b9b7c67c2c08d9e1f4d4c76d235d15fa9960d76e1e6e81c220a2f8a` | **VERIFIED** |
| `tokenizer_config.json` | 536 | `1121ad33ecd98a97b2db184ce896546feb7555bebddf33a2dfe1b1a1077dc847` | **VERIFIED** |
| `tokenizer.json` | 8,340,141 | `d87197028bcdd4a6c68dc03bd9b04e0956b0998daf7351345de21278a1c9249a` | **VERIFIED** |
| `training_meta.json` | 2,287 | `f2e755836bf5c74a858f6e836cb7181f378a69b0280c8e7dc416f8e8dcb0d95f` | **VERIFIED** |

---

## 2. Offline Re-Loading Verification
The saved checkpoint was independently re-loaded in offline mode (`local_files_only=True`, `HF_HUB_OFFLINE=1`):
- Architecture: `DebertaV2ForSequenceClassification`
- Output logits: 3 classes (`[1, 3]`)
- Parameter count: Exactly 141,897,219
- All weights safely serialized via Safetensors format.
