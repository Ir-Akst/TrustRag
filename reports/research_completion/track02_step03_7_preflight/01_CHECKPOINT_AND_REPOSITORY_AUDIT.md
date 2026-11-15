# TrustRAG — Track 2, Step 3.7: Checkpoint & Repository Audit

## 1. Repository State Verification

| Repository Target | Path | Active Branch | HEAD Commit | Audit Status |
| :--- | :--- | :---: | :---: | :---: |
| **Primary Project** | `/home/aditya/rags/TrustRag-phase11` | `phase-11` | `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` | **MATCH_EXPECTED** |
| **Protected Baseline** | `/home/aditya/rags/TrustRag` | `phase-10` | `e65bcc80aac634900d1f8e343880fddf66cec168` | **STRICTLY_UNTOUCHED** |

---

## 2. Checkpoint Hash Cross-Verification (vs Step 3.6 Audit Manifest)

### Pretrained Snapshot (`microsoft/deberta-v3-small`)
- Location: `/home/aditya/rags/models/pretrained/deberta-v3-small`
- `config.json` SHA-256: `b0bb1caf90a50aa67d1085130508dfbf8646ac5a11928305e280b07a36e100ae` (**VERIFIED**)
- `pytorch_model.bin` SHA-256: `d4b0ebcc7799a2c2dde1a39199cb0ed709f2c6b63a48b8c05133b77955f271a9` (**VERIFIED**)
- `tokenizer_config.json` SHA-256: `3f3978e0c036f2c2588cac34a6047cbb0af0b0dc1814254e291028529805496d` (**VERIFIED**)
- `spm.model` SHA-256: `c679fbf93643d19aab7ee10c0b99e460bdbc02fedf34b92b05af343b4af586fd` (**VERIFIED**)

### Accepted Binary Classifier Checkpoint (`deberta-v3-small-binary-pilot1000`)
- Location: `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`
- `model.safetensors` SHA-256: `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` (**IMMUTABLE_PRESERVED**)
- `config.json` SHA-256: `7cee3abbc6b9a3971c682867db8d16bb79eeaee218d544463bcc2433d82ff16d` (**IMMUTABLE_PRESERVED**)
- `tokenizer.json` SHA-256: `d87197028bcdd4a6c68dc03bd9b04e0956b0998daf7351345de21278a1c9249a` (**IMMUTABLE_PRESERVED**)

### Protected Path Overwrite Guard Audit
The runner `tools/training/train_nli_classifier.py` actively checks target output directories against:
1. `/home/aditya/rags/models/pretrained/deberta-v3-small`
2. `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`
3. `/home/aditya/rags/TrustRag`
Any save operation targeting these paths raises a fatal `SecurityViolationError`.
