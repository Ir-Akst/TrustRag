# TrustRAG Phase 10 — Dataset Inventory & Integrity Report

**Source Artifact:** `reports/phase10_experiments/phase10_20261112T073204Z_canonical_v2/bundle.json`  
**Mode:** Offline (`offline=true`, `seed=42`, zero automatic network downloads)

---

## 1. External Research Benchmarks (Target 7)

| Dataset | Official Source | License / Access | Eval / Train | Local Records | Status | Notes |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **RAGTruth** | `ParticleMedia/RAGTruth` | `MIT` / `open` | Eval + Train | 10 (`test.jsonl`: 5, `raw_test.jsonl`: 5) | **PARTIALLY_READY** | Below research threshold (100 vs 18,000 target); full parity `BLOCKED` |
| **HaluEval** | `pminervini/HaluEval` | `MIT` / `open` | Eval + Train | 0 | **BLOCKED** | No cached files offline |
| **LLM-AggreFact** | `lytang/LLM-AggreFact` | `CC-BY-ND-4.0` / `gated` | Eval only (`permitted_for_training=False`) | 0 | **BLOCKED** | Gated dataset absent offline |
| **RSB** | `arXiv:2505.18543` | Academic / `pending_verification` | Eval only (`permitted_for_training=False`) | 0 | **BLOCKED** | No cached files or public distribution URL offline |
| **Natural Questions** | `google-research-datasets/natural_questions` | `CC-BY-SA-3.0` / `open` | Eval + Train | 0 | **BLOCKED** | Absent offline |
| **HotpotQA** | `hotpotqa/hotpot_qa` | `CC-BY-SA-4.0` / `open` | Eval + Train | 0 | **BLOCKED** | Absent offline |
| **MS MARCO** | `microsoft/ms_marco` | Non-commercial / `open` | Eval + Train | 0 | **BLOCKED** | Absent offline |

---

## 2. Local Benchmarks & Smoke Fixtures

| Dataset | Scope | Splits & Counts | Status | Notes |
| :--- | :--- | :--- | :---: | :--- |
| `knowledge_poisoning` | `local_benchmark` | `train=104`, `val=22`, `test=24` | **AVAILABLE** | `data/benchmarks_backup/knowledge_poisoning` |
| `adversarial_robustness` | `local_benchmark` | `train=174`, `val=36`, `test=40` | **AVAILABLE** | `data/benchmarks_backup/adversarial_robustness` |
| `clean_rag` | `local_benchmark` | `train=70`, `val=15`, `test=15` | **AVAILABLE** | `data/benchmarks_backup/clean_rag` |
| `hallucination` | `local_benchmark` | `train=7`, `val=1`, `test=3` | **AVAILABLE** | `data/benchmarks_backup/hallucination` |
| `boolq` | `local_benchmark` | `train=70`, `val=15`, `test=15` | **AVAILABLE** | `data/processed/boolq/custom_splits` |
| `wice_smoke` | `local_smoke_fixture` | `test=4` | **AVAILABLE** | Smoke fixture only |
| `expertqa_smoke` | `local_smoke_fixture` | `test=4` | **AVAILABLE** | Smoke fixture only |

All local JSONL files have SHA-256 checksums, byte sizes, and record counts recorded in `bundle.json` (`dataset_inventory.items`).
