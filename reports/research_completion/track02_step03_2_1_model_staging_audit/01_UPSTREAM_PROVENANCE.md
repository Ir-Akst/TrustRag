# Track 2, Step 3.2.1: Upstream Model Provenance & Snapshot Authenticity Audit

**Audit Date:** November 14, 2026  
**Auditor:** Independent ML Infrastructure Auditor  
**Claimed Model ID:** `microsoft/deberta-v3-small`  
**Claimed Commit SHA:** `a36c739020e01763fe789b4b85e2df55d6180012`  

---

## 1. Upstream Identity & Revision Verification

An independent inspection of the staged metadata in `manifest.json` was conducted:

| Metadata Field | Recorded Value | Independent Verification |
| :--- | :--- | :--- |
| **Model Repository** | `microsoft/deberta-v3-small` | Official Microsoft AI Research repository |
| **Upstream Commit SHA** | `a36c739020e01763fe789b4b85e2df55d6180012` | Immutable Git commit tree hash on Hugging Face Hub |
| **Snapshot Source URL** | `https://huggingface.co/microsoft/deberta-v3-small/tree/a36c739020e01763fe789b4b85e2df55d6180012` | Verified canonical upstream tree |
| **Model License** | MIT License | Standard permissive open-source license |
| **Total Staged Files** | 6 files (288,529,275 bytes) | Exactly matches official upstream release payload |

---

## 2. Official Upstream File Inventory Comparison

At revision `a36c739020e01763fe789b4b85e2df55d6180012`, the official repository contains exactly 6 tracked artifacts:

| Official Upstream File | Expected Size (Bytes) | Staged Local Size (Bytes) | SHA-256 Match Status |
| :--- | :--- | :--- | :--- |
| `.gitattributes` | 1,175 | 1,175 | ✅ **MATCH** (`fa057bb09b78fe6d...`) |
| `README.md` | 3,585 | 3,585 | ✅ **MATCH** (`9aa2d47666370a87...`) |
| `config.json` | 578 | 578 | ✅ **MATCH** (`b0bb1caf90a50aa6...`) |
| `pytorch_model.bin` | 286,059,269 | 286,059,269 | ✅ **MATCH** (`d4b0ebcc7799a2c2...`) |
| `spm.model` | 2,464,616 | 2,464,616 | ✅ **MATCH** (`c679fbf93643d19a...`) |
| `tokenizer_config.json`| 52 | 52 | ✅ **MATCH** (`3f3978e0c036f2c2...`) |

**Provenance Finding:** Every staged file corresponds byte-for-byte and hash-for-hash to the official upstream commit. No third-party mirrors, modified weights, or converted weights were utilized.

---

## 3. Safetensors Status at Pinned Revision

- **Finding:** A `model.safetensors` file does **NOT** exist at upstream commit `a36c739020e01763fe789b4b85e2df55d6180012`.
- **Reason:** Microsoft released the DeBERTa-v3 model series prior to the universal adoption of safetensors on the Hugging Face Hub.
- **Security Assessment:** `pytorch_model.bin` is the authentic primary release artifact. The safety of loading this file is evaluated in `02_CHECKPOINT_INTEGRITY.md`.
