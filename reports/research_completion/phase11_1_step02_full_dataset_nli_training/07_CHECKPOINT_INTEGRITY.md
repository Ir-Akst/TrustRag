# TrustRAG — Phase 11.1, Step 2: Full-Dataset NLI Training Audit
## 07 — Checkpoint Integrity & Protected Asset Verification

- **Audit Date:** 2026-11-14T18:25:00Z
- **Auditor:** Senior ML Training Engineer & Independent Experimental Auditor

---

### 1. New Output Directory Status

- **Authorized Destination:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch/`
- **Preflight Check:** Checked for existence.
- **Result:** Directory does not exist on disk (zero bytes written). Zero files created.

---

### 2. Protected Baseline Checkpoints Audit

All 4 protected checkpoints were audited before and after preflight checks. Their cryptographic digests confirm zero modification, deletion, or corruption:

| Protected Checkpoint | File Path | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| **Pretrained Base** | `/home/aditya/rags/models/pretrained/deberta-v3-small/pytorch_model.bin` | `b3f81e3da06c7e2ad6e58b1a37803a6bcbf3ee258ab08e2f81643c1b64ff06d6` | ✅ IMMUTABLE |
| **Step 3.4.2 Binary Pilot** | `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000/model.safetensors` | `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` | ✅ IMMUTABLE |
| **Step 3.8 Failed NLI Pilot** | `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000/model.safetensors` | `500832fa1b9b7c67c2c08d9e1f4d4c76d235d15fa9960d76e1e6e81c220a2f8a` | ✅ IMMUTABLE |
| **Step 3.16 Remediated Pilot**| `/home/aditya/rags/models/trained/deberta-v3-small-nli-remediated/model.safetensors` | `bb4c26bab4a147c2ad6bdae7ec8a1ecc56841ea56fc89922fd377fb5d70fe113` | ✅ IMMUTABLE |

---

### 3. Repository Cleanliness Confirmation

- `git rev-parse HEAD`: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`
- `git branch --show-current`: `phase-11`
- Zero tracked files modified or deleted during preflight.

