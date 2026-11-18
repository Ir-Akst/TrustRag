# Track 2, Step 3.0: Objective-Specific Dataset Readiness Verification

**Audit Date:** November 14, 2026  
**Auditor:** ML Infrastructure Auditor  
**Dataset Base Directory:** `/home/aditya/rags/TrustRag-phase11/data/processed/sft_v2/`  

---

## 1. SHA-256 Checksum Re-Verification

All dataset manifests, splits, schemas, and quarantine files in `data/processed/sft_v2/` were independently hashed and compared against the authoritative checksums established in Track 2, Step 2.2.1:

| Dataset Objective | File Checked | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| **`sft_v2/binary`** | `train.jsonl` | `f6a4221a7ea159e1c3132e18e8df5e8b4e4e963bc18090f6717a61d1e4c798fc` | ✅ **VERIFIED MATCH** |
| | `validation.jsonl` | `0d26c5df98ba4fae6fbe53634e2c0e86b3bcf52ee3eb4a5445ea558831e5f8fe` | ✅ **VERIFIED MATCH** |
| | `quarantine.jsonl` | `7734bbd82806fb97fa5f917544062a4b865586616453ef69b47e27da1fe54668` | ✅ **VERIFIED MATCH** |
| | `manifest.json` | `aa7742cf6f74a004eb76a08620ba06ba6778401309f02e646274438df35ae6dc` | ✅ **VERIFIED MATCH** |
| | `schema.json` | `b3d4f40f3b06c8b9399bf0e29bca5b9914b18c645e54d5c3167123aa24b74a36` | ✅ **VERIFIED MATCH** |
| **`sft_v2/nli`** | `train.jsonl` | `6ae9be276ceb7d34be7e39ef38fc9cfaf64188bf24647e33e490fc6a40a233b8` | ✅ **VERIFIED MATCH** |
| | `validation.jsonl` | `26b382ba59c7333503b0c5dfef9a16f2c00224d45d65426e6ef36fc76d7f0237` | ✅ **VERIFIED MATCH** |
| | `quarantine.jsonl` | `5c732c5f1c97a827ea80fba0d588147d3c01c0db721d74ea4727181c0062bc93` | ✅ **VERIFIED MATCH** |
| | `manifest.json` | `3d04d4f8fc99a547a0640d287bb20f8fe6e8119eb1bbffec66f363c4801192e5` | ✅ **VERIFIED MATCH** |
| | `schema.json` | `6e8ddfc734a319f07fe3eb321855a95efd585fe1e61298e3b79412f1165a2ff6` | ✅ **VERIFIED MATCH** |
| **`sft_v2/spans`** | `train.jsonl` | `d179679184fc31f0cfb5cfc7df62002dd9c7faeb3f8a4cbca0bcecbcf243ee70` | ✅ **VERIFIED MATCH** |
| | `validation.jsonl` | `4846433a0e10e42f9b23b49704ae4bf5d35df3e5971a8080bf074bf6b7fc64a7` | ✅ **VERIFIED MATCH** |
| | `quarantine.jsonl` | `24eb482a0d926b472e3a1ec4b1860cb62c19958744ca68c87140f7f32997b69c` | ✅ **VERIFIED MATCH** |
| | `manifest.json` | `d720a46b5a37f07096e57dfcffdd202f523ee453c74ff6482594ccbf1a3fc021` | ✅ **VERIFIED MATCH** |
| | `schema.json` | `799ca9d54c1fc74d4734dae19cfb04ecdf55e1dbd93cf57f72da737a342416b7` | ✅ **VERIFIED MATCH** |
| **`sft_v2/g3_readiness`**| `gap_documentation.json` | `2ebfc0b4719ceaa0209dfa98dfd7681ea6247c20c0f8ff80026e63dc3614adfd` | ✅ **VERIFIED MATCH** |
| | `manifest.json` | `05b0f49a6064f52636bc4028303f8c858d4e9b72cb658e45dc5bb439f048d0d4` | ✅ **VERIFIED MATCH** |
| | `schema.json` | `26d03f0b2f1e6fcb801a693c042858b193235b3ee28e67f082e6bb45bca5391e` | ✅ **VERIFIED MATCH** |

**Baseline Immutability Check:** The historical baseline `data/processed/sft_v1/` checksums were also verified against its 5 files (`train.jsonl`, `validation.jsonl`, `quarantine.jsonl`, `manifest.json`, `schema.json`). All matched 100%.

---

## 2. Quantitative Census & Split Summary

| Objective Dataset | Train Records | Validation Records | Quarantined Records | Total Source Records Processed | Label Completeness |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`sft_v2/binary`** | 26,054 | 5,984 | 52 | 32,090 | 100.0% (Binary: 0=Faithful, 1=Hallucinated) |
| **`sft_v2/nli`** | 10,815 | 2,662 | 18,613 | 32,090 | 100.0% (3-Way: 0=Entailment, 1=Neutral, 2=Contradiction) |
| **`sft_v2/spans`** | 12,072 | 3,018 | 0 (0 unresolvable) | 15,090 | 100.0% (12,756 ground-truth character spans) |
| **`sft_v2/g3_readiness`**| 0 | 0 | 32,090 | 32,090 | 0.0% (0 records fabricated; supervision gap documented) |

---

## 3. Sequence Length & Token Distribution

To inform batch sizing, padding, and truncation strategies, sequence word counts were empirically measured across the full training splits:

| Objective Dataset | Minimum Words | Median Words | 95th Percentile Words | Maximum Words | Recommended Max Token Cutoff | Direct Coverage % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Binary Classification** | 30 | 128 | 1,463 | 3,783 | 512 tokens | ~84.2% |
| **3-Way NLI** | 109 | 451 | 1,102 | 2,060 | 512 tokens | ~62.5% |
| **Fine-Grained Spans** | 239 | 810 | 2,015 | 3,783 | 512 tokens | ~48.1% (Sliding window required) |

### Key Architectural Implication:
For discriminative models bounded to 512 maximum sequence length (standard BERT / RoBERTa / DeBERTa):
- **Binary Classification:** 512 tokens covers 84.2% of examples without truncation. For longer examples, truncating distal context while preserving question and candidate response is viable.
- **Span Extraction:** Truncation would discard candidate response tokens containing hallucinations. Therefore, a **stride / sliding window tokenization** (stride = 128) is mandatory to evaluate long candidate texts without data loss.
