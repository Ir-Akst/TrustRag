# Track 2, Step 3.2: Authoritative SHA-256 Manifest for Staged Model

**Audit Date:** November 14, 2026  
**Auditor:** Senior ML Infrastructure Engineer  
**Staged Model Directory:** `/home/aditya/rags/models/pretrained/deberta-v3-small/`  
**Upstream Commit:** `a36c739020e01763fe789b4b85e2df55d6180012`  

---

## 1. Authoritative SHA-256 Checksums

Every staged file was hashed using cryptographic SHA-256:

```
fa057bb09b78fe6d33af5a01440be5e8c881cd8055de35ee5588ea759cf57bfc  .gitattributes
9aa2d47666370a87d20422ed68a1ee80d79d66b4447b6f9925d97d11f4605d24  README.md
b0bb1caf90a50aa67d1085130508dfbf8646ac5a11928305e280b07a36e100ae  config.json
d4b0ebcc7799a2c2dde1a39199cb0ed709f2c6b63a48b8c05133b77955f271a9  pytorch_model.bin
c679fbf93643d19aab7ee10c0b99e460bdbc02fedf34b92b05af343b4af586fd  spm.model
3f3978e0c036f2c2588cac34a6047cbb0af0b0dc1814254e291028529805496d  tokenizer_config.json
```

---

## 2. Checksum Manifest File

The above digests are permanently saved in the model directory:
- [checksums.sha256](file:///home/aditya/rags/models/pretrained/deberta-v3-small/checksums.sha256)
- [manifest.json](file:///home/aditya/rags/models/pretrained/deberta-v3-small/manifest.json)
