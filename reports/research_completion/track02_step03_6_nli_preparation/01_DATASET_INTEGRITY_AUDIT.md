# TrustRAG — Track 2, Step 3.6: NLI Dataset Integrity & Provenance Audit

## 1. Census & Class Distribution Verification

| Split | Expected Count | Observed Count | ENTAILMENT (0) | CONTRADICTION (1) | NEUTRAL (2) | Schema Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train** | 10,815 | **10,815** | 6,707 (62.0%) | 1,420 (13.1%) | 2,688 (24.9%) | **100% VALID** |
| **Validation** | 2,662 | **2,662** | 1,662 (62.4%) | 356 (13.4%) | 644 (24.2%) | **100% VALID** |
| **Combined** | 13,477 | **13,477** | 8,369 (62.1%) | 1,776 (13.2%) | 3,332 (24.7%) | **100% VALID** |

- **Malformed Lines:** 0
- **Missing Required Fields:** 0
- **Empty / Blank Premise or Hypothesis:** 0
- **Upstream Source Corpus:** 100% RAGTruth human annotations (`source_dataset == "ragtruth"`).

---

## 2. Leakage & Isolation Audit

| Audit Target | Evaluation Scope | Observed Overlap | Isolation Status |
| :--- | :--- | :---: | :---: |
| Example ID Overlap | Train vs. Validation | **0 IDs** | **VERIFIED_DISJOINT** |
| Document / Premise Hash Overlap | SHA-256 of `premise` text | **0 Documents** | **VERIFIED_DISJOINT** |
| Canonical Test Set Exposure | Upstream `test.jsonl` files | **0 Records** | **STRICTLY_ISOLATED** |
| Binary Split Independence | Pilot Validation (200 records) | NLI records isolated | **VERIFIED_ISOLATED** |

---

## 3. Exclusion Manifest Audit

The exclusion manifest (`data/processed/sft_v2/nli/exclusion_manifest.json`) records exactly **1,614 quarantined instances**:
- `RAGTRUTH_MIXED_CONFLICT_AND_BASELESS_INFO`: **1,613 records**
  * *Reason:* Instances where a response contains both factual contradictions and unsupported baseless additions were excluded to prevent contradictory supervision between `CONTRADICTION` and `NEUTRAL`.
- `HALUEVAL_EXCLUDED_LACKS_DEFENSIBLE_NLI_SUPERVISION`: **1 record** (entire corpus policy)
  * *Reason:* HaluEval does not provide token/span-level annotations distinguishing between contradictions and baseless info; assigning 3-way labels to HaluEval would constitute ungrounded heuristic synthesis.
