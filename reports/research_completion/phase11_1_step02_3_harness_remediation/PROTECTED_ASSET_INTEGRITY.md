# TrustRAG — Phase 11.1, Step 2.3: Protected Asset Integrity & Governance Report

**Date:** 2026-11-15  
**Audit Type:** Cryptographic Hash Verification & Scope Enforcement  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**HEAD Commit:** `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`  
**Overall Status:** PASSED (100% Immutable Integrity Verified)

---

## 1. Governance Boundary & Authorization Compliance

In accordance with the explicit Step 2.3 authorization scope:
- Training authorization: **NOT GRANTED**. Zero optimizer steps or forward/backward passes were executed on actual training or validation datasets.
- Checkpoint modification: **PROHIBITED**. No pre-existing models or checkpoints were modified, overwritten, or deleted.
- Dataset modification: **PROHIBITED**. All raw, processed, and manifest files remained strictly read-only.
- Git operations: **NO COMMITS, PUSHES, MERGES, OR BRANCH SWITCHING**.

---

## 2. Protected Checkpoint Cryptographic Audits

The cryptographic SHA-256 checksums of all four historical and pretrained model assets were computed post-remediation and compared against pre-step baseline manifests.

| Model / Checkpoint Name | File Path | Status | Pre-Step SHA-256 | Post-Step SHA-256 | Match |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **DeBERTa-v3-small (Pretrained)** | `models/pretrained/deberta-v3-small/pytorch_model.bin` | Protected | `d4b0ebcc7799a2c2dde1a39199cb0ed709f2c6b63a48b8c05133b77955f271a9` | `d4b0ebcc7799a2c2dde1a39199cb0ed709f2c6b63a48b8c05133b77955f271a9` | **EXACT** |
| **Binary Pilot 1000 Checkpoint** | `models/trained/deberta-v3-small-binary-pilot1000/model.safetensors` | Protected | `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` | `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` | **EXACT** |
| **NLI Pilot 1000 Checkpoint** | `models/trained/deberta-v3-small-nli-pilot1000/model.safetensors` | Protected | `500832fa1b9b7c67c2c08d9e1f4d4c76d235d15fa9960d76e1e6e81c220a2f8a` | `500832fa1b9b7c67c2c08d9e1f4d4c76d235d15fa9960d76e1e6e81c220a2f8a` | **EXACT** |
| **NLI Remediated Checkpoint** | `models/trained/deberta-v3-small-nli-remediated/model.safetensors` | Protected | `bb4c26bab4a147c2ad6bdae7ec8a1ecc56841ea56fc89922fd377fb5d70fe113` | `bb4c26bab4a147c2ad6bdae7ec8a1ecc56841ea56fc89922fd377fb5d70fe113` | **EXACT** |

---

## 3. Dataset Immutability Audits

The complete NLI dataset split in `data/processed/sft_v2/nli/` was verified against its baseline SHA-256 manifest:

```bash
cd /home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/nli/ && sha256sum -c checksums.sha256
dataset_manifest.json: OK
exclusion_manifest.json: OK
schema.json: OK
train.jsonl: OK
validation.jsonl: OK
```

| File Name | SHA-256 Checksum | Verified Record Count | Status |
| :--- | :--- | :--- | :---: |
| `train.jsonl` | `b1777c7ac608d6d79171dbc4deaeb7bf5c4ba87acf83adbe53d63020524474ad` | 10,815 samples | **INTACT** |
| `validation.jsonl` | `5ffdc2e9c1f609e9db6786a489745347f71755dc039864d4b1a415ff68f121d5` | 2,704 samples | **INTACT** |
| `dataset_manifest.json` | `d72023bb4129b0a70f443b3db97fba034032d1ef10851897d5a5cf2b0124fe76` | Manifest metadata | **INTACT** |
| `exclusion_manifest.json` | `3780fbca8dc2d4d9cc2a05cf4c28135832a26514fc7dc8161ba05db3a84e6260` | Leakage exclusion IDs | **INTACT** |
| `schema.json` | `4359ebaa000abf0cff83ebc2efd8616a19f4a569d67b845d4c9f131a941e7d23` | Schema definition | **INTACT** |

---

## 4. Codebase & Git Status Verification

- Current Branch: `phase-11` (unswitched).
- Working Tree: No commits, resets, merges, or pushes performed.
- Modifications strictly restricted to:
  1. `tools/training/train_nli_classifier.py` (harness infrastructure)
  2. `tests/unit/test_phase11_step02_3_harness_remediation.py` (unit testing suite)
  3. `reports/research_completion/phase11_1_step02_3_harness_remediation/` (audit report package)

---

## 5. Certification Conclusion

Zero tampering, zero unauthorized training runs, zero dataset alteration, and zero model overwrites occurred during Step 2.3. All protected assets remain cryptographically identical to their historical baselines.

