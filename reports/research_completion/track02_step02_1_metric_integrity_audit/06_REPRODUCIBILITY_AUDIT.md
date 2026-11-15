# TrustRAG — Track 1, Step 2.1: Independent Benchmark Metric Integrity Audit
## 06. Reproducibility Audit

### 1. Independent Rerun Protocol
- **Rerun Environment:** `/tmp/track02_reproducibility_test`
- **Script Executed:** `tools/evaluation/run_track02_benchmarks.py --output-dir /tmp/track02_reproducibility_test`
- **Execution Mode:** Full, untruncated evaluation across all 4 benchmarks (5,700 verification records + 17,111 retrieval queries).
- **Runtime:** 265.3 seconds.

---

### 2. Record-by-Record Determinism Results

| Benchmark File | Original Records | Rerun Records | Verdict / Score Match Rate | Aggregate Metric Match |
| :--- | :--- | :--- | :--- | :--- |
| `predictions_ragtruth.jsonl` | 2,700 | 2,700 | **2,700 / 2,700 (100.0%)** | **EXACT MATCH** |
| `predictions_halueval.jsonl` | 3,000 | 3,000 | **3,000 / 3,000 (100.0%)** | **EXACT MATCH** |
| `predictions_hotpotqa_retrieval.jsonl` | 7,405 | 7,405 | **7,405 / 7,405 (100.0%)** | **EXACT MATCH** |
| `predictions_msmarco_retrieval.jsonl` | 9,706 | 9,706 | **9,706 / 9,706 (100.0%)** | **EXACT MATCH** |
| `metrics_ragtruth.json` | - | - | **Identical JSON** | **EXACT MATCH** |
| `metrics_halueval.json` | - | - | **Identical JSON** | **EXACT MATCH** |
| `metrics_hotpotqa.json` | - | - | **Identical JSON** | **EXACT MATCH** |
| `metrics_msmarco.json` | - | - | **Identical JSON** | **EXACT MATCH** |

---

### 3. Forensic Analysis of Textual Diffs in Explanations
In RAGTruth and HaluEval, 200 and 280 records exhibited superficial string diffs in the `explanation` field:
- **Example:**
  - Original: `unverified entities ['philadelphia', 'thomas', 'keonna', 'isis']`
  - Rerun: `unverified entities ['thomas', 'keonna', 'philadelphia', 'isis']`
- **Cause:** Python's internal hash randomization (`PYTHONHASHSEED`) alters the iteration order of Python `set` elements.
- **Verification:** All numerical scores, classifications, verdicts, and ground truths are 100.0% invariant.
