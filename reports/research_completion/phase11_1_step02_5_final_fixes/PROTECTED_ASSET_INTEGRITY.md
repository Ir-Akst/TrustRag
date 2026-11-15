# TrustRAG — Phase 11.1, Step 2.5: Protected Asset Integrity & Scope Compliance

**Date:** 2026-11-15  
**Auditor / Engineer:** Senior ML Infrastructure Engineer  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**Commit HEAD:** `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`  
**Integrity Status:** 100% CRYPTOGRAPHICALLY IDENTICAL & COMPLIANT

---

## 1. Scope Boundary Enforcement

Under Step 2.5 explicit authorization constraints:
- **No Model Training:** 0 forward or backward passes were executed on real datasets. Zero optimizer updates were committed.
- **No Checkpoint Overwrites:** Zero files in historical checkpoint directories were modified or deleted.
- **No Dataset Tampering:** All training, validation, and raw datasets remained read-only.
- **No Git State Mutation:** Zero commits, pushes, merges, resets, or branch checkouts occurred.

---

## 2. Protected Checkpoint Cryptographic Audits

The cryptographic SHA-256 checksums of all four historical and pretrained model assets were computed post-remediation and verified against the pre-step baseline:

| Asset Name | Canonical File Path | Status | SHA-256 Digest | Match |
| :--- | :--- | :---: | :--- | :---: |
| **Pretrained DeBERTa-v3-small** | `models/pretrained/deberta-v3-small/pytorch_model.bin` | Protected | `d4b0ebcc7799a2c2dde1a39199cb0ed709f2c6b63a48b8c05133b77955f271a9` | **EXACT** |
| **Binary Pilot 1000** | `models/trained/deberta-v3-small-binary-pilot1000/model.safetensors` | Protected | `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` | **EXACT** |
| **NLI Pilot 1000** | `models/trained/deberta-v3-small-nli-pilot1000/model.safetensors` | Protected | `500832fa1b9b7c67c2c08d9e1f4d4c76d235d15fa9960d76e1e6e81c220a2f8a` | **EXACT** |
| **NLI Remediated** | `models/trained/deberta-v3-small-nli-remediated/model.safetensors` | Protected | `bb4c26bab4a147c2ad6bdae7ec8a1ecc56841ea56fc89922fd377fb5d70fe113` | **EXACT** |

---

## 3. Dataset Immutability Audits

The NLI dataset split in `data/processed/sft_v2/nli/` was audited against its cryptographic manifest:

```bash
cd /home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/ && sha256sum -c checksums.sha256
dataset_manifest.json: OK
exclusion_manifest.json: OK
schema.json: OK
train.jsonl: OK
validation.jsonl: OK
```

| File Name | SHA-256 Checksum | Verified Records | Status |
| :--- | :--- | :---: | :---: |
| `train.jsonl` | `b1777c7ac608d6d79171dbc4deaeb7bf5c4ba87acf83adbe53d63020524474ad` | 10,815 | **INTACT** |
| `validation.jsonl` | `5ffdc2e9c1f609e9db6786a489745347f71755dc039864d4b1a415ff68f121d5` | 2,704 | **INTACT** |
| `dataset_manifest.json` | `d72023bb4129b0a70f443b3db97fba034032d1ef10851897d5a5cf2b0124fe76` | - | **INTACT** |
| `exclusion_manifest.json` | `3780fbca8dc2d4d9cc2a05cf4c28135832a26514fc7dc8161ba05db3a84e6260` | - | **INTACT** |
| `schema.json` | `4359ebaa000abf0cff83ebc2efd8616a19f4a569d67b845d4c9f131a941e7d23` | - | **INTACT** |

---

## 4. Codebase & Git Status Verification

- Branch: `phase-11` (unswitched).
- Commit: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` (unchanged).
- Git working directory changes strictly limited to:
  1. `tools/training/train_nli_classifier.py` (two targeted limitation fixes).
  2. `tests/unit/test_phase11_step02_5_final_fixes.py` (synthetic unit tests).
  3. `reports/research_completion/phase11_1_step02_5_final_fixes/` (Step 2.5 documentation package).

---

## 5. Certification

All protected assets, models, weights, datasets, manifests, and git boundaries remain cryptographically pristine. Zero unauthorized training or data alteration occurred.

