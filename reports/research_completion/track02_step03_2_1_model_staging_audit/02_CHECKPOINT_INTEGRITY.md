# Track 2, Step 3.2.1: Checkpoint Integrity & Security Assessment

**Audit Date:** November 14, 2026  
**Auditor:** Independent ML Infrastructure Auditor  
**Inspected Directory:** `/home/aditya/rags/models/pretrained/deberta-v3-small/`  

---

## 1. Cryptographic SHA-256 Digest Verification

An independent hash computation was executed across every staged file in the local snapshot directory:

| Staged File Name | File Size (Bytes) | Cryptographic SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| **`pytorch_model.bin`** | 286,059,269 | `d4b0ebcc7799a2c2dde1a39199cb0ed709f2c6b63a48b8c05133b77955f271a9` | ✅ **VERIFIED** |
| **`spm.model`** | 2,464,616 | `c679fbf93643d19aab7ee10c0b99e460bdbc02fedf34b92b05af343b4af586fd` | ✅ **VERIFIED** |
| **`config.json`** | 578 | `b0bb1caf90a50aa67d1085130508dfbf8646ac5a11928305e280b07a36e100ae` | ✅ **VERIFIED** |
| **`tokenizer_config.json`**| 52 | `3f3978e0c036f2c2588cac34a6047cbb0af0b0dc1814254e291028529805496d` | ✅ **VERIFIED** |
| **`README.md`** | 3,585 | `9aa2d47666370a87d20422ed68a1ee80d79d66b4447b6f9925d97d11f4605d24` | ✅ **VERIFIED** |
| **`.gitattributes`** | 1,175 | `fa057bb09b78fe6d33af5a01440be5e8c881cd8055de35ee5588ea759cf57bfc` | ✅ **VERIFIED** |

---

## 2. Checkpoint Format & Packaging Audit

`pytorch_model.bin` was inspected for internal structure:
- **Archive Format:** Valid standard **PyTorch v1.6+ Zip Archive** (`zipfile.is_zipfile() == True`).
- **Archive Table of Contents:**
  - `archive/data.pkl` (15,332 bytes): Standard PyTorch tensor reconstruction metadata.
  - `archive/data/[tensor_ids]` (114 binary tensor data records).
- **Integrity Check:** The zip archive decompresses without errors or truncated byte markers.

---

## 3. Pickle Deserialization Security Assessment

Because `pytorch_model.bin` uses the PyTorch checkpoint format (which relies on Python pickle for tensor metadata serialization), security risks associated with arbitrary code execution during unpickling were audited:

1. **Native PyTorch Safe Unpickler (`weights_only=True`):**
   - PyTorch 2.4+ implements a restricted unpickler that disallows arbitrary global execution (`torch.load(..., weights_only=True)`).
   - In our audit test, `torch.load("pytorch_model.bin", weights_only=True)` succeeded cleanly, proving that the checkpoint contains **strictly tensor storage objects and zero custom Python execution classes**.
2. **Transformers Loader Implementation:**
   - In `transformers==5.20.2`, `AutoModel.from_pretrained()` internally defaults to safe deserialization patterns when loading `.bin` files.
3. **No Conversion Required:**
   - Because the authentic upstream checkpoint passes safe deserialization without warnings and hashes match official Microsoft records, converting the checkpoint locally is neither necessary nor authorized.
