# Track 2, Step 3.4.2 — Section 05: Checkpoint Integrity and Artifact Verification

## 1. Checkpoint Serialization Verification

The trained model checkpoint was atomically staged and saved to:
`/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`

### Serialized File Inventory & SHA-256 Hashes:

| File Name | File Size | SHA-256 Checksum |
|-----------|:---------:|:----------------:|
| `config.json` | 924 bytes | `7cee3abbc6b9a3971c682867db8d16bb79eeaee218d544463bcc2433d82ff16d` |
| `model.safetensors` | 567,598,552 bytes (~567.6 MB) | `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` |
| `tokenizer_config.json` | 536 bytes | `1121ad33ecd98a97b2db184ce896546feb7555bebddf33a2dfe1b1a1077dc847` |
| `tokenizer.json` | 8,340,141 bytes (~8.34 MB) | `d87197028bcdd4a6c68dc03bd9b04e0956b0998daf7351345de21278a1c9249a` |
| `training_meta.json` | 1,563 bytes | `d1e91f1c47eb3858874173753a0cdd093e007f2be52b5bf4e2247f10fbd8d8c3` |

---

## 2. Directory Protection Audit

1. **Pretrained Directory Intact:** Pretrained weights in `/home/aditya/rags/models/pretrained/deberta-v3-small` remain 100% bit-for-bit identical to the upstream snapshot. No files were overwritten.
2. **Git Tracking Isolation:** The checkpoint is located under `/home/aditya/rags/models/trained/` outside Git-tracked source directories. No checkpoint binaries were added to git.
