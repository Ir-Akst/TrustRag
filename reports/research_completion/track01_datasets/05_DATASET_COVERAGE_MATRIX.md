# TrustRAG Research Completion — Track 1, Step 1: Dataset Coverage Matrix

**Date**: 2026-11-13  
**Branch**: `phase-11`  
**Repository**: `/home/aditya/rags/TrustRag-phase11`  

---

## 1. Research Benchmark Coverage Matrix

The coverage status of each dataset is tracked across six standardized lifecycle stages:
1. `NOT DOWNLOADED`: Dataset identified; acquisition pipeline configured; not present locally.
2. `ACCESS BLOCKED`: Gated access, license restrictions, or absent public repository prevents automated acquisition.
3. `DOWNLOADED`: Raw files present and cryptographically verified.
4. `PREPROCESSED`: Normalized into JSONL splits with schema compliance.
5. `VALIDATED`: Zero schema errors, deduplication complete, split leakage confirmed 0.
6. `READY FOR EXPERIMENTS`: Full benchmark pipeline active; ready for evaluation and defense benchmarking.

---

### Benchmark Lifecycle Status

| # | Dataset | Category | Target Record Type | Target Count | Acquired Count | Storage Footprint | Lifecycle State |
| :-: | :--- | :--- | :--- | :-: | :-: | :-: | :--- |
| **1** | **RAGTruth** | Hallucination Detection | `ClaimVerificationRecord` | 18,000 | **17,790** | 148.6 MB (raw+proc) | **READY FOR EXPERIMENTS** |
| **2** | **HaluEval** | Hallucination Detection | `ClaimVerificationRecord` | 10,000 | **20,000** | 20.6 MB (raw+proc) | **READY FOR EXPERIMENTS** |
| **3** | **HotpotQA** | Multi-hop QA | `QueryRecord` | 30,000 | **7,405** (val) | 30.5 MB (raw+proc) | **READY FOR EXPERIMENTS** |
| **4** | **MS MARCO** | Web Reading Comprehension | `QueryRecord` | 100,000 | **10,047** (val) | 24.0 MB (raw+proc) | **READY FOR EXPERIMENTS** |
| **5** | **Natural Questions** | Open-Domain QA | `QueryRecord` | 30,000 | 0 | 0 MB | **NOT DOWNLOADED** |
| **6** | **LLM-AggreFact** | Multi-Task Hallucination | `ClaimVerificationRecord` | 5,000 | 0 | 0 MB | **ACCESS BLOCKED** |
| **7** | **RSB** | RAG Security Bench | `SecurityRecord` | 5,000 | 0 | 0 MB | **ACCESS BLOCKED** |

---

## 2. Summary of Coverage Statistics

- **Total Canonical Datasets Audited**: 7
- **Datasets Ready for Immediate Experimentation**: **4** (RAGTruth, HaluEval, HotpotQA, MS MARCO)
- **Total Validated Research Records in Memory/Disk**: **55,242 records**
- **Datasets Gated / Blocked**: **2** (LLM-AggreFact, RSB)
- **Datasets Deferred due to Storage/Bandwidth**: **1** (Natural Questions, ~40 GB full corpus)
- **Total Acquired Storage Footprint**: **~224 MB** (91.5 MB raw + 133.0 MB processed)

