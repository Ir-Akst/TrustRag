# Track 2, Step 3.2.1: Dataset Preservation & Integrity Audit

**Audit Date:** November 14, 2026  
**Auditor:** Independent ML Infrastructure Auditor  
**Dataset Base Directory:** `/home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/`  

---

## 1. Authoritative 18-File SHA-256 Verification

Every dataset file in `sft_v2/` was independently hashed during this audit and compared against the baseline hashes established in Track 2 Step 2.2.1:

| Dataset Objective | File Name | Authoritative SHA-256 Digest | Audit Verification Status |
| :--- | :--- | :--- | :--- |
| **`binary/`** | `train.jsonl` | `f6a4221a7ea159e1c3132e18e8df5e8b4e4e963bc18090f6717a61d1e4c798fc` | ✅ **100% BIT-EXACT MATCH** |
| | `validation.jsonl` | `0d26c5df98ba4fae6fbe53634e2c0e86b3bcf52ee3eb4a5445ea558831e5f8fe` | ✅ **100% BIT-EXACT MATCH** |
| | `quarantine.jsonl` | `7734bbd82806fb97fa5f917544062a4b865586616453ef69b47e27da1fe54668` | ✅ **100% BIT-EXACT MATCH** |
| | `manifest.json` | `aa7742cf6f74a004eb76a08620ba06ba6778401309f02e646274438df35ae6dc` | ✅ **100% BIT-EXACT MATCH** |
| | `schema.json` | `b3d4f40f3b06c8b9399bf0e29bca5b9914b18c645e54d5c3167123aa24b74a36` | ✅ **100% BIT-EXACT MATCH** |
| **`nli/`** | `train.jsonl` | `6ae9be276ceb7d34be7e39ef38fc9cfaf64188bf24647e33e490fc6a40a233b8` | ✅ **100% BIT-EXACT MATCH** |
| | `validation.jsonl` | `26b382ba59c7333503b0c5dfef9a16f2c00224d45d65426e6ef36fc76d7f0237` | ✅ **100% BIT-EXACT MATCH** |
| | `quarantine.jsonl` | `5c732c5f1c97a827ea80fba0d588147d3c01c0db721d74ea4727181c0062bc93` | ✅ **100% BIT-EXACT MATCH** |
| | `manifest.json` | `3d04d4f8fc99a547a0640d287bb20f8fe6e8119eb1bbffec66f363c4801192e5` | ✅ **100% BIT-EXACT MATCH** |
| | `schema.json` | `6e8ddfc734a319f07fe3eb321855a95efd585fe1e61298e3b79412f1165a2ff6` | ✅ **100% BIT-EXACT MATCH** |
| **`spans/`** | `train.jsonl` | `d179679184fc31f0cfb5cfc7df62002dd9c7faeb3f8a4cbca0bcecbcf243ee70` | ✅ **100% BIT-EXACT MATCH** |
| | `validation.jsonl` | `4846433a0e10e42f9b23b49704ae4bf5d35df3e5971a8080bf074bf6b7fc64a7` | ✅ **100% BIT-EXACT MATCH** |
| | `quarantine.jsonl` | `24eb482a0d926b472e3a1ec4b1860cb62c19958744ca68c87140f7f32997b69c` | ✅ **100% BIT-EXACT MATCH** |
| | `manifest.json` | `d720a46b5a37f07096e57dfcffdd202f523ee453c74ff6482594ccbf1a3fc021` | ✅ **100% BIT-EXACT MATCH** |
| | `schema.json` | `799ca9d54c1fc74d4734dae19cfb04ecdf55e1dbd93cf57f72da737a342416b7` | ✅ **100% BIT-EXACT MATCH** |
| **`g3_readiness/`**| `gap_documentation.json` | `2ebfc0b4719ceaa0209dfa98dfd7681ea6247c20c0f8ff80026e63dc3614adfd` | ✅ **100% BIT-EXACT MATCH** |
| | `manifest.json` | `05b0f49a6064f52636bc4028303f8c858d4e9b72cb658e45dc5bb439f048d0d4` | ✅ **100% BIT-EXACT MATCH** |
| | `schema.json` | `26d03f0b2f1e6fcb801a693c042858b193235b3ee28e67f082e6bb45bca5391e` | ✅ **100% BIT-EXACT MATCH** |

---

## 2. Preservation Guarantee

- **Zero Modifications:** No files were rewritten, truncated, appended, or moved.
- **Historical Baseline (`sft_v1`):** All 5 files in `data/processed/sft_v1/` were also verified intact against their frozen SHA-256 digests.
