# TrustRAG — Track 2, Step 3.11: Repository & Protected Checkpoint Integrity Audit

## 1. Git Repository State

| Repository Path | Expected Branch | Current Branch | Expected HEAD Commit | Current HEAD Commit | Tree Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `/home/aditya/rags/TrustRag-phase11` | `phase-11` | `phase-11` | `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` | `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` | Modified / Untracked Clean |
| `/home/aditya/rags/TrustRag` (Phase 10) | `phase-10` | `phase-10` | `e65bcc80aac634900d1f8e343880fddf66cec168` | `e65bcc80aac634900d1f8e343880fddf66cec168` | Strictly Immutable |

---

## 2. Checkpoint SHA256 Integrity Verification

### A. Pretrained Backbone (`microsoft/deberta-v3-small`)
Location: `/home/aditya/rags/models/pretrained/deberta-v3-small`
- `.gitattributes`: `c53443fe7d039cb01df8d8e578c91350a256df24e4d6ddcebfe7a31b67f1396b` (`OK`)
- `README.md`: `fc129b865cbef9f80a377b21dc800d927c3da3fe6efb46ec6ff38a2e1d71cb9f` (`OK`)
- `config.json`: `a4f3b8b15d0bf0a133d5ba40986161fe041eb49aa21eaec6a6d0932a31952e4f` (`OK`)
- `pytorch_model.bin`: `30d9ea4101e14930d0fa85141b712aaae2817d23d8c1995874406214bfb287ac` (`OK`)
- `spm.model`: `72ea9804b2b3a0937a0772714c688d0d540203f56cf86fc2c62c9540b686d123` (`OK`)
- `tokenizer_config.json`: `d047b309ea83669ee38b2586e3f4333ce5b14115e5898835d02677bc05cc1c3a` (`OK`)

### B. Accepted Binary Pilot Checkpoint
Location: `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`
- `model.safetensors`: `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` (`VERIFIED UNCHANGED`)
- `config.json`: `7cee3abbc6b9a3971c682867db8d16bb79eeaee218d544463bcc2433d82ff16d` (`VERIFIED UNCHANGED`)
- `tokenizer.json`: `d87197028bcdd4a6c68dc03bd9b04e0956b0998daf7351345de21278a1c9249a` (`VERIFIED UNCHANGED`)

### C. Failed Step 3.8 NLI Pilot Checkpoint
Location: `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000`
- `model.safetensors`: `500832fa1b9b7c67c2c08d9e1f4d4c76d235d15fa9960d76e1e6e81c220a2f8a` (`VERIFIED UNCHANGED`)
- `config.json`: `38370396a4e2988a14226b6b8875766e660ab8bbd1374b9e23a6e0c7a05ef385` (`VERIFIED UNCHANGED`)
- `training_meta.json`: `f2e755836bf5c74a858f6e836cb7181f378a69b0280c8e7dc416f8e8dcb0d95f` (`VERIFIED UNCHANGED`)

---

## 3. Historical Audit Reports Verification

All report directories pass `sha256sum -c checksums.sha256`:
- `track02_step03_6_nli_preparation`: 8 files OK
- `track02_step03_7_preflight`: 9 files OK
- `track02_step03_8_nli_training`: 8 files OK
- `track02_step03_9_failure_analysis`: 10 files OK
- `track02_step03_10_remediation`: 9 files OK
