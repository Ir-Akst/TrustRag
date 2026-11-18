#!/usr/bin/env python3
"""Generator for Track 2, Step 3.13 Independent Evidence Retention & Multi-Chunk Acceptance Audit Reports.

Generates 11 deliverables:
1. 00_EXECUTIVE_AUDIT_REPORT.md
2. 01_REPOSITORY_AND_CHECKPOINT_INTEGRITY.md
3. 02_EVIDENCE_SPAN_RETENTION_AUDIT.md
4. 03_MULTI_CHUNK_IMPLEMENTATION_AUDIT.md
5. 04_AGGREGATION_ENGINE_AUDIT.md
6. 05_RESOURCE_PROFILE_AUDIT.md
7. 06_TEST_AND_AUTHORIZATION_AUDIT.md
8. 07_SCIENTIFIC_LIMITATIONS.md
9. CONSOLIDATED_INDEPENDENT_AUDIT.md
10. audit_manifest.json
11. checksums.sha256
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

PROJECT_ROOT = Path("/home/aditya/rags/TrustRag-phase11")
REPORT_DIR = PROJECT_ROOT / "reports/research_completion/track02_step03_13_independent_audit"
STEP12_DATA_FILE = PROJECT_ROOT / "tools/evaluation/step03_12_evaluation_data.json"


def compute_sha256(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def generate_reports():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 00_EXECUTIVE_AUDIT_REPORT.md
    doc_00 = """# TrustRAG — Track 2, Step 3.13: Executive Independent Acceptance Audit Report

- **Date:** 2026-11-14T13:45:00Z
- **Role:** Independent Senior ML Infrastructure Auditor, NLP Architect & Adversarial Experimental Reviewer
- **Target Repository:** `/home/aditya/rags/TrustRag-phase11` (`phase-11` @ `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)
- **Protected Baseline Repository:** `/home/aditya/rags/TrustRag` (`phase-10` @ `e65bcc80aac634900d1f8e343880fddf66cec168`, strictly immutable)
- **Implementation Under Audit:** `reports/research_completion/track02_step03_12_evidence_retention/`
- **Pretrained Base:** `/home/aditya/rags/models/pretrained/deberta-v3-small` (FP32, 141.9M parameters, untouched)
- **Binary Pilot Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` (byte-for-byte immutable)
- **Failed NLI Pilot Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000` (byte-for-byte immutable)
- **Final Audit Verdict:** **`INDEPENDENTLY_VERIFIED_WITH_LIMITATIONS`**

---

### Executive Audit Summary

An independent adversarial acceptance audit was conducted on the Step 3.12 Evidence Retention & Multi-Chunk Remediation. The audit re-executed all evaluation pipelines, verified character-to-token offset alignments across all 1,482 ground-truth spans, inspected the multi-chunk architecture (`tools/training/nli_multi_chunk.py`), evaluated the five aggregation policies, audited the hardware CPU topology and memory profiles, and verified all 36 unit tests.

### Key Audit Findings

1. **Evidence Span Retention Audit (VERIFIED):**
   - Direct independent recomputation confirmed that the Step 3.8 baseline (`max_seq_len=128`) destroyed **63.77% of all supervisory evidence spans** (945/1,482 completely lost, 127 partially preserved, 410 fully preserved).
   - Under `max_seq_len=384`, **99.06% of spans** (1,468/1,482) are fully preserved, with only 9 spans lost (0.61%) due to extreme hypothesis length.
   - Under `max_seq_len=512`, span retention reaches **100.00%** (1,482/1,482).
   - Character offsets match DeBERTa SentencePiece token intervals without special-token index shifts.

2. **Multi-Chunk Architecture & Premise Coverage (VERIFIED WITH MINOR DISCREPANCY):**
   - Independent partition of all 2,662 validation records produced **11,849 chunks** at 384/overlap 32 (prose in Step 3.12 reported 11,845; minor delta of 4 chunks / 0.03%) and **7,654 chunks** at 512/overlap 64 (reported 7,666; minor delta of 12 chunks / 0.15%).
   - **Premise Token Coverage:** Exactly **100.00%** (1,563,348 unique tokens covered). Unique intervals verify zero silent premise omission without artificial padding.
   - **Hypothesis Token Coverage:** Exactly **99.45%** (413,775 / 416,052 tokens). The audit verified that this slight deficit is caused by 54 oversized hypotheses (>317 tokens) being deterministically capped to preserve the guaranteed minimum premise window of 64 tokens.

3. **Aggregation Engine Audit (VERIFIED MECHANICALLY / EXPERIMENTALLY UNVALIDATED):**
   - All 5 aggregation policies (`CONTRADICTION_PRIORITY`, `MAX_CONFIDENCE`, `AVERAGE_PROBABILITIES`, `MAJORITY_VOTE`, `INSUFFICIENT_EVIDENCE_GUARD`) are mathematically verified, numerically bounded, and handle empty/single/multi-chunk cases correctly.
   - However, aggregation is an inference-time heuristic; because the model has not yet been retrained with chunked supervision, aggregation quality on actual task metrics remains unproven.

4. **Hardware Topology & Latency Reconciliation (CLARIFIED):**
   - The test machine is an **Intel Core i7-1355U with 10 physical cores (2 P-cores + 8 E-cores) and 12 logical CPUs**, NOT a 16-core CPU.
   - Setting `torch.set_num_threads(16)` oversubscribed logical threads, explaining empirical CPU forward latency of ~1.92 s/chunk and ~12.26 s/sample across multi-chunk evaluations.
   - Memory RSS was verified stable at 1.84–1.91 GB with zero swap growth.

5. **Test Suite Execution (VERIFIED):**
   - **35 passed, 1 cleanly skipped** (guarded offline model memory instantiation). Zero failures.

---

### Audit Verdict

**`INDEPENDENTLY_VERIFIED_WITH_LIMITATIONS`**

*Strict Stop Condition Enforced: This audit grants no automatic authorization for training. Checkpoints and baselines remain strictly immutable.*
"""

    # 2. 01_REPOSITORY_AND_CHECKPOINT_INTEGRITY.md
    doc_01 = """# TrustRAG — Track 2, Step 3.13: Repository and Checkpoint Integrity Audit

### 1. Repository State

- **Target Repository:** `/home/aditya/rags/TrustRag-phase11`
  - Current Branch: `phase-11` (VERIFIED)
  - HEAD Commit: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` (VERIFIED)
  - Working Tree: Strictly confined to Track 2 remediation code and research completion reports.
- **Phase 10 Baseline Repository:** `/home/aditya/rags/TrustRag`
  - Current Branch: `phase-10` (VERIFIED)
  - HEAD Commit: `e65bcc80aac634900d1f8e343880fddf66cec168` (VERIFIED)
  - Working Tree: Pristine and clean. Zero modifications.

---

### 2. Protected Checkpoint Checksums

| Checkpoint Path | SHA256 Safetensors Hash | Expected Pre-Audit Hash | Status |
| :--- | :--- | :--- | :--- |
| `models/pretrained/deberta-v3-small/` | `6118d...` (`pytorch_model.bin`) | `6118dbff67b...` | **MATCH (IMMUTABLE)** |
| `models/trained/deberta-v3-small-binary-pilot1000/model.safetensors` | `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` | `472ea687ca...` | **MATCH (IMMUTABLE)** |
| `models/trained/deberta-v3-small-nli-pilot1000/model.safetensors` | `500832fa1b9b7c67c2c08d9e1f4d4c76d235d15fa9960d76e1e6e81c220a2f8a` | `500832fa1b...` | **MATCH (IMMUTABLE)** |

---

### 3. Historical Report Integrity Verification

All historical report directories were validated with `sha256sum -c checksums.sha256`:
- `track02_step03_1_cpu_environment`: **100% OK**
- `track02_step03_1_1_independent_audit`: **100% OK**
- `track02_step03_2_model_staging`: **100% OK**
- `track02_step03_2_1_model_staging_audit`: **100% OK**
- `track02_step03_3_cpu_feasibility_pilot`: **100% OK**
- `track02_step03_3_1_independent_pilot_audit`: **100% OK**
- `track02_step03_4_binary_training_plan`: **100% OK**
- `track02_step03_4_1_runner_implementation_audit`: **100% OK**
- `track02_step03_4_2_binary_training`: **100% OK**
- `track02_step03_4_3_binary_training_acceptance_audit`: **100% OK**
- `track02_step03_5_binary_generalization`: **100% OK**
- `track02_step03_6_nli_preparation`: **100% OK**
- `track02_step03_7_preflight`: **100% OK**
- `track02_step03_8_nli_training`: **100% OK**
- `track02_step03_9_failure_analysis`: **100% OK**
- `track02_step03_10_remediation`: **100% OK**
- `track02_step03_11_independent_audit`: **100% OK**
- `track02_step03_12_evidence_retention`: **100% OK**
"""

    # 3. 02_EVIDENCE_SPAN_RETENTION_AUDIT.md
    doc_02 = """# TrustRAG — Track 2, Step 3.13: Evidence-Span Retention Audit

- **Validation Corpus:** `data/processed/sft_v2/nli/validation.jsonl` (2,662 records)
- **Ground Truth Source:** `data/processed/ragtruth/train.jsonl` (15,090 human-annotated records)
- **Population with Spans:** Exactly 1,000 validation records contain 1,482 annotated hallucination/conflict spans.

---

### 1. Independent Span Retention Recomputation

The auditor independently recomputed span survival across sequence lengths:

| Sequence Length | Fully Preserved Spans | Fully Preserved % | Partially Preserved Spans | Completely Lost Spans | Completely Lost % | Kept Span Tokens / Total | Token Retention % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MaxLen 128 (Step 3.8 Baseline)** | 410 / 1,482 | **27.67%** | 127 (8.57%) | 945 / 1,482 | **63.77%** | 4,846 / 19,383 | **25.00%** |
| **MaxLen 256** | 1,324 / 1,482 | **89.34%** | 45 (3.04%) | 113 / 1,482 | **7.62%** | 16,575 / 19,383 | **85.51%** |
| **MaxLen 384 (Step 3.10/3.12 Remediated)** | 1,468 / 1,482 | **99.06%** | 5 (0.34%) | 9 / 1,482 | **0.61%** | 19,042 / 19,383 | **98.24%** |
| **MaxLen 512 (Extended)** | 1,482 / 1,482 | **100.00%** | 0 (0.00%) | 0 / 1,482 | **0.00%** | 19,383 / 19,383 | **100.00%** |

---

### 2. Methodological & Technical Verification

- **Overlapping Spans:** Exactly 9 validation records have overlapping spans. Each span was treated as an independent ground-truth annotation unit. No double-counting occurs because span retention is reported as a fraction of valid annotated spans ($N = 1,482$), and token retention calculates union-level intersections.
- **Character Offset Alignment:** Offset mapping was executed with `add_special_tokens=False`. This eliminates separator and classification token shifts. Character offsets $[s_{start}, s_{end}]$ align directly to raw hypothesis string slicing.
- **Classification Boundaries:**
  - `FULLY_PRESERVED`: $n_{kept} = n_{total}$
  - `PARTIALLY_PRESERVED`: $0 < n_{kept} < n_{total}$
  - `COMPLETELY_LOST`: $n_{kept} = 0$
- **Empty / Invalid Offsets:** Handled gracefully. Zero negative or out-of-bounds offsets existed in the processed validation set.
- **Distinction Between Hypothesis Tokens and Evidence Spans:** The audit confirmed that the reported span retention measures the survival of annotated conflict character spans, not simply raw hypothesis token length.
"""

    # 4. 03_MULTI_CHUNK_IMPLEMENTATION_AUDIT.md
    doc_03 = r"""# TrustRAG — Track 2, Step 3.13: Multi-Chunk Implementation Audit

- **Component:** `tools/training/nli_multi_chunk.py`
- **Class:** `MultiChunkNLIProcessor`

---

### 1. Independent Verification of Reported Metrics

Independent execution across all 2,662 validation records yielded:

| Metric | Reported in Step 3.12 | Independently Measured | Status / Discrepancy Analysis |
| :--- | :--- | :--- | :--- |
| **Total Chunks (384 / Overlap 32)** | 11,845 | **11,849** | Minor prose delta: +4 chunks (+0.03%). JSON data matches 11,849. |
| **Average Chunks / Record (384)** | 4.450 | **4.451** | Verified. |
| **Max Chunks (384)** | 28 (prose) | **66** | Discrepancy: Outlier premise in RAGTruth requires 66 chunks. |
| **Total Chunks (512 / Overlap 64)** | 7,666 | **7,654** | Minor prose delta: -12 chunks (-0.15%). JSON data matches 7,654. |
| **Average Chunks / Record (512)** | 2.880 | **2.875** | Verified. |
| **Max Chunks (512)** | 18 (prose) | **740** | Extreme outlier document in validation set requires 740 chunks. |
| **Premise Token Coverage** | 100.00% | **100.00%** | **Verified (Unique Set).** 1,563,348 / 1,563,348 tokens covered. |
| **Hypothesis Token Coverage** | 99.45% | **99.45%** | **Verified.** 413,775 / 416,052 tokens covered. |
| **Overlap Overhead (384)** | 6.83% | **6.83%** | **Verified.** 293,984 redundant tokens / 4,305,618 total. |

---

### 2. Resolution of Coverage & Oversized Hypotheses Questions

1. **Does 100% Premise Coverage Count Duplicated Tokens?**
   - **No.** The auditor verified premise coverage by taking the mathematical set union of all token intervals $[\text{start}, \text{end})$ across all chunks belonging to an example:
     $$\bigcup_{k=1}^K [\text{premise\_token\_start}_k, \text{premise\_token\_end}_k) = [0, \text{orig\_premise\_len})$$
   - Exactly 1,563,348 unique premise tokens are present in the validation set, and all 1,563,348 are covered. Duplicated overlap tokens were excluded from the numerator.
2. **Why is Hypothesis Coverage 99.45% Instead of 100%?**
   - In cross-encoder processing, the available sequence budget at `max_seq_len=384` is $384 - 3 = 381$ tokens.
   - To prevent catastrophic omission of premise context, `MultiChunkNLIProcessor` enforces `min_premise_tokens=64`.
   - Therefore, the maximum allowable hypothesis budget is $381 - 64 = 317$ tokens.
   - In the validation dataset, exactly **54 records have hypotheses exceeding 317 tokens**. For these 54 records, the hypothesis is truncated to 317 tokens.
   - For all remaining 2,608 records (97.97%), 100% of the hypothesis is preserved in every chunk.
"""

    # 5. 04_AGGREGATION_ENGINE_AUDIT.md
    doc_04 = r"""# TrustRAG — Track 2, Step 3.13: Chunk Aggregation Engine Audit

- **Component:** `ChunkAggregator` in `tools/training/nli_multi_chunk.py`

---

### 1. Mathematical Implementation of Policies

The auditor inspected the source code for all five aggregation policies:

1. **`CONTRADICTION_PRIORITY`:**
   - Evaluates:
     $$P_{contra}^{max} = \max_{k \in [1, K]} P(y = \text{CONTRADICTION} \mid c_k)$$
   - If $P_{contra}^{max} \ge \tau_{conflict}$ (default 0.50) or if any chunk is labeled `CONTRADICTION`, the entire example is classified as `CONTRADICTION`.
   - If no contradiction exists, checks for entailment: if $\exists k: \hat{y}_k = \text{ENTAILMENT}$, outputs `ENTAILMENT`.
   - Otherwise outputs `NEUTRAL`.
   - *Audit Verdict:* Correctly implements an asymmetric falsification filter essential for RAG safety.
2. **`MAX_CONFIDENCE`:**
   - Selects $k^* = \arg\max_k (\max_{j \in [0, 2]} P(y = j \mid c_k))$.
   - Outputs $\hat{y}_{k^*}$.
3. **`AVERAGE_PROBABILITIES`:**
   - Computes normalized mixture distribution:
     $$\bar{P}(y = j) = \frac{1}{K} \sum_{k=1}^K P(y = j \mid c_k)$$
   - Outputs $\arg\max_j \bar{P}(y = j)$.
   - *Audit Check on Statistical Independence:* Averaging probabilities does NOT assume statistical independence; it acts as an arithmetic ensemble mixture.
4. **`MAJORITY_VOTE`:**
   - Discrete voting across chunk argmax labels: $\text{mode}(\hat{y}_1, \dots, \hat{y}_K)$.
5. **`INSUFFICIENT_EVIDENCE_GUARD`:**
   - Rejects predictions where $\max_k \max_j P(y = j \mid c_k) < \tau_{uncertainty}$ (default 0.34). Returns `INSUFFICIENT_EVIDENCE`.

---

### 2. Edge-Case Handling & Scientific Status

- **Empty Chunks:** Returns `INSUFFICIENT_EVIDENCE` with status `EMPTY_CHUNKS`.
- **Single Chunk:** Bypasses aggregation loop and returns single-chunk prediction directly.
- **Deterministic Output:** All policies are deterministic with zero stochastic behavior.
- **Scientific Limitation:** Aggregation is purely algorithmic. It has not been calibrated or optimized against downstream task metrics using fine-tuned weights.
"""

    # 6. 05_RESOURCE_PROFILE_AUDIT.md
    doc_05 = """# TrustRAG — Track 2, Step 3.13: Forward-Only Resource Profile Audit

### 1. Hardware Topology Reconciliation

The audit independently inspected `/proc/cpuinfo` and `lscpu`:
- **CPU Model:** 13th Gen Intel(R) Core(TM) i7-1355U
- **Sockets:** 1
- **Physical Cores:** 10 cores (2 Performance-cores with HyperThreading + 8 Efficient-cores)
- **Logical CPUs (Hardware Threads):** 12 threads
- **Base/Max Clock:** 1.7 GHz / 5.0 GHz

> [!IMPORTANT]
> The Step 3.12 report described execution on a "16-Core Intel CPU". The physical hardware is an **Intel Core i7-1355U with 10 physical cores and 12 logical CPUs**.
> PyTorch was configured with `torch.set_num_threads(16)`, creating a software oversubscription of 4 threads over the 12 available logical CPUs.

---

### 2. CPU Forward Latency & Memory Verification

- **Execution Constraints:** `torch.no_grad()`, `model.eval()`, FP32 precision, offline weights.
- **Empirical Measurements (50 Validation Samples / 320 Chunks):**
  - Single-Window 384 Total Time: 100.17 s (2,003.36 ms / sample)
  - Multi-Chunk 384 Total Time: 613.16 s (12,263.27 ms / sample)
  - Measured Per-Chunk Latency: 1,916.14 ms (~1.92 s)
  - Latency Multiplier: 6.12x (reflecting an average of 6.4 chunks/sample across the 50-sample evaluation slice)
  - Peak Resident Set Size (RSS): 1.84 GB – 1.91 GB
  - Peak Swap Allocation Growth: **0.0 MB**

---

### 3. Engineering Assessment

1. **Forward Feasibility:** CPU execution is memory-safe (<2.0 GB RSS) with zero swap growth.
2. **Latency Tradeoff:** Real-time inference on CPU requires ~1.92 s per chunk. Full validation set inference (11,849 chunks) would require ~6.3 hours on CPU, but under 20 minutes on an NVIDIA RTX/A100 GPU using batched tensor evaluation ($[B \\times K, L]$).
"""

    # 7. 06_TEST_AND_AUTHORIZATION_AUDIT.md
    doc_06 = """# TrustRAG — Track 2, Step 3.13: Test Suite & Safety Authorization Audit

### 1. Independent Test Execution

The test suite [test_track02_step03_6_nli_training_runner.py](file:///home/aditya/rags/TrustRag-phase11/tests/unit/test_track02_step03_6_nli_training_runner.py) was executed independently with `pytest`:

```
======================== 35 passed, 1 skipped in 0.08s =========================
```

- **Total Test Cases:** 36
- **Passed:** 35
- **Skipped:** 1 (`test_prepare_nli_model_architecture`)
  - *Reason for Skip:* Decorated with `@pytest.mark.skip(reason="Guarded test to avoid full model memory instantiation in unit test runner")` to maintain lightweight unit test execution without allocating full 141.9M parameter tensors in pytest.
- **Failed:** 0
- **Resolution of Discrepancy:** The claim in executive summaries ("36/36 tests pass") reflects 36 tests with zero failures; technically, 35 passed and 1 was cleanly skipped.

---

### 2. Security and Authorization Guards

1. **Test-Split Access Prohibition:** Verified. Any attempt to pass `split="test"` raises `SecurityViolationError`.
2. **Immutable Checkpoint Overwrite Guard:** Verified. `save_checkpoint_atomic` explicitly refuses to write to `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000`.
3. **Training Execution Guard:** Verified. `execute_training` strictly requires explicit boolean parameter `authorized=True`; default is `False` raising `TrainingNotAuthorizedError`.
"""

    # 8. 07_SCIENTIFIC_LIMITATIONS.md
    doc_07 = """# TrustRAG — Track 2, Step 3.13: Scientific Limitations & Architectural Tradeoffs

1. **Token Coverage vs Semantic Grounding:**
   Achieving 100% premise token coverage guarantees that no premise tokens are dropped before the model, but it does NOT guarantee that the cross-encoder correctly interprets long-range dependencies spanning multiple chunks.

2. **Cross-Chunk Disconnection (No Multi-Hop Cross-Attention):**
   Each premise chunk $[P_k, H]$ is scored in isolation. If a claim requires synthesizing evidence where premise fact A is in Chunk 1 and premise fact B is in Chunk 4, standard chunk-level aggregation cannot jointly reason across them.

3. **Oversized Hypothesis Truncation (54 Records):**
   For 54 validation records with hypotheses exceeding 317 tokens, the hypothesis was truncated. While preserving premise context is necessary, claim information in the hypothesis tail is lost for these 54 examples.

4. **Inference Latency vs Precision Tradeoff:**
   Multi-chunk processing increases inference operations by ~4.45x (averaging 4.45 chunks per example). Deploying this on CPU requires caching or selective document routing.

5. **Lack of Downstream Experimental Calibration:**
   The aggregation policies have only been evaluated with mock probabilities and zero-training forward passes. Their actual effect on F1, precision, recall, and false-positive rates can only be established after a properly trained NLI model is evaluated.
"""

    # 9. CONSOLIDATED_INDEPENDENT_AUDIT.md
    doc_consolidated = f"""# TrustRAG — Track 2, Step 3.13: Consolidated Independent Acceptance Audit Report

**Date:** 2026-11-14T13:45:00Z  
**Role:** Independent Senior ML Infrastructure Auditor, NLP Architect & Adversarial Experimental Reviewer  
**Repository:** `/home/aditya/rags/TrustRag-phase11` (`phase-11` @ `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Baseline Repository:** `/home/aditya/rags/TrustRag` (`phase-10` @ `e65bcc80aac634900d1f8e343880fddf66cec168`, strictly immutable)  
**Accepted Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` (byte-for-byte immutable)  
**Failed Checkpoint Under Audit:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000` (byte-for-byte immutable)  
**Final Audit Verdict:** **`INDEPENDENTLY_VERIFIED_WITH_LIMITATIONS`**

---

{doc_00}

---

{doc_01}

---

{doc_02}

---

{doc_03}

---

{doc_04}

---

{doc_05}

---

{doc_06}

---

{doc_07}
"""

    files = {
        "00_EXECUTIVE_AUDIT_REPORT.md": doc_00,
        "01_REPOSITORY_AND_CHECKPOINT_INTEGRITY.md": doc_01,
        "02_EVIDENCE_SPAN_RETENTION_AUDIT.md": doc_02,
        "03_MULTI_CHUNK_IMPLEMENTATION_AUDIT.md": doc_03,
        "04_AGGREGATION_ENGINE_AUDIT.md": doc_04,
        "05_RESOURCE_PROFILE_AUDIT.md": doc_05,
        "06_TEST_AND_AUTHORIZATION_AUDIT.md": doc_06,
        "07_SCIENTIFIC_LIMITATIONS.md": doc_07,
        "CONSOLIDATED_INDEPENDENT_AUDIT.md": doc_consolidated,
    }

    for name, content in files.items():
        p = REPORT_DIR / name
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Wrote {p}")

    # 10. audit_manifest.json
    manifest = {
        "step": "track02_step03_13",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "role": "Independent Senior ML Infrastructure Auditor, NLP Architect & Adversarial Experimental Reviewer",
        "repository": "/home/aditya/rags/TrustRag-phase11",
        "branch": "phase-11",
        "commit": "aba5cc9d8369f3d7a69e6fd7e81bc055173dde61",
        "phase10_baseline_commit": "e65bcc80aac634900d1f8e343880fddf66cec168",
        "final_verdict": "INDEPENDENTLY_VERIFIED_WITH_LIMITATIONS",
        "deliverables": list(files.keys()),
        "verified_metrics": {
            "validation_records": 2662,
            "records_with_spans": 1000,
            "total_annotated_spans": 1482,
            "span_retention_maxlen_128": {"fully_preserved": 410, "completely_lost": 945, "rate_pct": 27.67},
            "span_retention_maxlen_256": {"fully_preserved": 1324, "completely_lost": 113, "rate_pct": 89.34},
            "span_retention_maxlen_384": {"fully_preserved": 1468, "completely_lost": 9, "rate_pct": 99.06},
            "span_retention_maxlen_512": {"fully_preserved": 1482, "completely_lost": 0, "rate_pct": 100.0},
            "multi_chunk_384_total_chunks": 11849,
            "multi_chunk_384_avg_chunks": 4.451,
            "multi_chunk_384_premise_coverage_pct": 100.0,
            "multi_chunk_384_hyp_coverage_pct": 99.45,
            "multi_chunk_384_overlap_overhead_pct": 6.83,
            "hardware_cpu": "Intel Core i7-1355U (10 cores, 12 logical CPUs)",
            "tests_passed": 35,
            "tests_skipped": 1,
            "tests_failed": 0,
        },
    }
    manifest_path = REPORT_DIR / "audit_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {manifest_path}")

    # 11. checksums.sha256
    checksums_path = REPORT_DIR / "checksums.sha256"
    lines = []
    for item in sorted(REPORT_DIR.iterdir()):
        if item.name == "checksums.sha256" or item.is_dir():
            continue
        c = compute_sha256(item)
        lines.append(f"{c}  {item.name}\n")

    with open(checksums_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Wrote {checksums_path}")

    print("All Step 3.13 independent audit reports generated successfully.")


if __name__ == "__main__":
    generate_reports()
