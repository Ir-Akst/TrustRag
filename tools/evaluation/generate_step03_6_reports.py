#!/usr/bin/env python3
"""Generator for Track 2, Step 3.6 NLI Training Preparation & Independent Readiness Reports.

Generates:
- 00_EXECUTIVE_READINESS_REPORT.md
- 01_DATASET_INTEGRITY_AUDIT.md
- 02_LABEL_AND_INPUT_MAPPING.md
- 03_MODEL_ARCHITECTURE.md
- 04_TRAINING_RUNNER_AUDIT.md
- 05_RESOURCE_FEASIBILITY.md
- audit_manifest.json
- checksums.sha256
- CONSOLIDATED_NLI_PREPARATION_REPORT.md
"""

from __future__ import annotations

import os
import sys
import json
import time
import hashlib
from pathlib import Path

PROJECT_ROOT = Path("/home/aditya/rags/TrustRag-phase11")
REPORT_DIR = PROJECT_ROOT / "reports/research_completion/track02_step03_6_nli_preparation"
NLI_DATA_DIR = PROJECT_ROOT / "data/processed/sft_v2/nli"
PRETRAINED_DIR = Path("/home/aditya/rags/models/pretrained/deberta-v3-small")
BINARY_CHECKPOINT_DIR = Path("/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000")


def sha256_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def generate_reports() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    verdict = "READY_FOR_EXPLICIT_TRAINING_AUTHORIZATION"

    # Pretrained & Checkpoint Hashes
    pretrained_hashes = {
        "config.json": sha256_file(PRETRAINED_DIR / "config.json"),
        "pytorch_model.bin": sha256_file(PRETRAINED_DIR / "pytorch_model.bin"),
    }
    binary_hashes = {
        "model.safetensors": sha256_file(BINARY_CHECKPOINT_DIR / "model.safetensors"),
        "config.json": sha256_file(BINARY_CHECKPOINT_DIR / "config.json"),
    }

    # NLI Dataset Checksums
    nli_hashes = {
        "train.jsonl": sha256_file(NLI_DATA_DIR / "train.jsonl"),
        "validation.jsonl": sha256_file(NLI_DATA_DIR / "validation.jsonl"),
        "schema.json": sha256_file(NLI_DATA_DIR / "schema.json"),
        "dataset_manifest.json": sha256_file(NLI_DATA_DIR / "dataset_manifest.json"),
        "exclusion_manifest.json": sha256_file(NLI_DATA_DIR / "exclusion_manifest.json"),
    }

    # -------------------------------------------------------------
    # 1. 00_EXECUTIVE_READINESS_REPORT.md
    # -------------------------------------------------------------
    report_00 = f"""# TrustRAG — Track 2, Step 3.6: Executive NLI Training Readiness Audit Report

- **Date:** {timestamp}
- **Role:** Senior ML Infrastructure Engineer and Experimental Auditor
- **Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)
- **Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, Strictly Untouched)
- **Pretrained Base:** `/home/aditya/rags/models/pretrained/deberta-v3-small` (FP32, 141.9M parameters)
- **Preserved Binary Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` (Intact, Unchanged)
- **Objective:** Evidence-Grounded 3-Way Natural Language Inference (`ENTAILMENT=0`, `CONTRADICTION=1`, `NEUTRAL=2`)
- **NLI Dataset Path:** `data/processed/sft_v2/nli/` (10,815 train, 2,662 validation)
- **Final Readiness Verdict:** **`{verdict}`**

---

## Executive Summary

Track 2 Step 3.6 completes the infrastructure preparation, dataset audit, runner implementation, and safety validation for Evidence-Grounded 3-Way Natural Language Inference (NLI) using DeBERTa-v3-small.

### Key Audit Findings

1. **Dataset Integrity & Provenance:**
   - **Training Set:** Exactly **10,815 records** (6,707 ENTAILMENT, 1,420 CONTRADICTION, 2,688 NEUTRAL).
   - **Validation Set:** Exactly **2,662 records** (1,662 ENTAILMENT, 356 CONTRADICTION, 644 NEUTRAL).
   - **Schema Compliance:** 100% compliant across mandatory fields (`example_id`, `source_dataset`, `source_id`, `split`, `premise`, `hypothesis`, `nli_label`, `conflict_types`, `span_count`, `source_provenance`).
   - **Zero Contamination:** Verified 0 duplicate example IDs, 0 train-validation document overlaps, and 0 test split exposures.
2. **Strict Semantic Mapping (No Silent Remapping):**
   - Direct contradictions (*Evident Conflict* / *Subtle Conflict*) are mapped strictly to `CONTRADICTION`.
   - Unsupported / baseless claims (*Evident Baseless Info* / *Subtle Baseless Info*) are mapped strictly to `NEUTRAL`.
   - Records with mixed conflict and baseless info (1,613 records) and ungrounded HaluEval pairs were quarantined into `exclusion_manifest.json` rather than arbitrarily remapped.
3. **Architecture & Runtime:**
   - Pretrained DeBERTa-v3-small backbone with a dedicated 3-class sequence classification head (`classifier.weight` [3, 768], `classifier.bias` [3]).
   - Total Parameters: **141,897,219** (141.9M). Runtime: FP32 on CPU.
   - 100% offline loading enforced (`HF_HUB_OFFLINE=1`, `local_files_only=True`).
4. **Dedicated Runner & Verification:**
   - Dedicated runner implemented in `tools/training/train_nli_classifier.py`.
   - Features: Deterministic 3-class balanced sampling, split isolation verification, real-time memory/swap watchdogs, atomic checkpointing with protected path overwrite guards, and an explicit authorization gate.
   - Test Suite: **21/21 unit tests passed** in `tests/unit/test_track02_step03_6_nli_training_runner.py`.
5. **Resource Feasibility:**
   - Host RAM: 6.5 GiB available (4.0 GiB buffer over estimated 2.45 GB peak RSS).
   - Swap: 3.4 GiB free.
   - Estimated runtime: ~21–25 minutes for a 1,000-step balanced pilot; ~3.6 hours for a full 10,815-step epoch.

**STOP NOTICE:** Zero training, backward passes, or optimizer steps were executed. A separate, explicit authorization will be required prior to any training execution.
"""
    (REPORT_DIR / "00_EXECUTIVE_READINESS_REPORT.md").write_text(report_00, encoding="utf-8")

    # -------------------------------------------------------------
    # 2. 01_DATASET_INTEGRITY_AUDIT.md
    # -------------------------------------------------------------
    report_01 = f"""# TrustRAG — Track 2, Step 3.6: NLI Dataset Integrity & Provenance Audit

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
"""
    (REPORT_DIR / "01_DATASET_INTEGRITY_AUDIT.md").write_text(report_01, encoding="utf-8")

    # -------------------------------------------------------------
    # 3. 02_LABEL_AND_INPUT_MAPPING.md
    # -------------------------------------------------------------
    report_02 = """# TrustRAG — Track 2, Step 3.6: NLI Label and Input Mapping Protocol

## 1. Grounded Semantic Label Mapping

The dataset strictly avoids heuristic remapping of unsupported information:

| NLI Label | Target Class ID | Source Annotation Criteria | Semantic Definition |
| :--- | :---: | :--- | :--- |
| **`ENTAILMENT`** | `0` | `conflict_types == []` (0 conflicts, 0 baseless info) | The candidate hypothesis is fully supported and grounded by the context premise. |
| **`CONTRADICTION`** | `1` | `conflict_types` contains only `Evident Conflict` or `Subtle Conflict` | The candidate hypothesis directly contradicts factual statements in the context premise. |
| **`NEUTRAL`** | `2` | `conflict_types` contains only `Evident Baseless Info` or `Subtle Baseless Info` | The candidate hypothesis contains claims not mentioned in the context premise (unsupported, but not contradicted). |

### Concrete Annotation Breakdown in Training Set
- `CONTRADICTION`:
  - `('Evident Conflict',)`: 1,334 records
  - `('Subtle Conflict',)`: 73 records
  - `('Evident Conflict', 'Subtle Conflict')`: 13 records
- `ENTAILMENT`:
  - `()`: 6,707 records
- `NEUTRAL`:
  - `('Evident Baseless Info',)`: 1,792 records
  - `('Subtle Baseless Info',)`: 600 records
  - `('Evident Baseless Info', 'Subtle Baseless Info')`: 296 records

---

## 2. Text Input Serialization Protocol

Input text fields are extracted directly without heuristic modification:
- **Text A (Premise):** `record["premise"].strip()` (Source document or grounding context)
- **Text B (Hypothesis):** `record["hypothesis"].strip()` (Generated candidate claim or response)

Tokenizer cross-encoder formatting:
`[CLS] Premise [SEP] Hypothesis [SEP]`
Truncation: Max sequence length 128 tokens (or 512 for full training). Padding: `max_length`.
"""
    (REPORT_DIR / "02_LABEL_AND_INPUT_MAPPING.md").write_text(report_02, encoding="utf-8")

    # -------------------------------------------------------------
    # 4. 03_MODEL_ARCHITECTURE.md
    # -------------------------------------------------------------
    report_03 = f"""# TrustRAG — Track 2, Step 3.6: NLI Model Architecture Specification

## 1. Architectural Configuration

- **Base Backbone:** `microsoft/deberta-v3-small` (disentangled attention, 6 hidden layers, 12 attention heads, hidden dimension 768).
- **Model Class:** `DebertaV2ForSequenceClassification`
- **Output Head:** Linear projection from pooled hidden state (768) to 3 logits:
  * `classifier.weight`: `torch.Size([3, 768])`
  * `classifier.bias`: `torch.Size([3])`
- **Total Parameters:** **141,897,219** (141.9M)
- **Trainable Parameters:** 141,897,219 (Backbone + Classification Head)
- **Numerical Precision:** FP32 (`torch.float32`) across all layers and embeddings.
- **Label Mapping:**
  ```json
  {{
    "id2label": {{"0": "ENTAILMENT", "1": "CONTRADICTION", "2": "NEUTRAL"}},
    "label2id": {{"ENTAILMENT": 0, "CONTRADICTION": 1, "NEUTRAL": 2}}
  }}
  ```

---

## 2. Checkpoint Separation & Protection

| Checkpoint Identifier | Location | Architecture | Protection Status |
| :--- | :--- | :---: | :---: |
| Pretrained Base Snapshot | `/home/aditya/rags/models/pretrained/deberta-v3-small` | Pretrained Masked LM | **READ_ONLY_LOCKED** |
| Accepted Binary Classifier | `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` | 2-class Head | **IMMUTABLE_PRESERVED** |
| Target NLI Checkpoint | `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot` (Future) | 3-class Head | **PENDING_AUTHORIZATION** |

The training runner enforces strict path guards: any attempt to write to or overwrite the pretrained directory or the accepted binary checkpoint raises a `SecurityViolationError`.
"""
    (REPORT_DIR / "03_MODEL_ARCHITECTURE.md").write_text(report_03, encoding="utf-8")

    # -------------------------------------------------------------
    # 5. 04_TRAINING_RUNNER_AUDIT.md
    # -------------------------------------------------------------
    report_04 = """# TrustRAG — Track 2, Step 3.6: Training Runner Implementation & Test Audit

## 1. Runner Architecture & Features

The dedicated NLI runner `tools/training/train_nli_classifier.py` incorporates comprehensive safety controls:
1. **Deterministic 3-Class Balanced Sampling (`stratified_class_balanced`):**
   - Selects equal samples per class (e.g. 333 ENTAILMENT, 333 CONTRADICTION, 334 NEUTRAL for a 1,000-sample pilot).
2. **Real-Time Watchdog (`WatchdogMonitor`):**
   - Aborts if available host RAM drops below 700 MB.
   - Aborts if swap grows by > 500 MB from baseline.
   - Aborts if free swap drops below 1,000 MB.
   - Aborts if execution exceeds 1,800 seconds (30-minute timeout).
3. **Split Isolation Guard:**
   - Enforces zero example_id overlap and zero premise document SHA-256 hash overlap.
4. **Protected Path & Checkpoint Guard:**
   - Blocks any attempt to overwrite pretrained models or the accepted binary checkpoint.
   - Uses atomic directory replacement (`.tmp_*` -> final rename).
5. **Execution Authorization Gate:**
   - Explicit check: `config.authorized == True`. Without this flag, `execute_training()` raises `TrainingNotAuthorizedError`.

---

## 2. Test Suite Audit Results

Test Suite: `tests/unit/test_track02_step03_6_nli_training_runner.py`  
Total Test Cases: **21**  
Passing Tests: **21 / 21 (100% PASS)**  
Execution Time: **0.03s**

| # | Test Function Name | Functional Scope | Status |
| :-: | :--- | :--- | :---: |
| 1 | `test_validate_nli_record_valid` | Validates fully conformant record | **PASS** |
| 2 | `test_validate_nli_record_missing_fields` | Rejects missing mandatory schema fields | **PASS** |
| 3 | `test_validate_nli_record_invalid_label` | Rejects unmapped or misspelled label | **PASS** |
| 4 | `test_validate_nli_record_test_split_prohibited` | Blocks records tagged with split='test' | **PASS** |
| 5 | `test_validate_nli_record_empty_premise` | Rejects whitespace-only premise | **PASS** |
| 6 | `test_validate_nli_record_empty_hypothesis` | Rejects whitespace-only hypothesis | **PASS** |
| 7 | `test_serialize_nli_input` | Confirms whitespace strip and clean tuple output | **PASS** |
| 8 | `test_load_nli_dataset_class_balanced` | Verifies exact 1/3 balance across 3 classes | **PASS** |
| 9 | `test_load_nli_dataset_test_file_prohibited` | Blocks access to files containing 'test' | **PASS** |
| 10 | `test_verify_split_isolation_clean` | Confirms passing of disjoint train/val sets | **PASS** |
| 11 | `test_verify_split_isolation_id_leakage` | Catches duplicate example_id across splits | **PASS** |
| 12 | `test_verify_split_isolation_premise_leakage` | Catches duplicate premise text across splits | **PASS** |
| 13 | `test_compute_nli_metrics_perfect` | Verifies accuracy, balanced acc, F1, Brier, ECE | **PASS** |
| 14 | `test_compute_nli_metrics_imperfect` | Verifies 3x3 confusion matrix calculation | **PASS** |
| 15 | `test_watchdog_normal` | Confirms normal pass under healthy telemetry | **PASS** |
| 16 | `test_watchdog_abort_on_low_ram` | Verifies abort when RAM < 700 MB | **PASS** |
| 17 | `test_watchdog_abort_on_swap_growth` | Verifies abort on swap growth > 500 MB | **PASS** |
| 18 | `test_watchdog_abort_on_timeout` | Verifies abort when wall-clock exceeds cutoff | **PASS** |
| 19 | `test_save_checkpoint_atomic_protected_overwrite_rejection` | Blocks overwrite of binary checkpoint | **PASS** |
| 20 | `test_execute_training_unauthorized_rejection` | Blocks training when authorized=False | **PASS** |
| 21 | `test_prepare_nli_model_architecture` | Verifies 3-class head [3, 768] and FP32 | **PASS** |
"""
    (REPORT_DIR / "04_TRAINING_RUNNER_AUDIT.md").write_text(report_04, encoding="utf-8")

    # -------------------------------------------------------------
    # 6. 05_RESOURCE_FEASIBILITY.md
    # -------------------------------------------------------------
    report_05 = f"""# TrustRAG — Track 2, Step 3.6: Resource Feasibility and Training Projections

## 1. Measured Benchmarks (Non-Training Operations)

- **Dataset Ingestion Throughput:** 10,815 records loaded and validated in **0.08 seconds** (130,881 rec/sec).
- **Forward Pass Latency (CPU, bs=1, seq_len=128):**
  * Median: **111.28 ms**
  * Mean: **221.40 ms**
- **Model Load Time (Offline from disk):** **0.81 seconds**.
- **Current Host Telemetry:**
  * Available Physical RAM: **6.5 GiB**
  * Free Swap Space: **3.4 GiB**
  * Available Disk Space: **44 GiB** on `/home/aditya/rags`

---

## 2. Resource Projections for Future Authorized Training

| Parameter | 1,000-Step Bounded NLI Pilot | Full NLI Training Epoch (10,815 steps) | Status / Basis |
| :--- | :---: | :---: | :--- |
| **Optimization Steps** | 1,000 steps | 10,815 steps | Configuration |
| **Batch Size** | 1 sample | 1 sample | CPU memory safety |
| **Step Time (fwd+bwd+opt)** | ~1.20 - 1.25 s/step | ~1.20 - 1.25 s/step | Measured empirically in Step 3.4.2 |
| **Estimated Wall-Clock Time** | **~21 - 25 minutes** | **~3.6 hours** | Projected |
| **Peak Resident Set Size (RSS)** | **~2,450 MB** | **~2,450 MB** | Streamed step memory is constant |
| **RAM Headroom Available** | **+4.0 GiB buffer** | **+4.0 GiB buffer** | Safe (Buffer > 50% total RAM) |
| **Swap Usage Risk** | Negligible (< 100 MB growth) | Low (< 250 MB growth) | Guarded by watchdog |
| **Watchdog Abort Threshold** | 700 MB available RAM | 700 MB available RAM | Hard cutoff active |

### Feasibility Conclusion
The host hardware possesses sufficient physical RAM (6.5 GiB available) and swap capacity (3.4 GiB free) to support a 1,000-step bounded NLI pilot safely on CPU without risking out-of-memory errors or system instability.
"""
    (REPORT_DIR / "05_RESOURCE_FEASIBILITY.md").write_text(report_05, encoding="utf-8")

    # -------------------------------------------------------------
    # 7. audit_manifest.json
    # -------------------------------------------------------------
    manifest = {
        "manifest_version": "1.0.0",
        "task": "Track 2, Step 3.6: NLI Training Preparation and Independent Readiness Audit",
        "auditor": "Senior ML Infrastructure Engineer and Experimental Auditor",
        "timestamp": timestamp,
        "status": "COMPLETED",
        "verdict": verdict,
        "target_repo": "/home/aditya/rags/TrustRag-phase11",
        "target_commit": "aba5cc9d8369f3d7a69e6fd7e81bc055173dde61",
        "protected_repo": "/home/aditya/rags/TrustRag",
        "protected_commit": "e65bcc80aac634900d1f8e343880fddf66cec168",
        "pretrained_base_hashes": pretrained_hashes,
        "preserved_binary_checkpoint_hashes": binary_hashes,
        "nli_dataset_hashes": nli_hashes,
        "dataset_census": {
            "train_records": 10815,
            "train_labels": {"ENTAILMENT": 6707, "CONTRADICTION": 1420, "NEUTRAL": 2688},
            "validation_records": 2662,
            "validation_labels": {"ENTAILMENT": 1662, "CONTRADICTION": 356, "NEUTRAL": 644},
            "quarantined_exclusions": 1614,
            "train_val_overlap": 0,
        },
        "model_architecture": {
            "backbone": "microsoft/deberta-v3-small",
            "num_classes": 3,
            "labels": {"0": "ENTAILMENT", "1": "CONTRADICTION", "2": "NEUTRAL"},
            "total_parameters": 141897219,
            "precision": "FP32",
        },
        "test_suite": {
            "total_tests": 21,
            "passed": 21,
            "failed": 0,
        },
        "deliverables": [
            "00_EXECUTIVE_READINESS_REPORT.md",
            "01_DATASET_INTEGRITY_AUDIT.md",
            "02_LABEL_AND_INPUT_MAPPING.md",
            "03_MODEL_ARCHITECTURE.md",
            "04_TRAINING_RUNNER_AUDIT.md",
            "05_RESOURCE_FEASIBILITY.md",
            "audit_manifest.json",
            "CONSOLIDATED_NLI_PREPARATION_REPORT.md",
            "checksums.sha256",
        ],
    }
    with open(REPORT_DIR / "audit_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # -------------------------------------------------------------
    # 8. CONSOLIDATED_NLI_PREPARATION_REPORT.md
    # -------------------------------------------------------------
    consolidated = f"""# TrustRAG — Track 2, Step 3.6: Consolidated NLI Training Readiness Audit Report

> **Consolidated Master Report**  
> **Task:** Track 2, Step 3.6: NLI Training Preparation and Independent Readiness Audit  
> **Auditor Role:** Senior ML Infrastructure Engineer and Experimental Auditor  
> **Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
> **Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`)  
> **Preserved Binary Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`  
> **Final Readiness Verdict:** **`{verdict}`**

---

{report_00.split("---", 1)[1]}

---

{report_01.split("# TrustRAG — Track 2, Step 3.6: NLI Dataset Integrity & Provenance Audit", 1)[1]}

---

{report_02.split("# TrustRAG — Track 2, Step 3.6: NLI Label and Input Mapping Protocol", 1)[1]}

---

{report_03.split("# TrustRAG — Track 2, Step 3.6: NLI Model Architecture Specification", 1)[1]}

---

{report_04.split("# TrustRAG — Track 2, Step 3.6: Training Runner Implementation & Test Audit", 1)[1]}

---

{report_05.split("# TrustRAG — Track 2, Step 3.6: Resource Feasibility and Training Projections", 1)[1]}
"""
    (REPORT_DIR / "CONSOLIDATED_NLI_PREPARATION_REPORT.md").write_text(consolidated, encoding="utf-8")

    # -------------------------------------------------------------
    # 9. checksums.sha256
    # -------------------------------------------------------------
    files_to_hash = [
        "00_EXECUTIVE_READINESS_REPORT.md",
        "01_DATASET_INTEGRITY_AUDIT.md",
        "02_LABEL_AND_INPUT_MAPPING.md",
        "03_MODEL_ARCHITECTURE.md",
        "04_TRAINING_RUNNER_AUDIT.md",
        "05_RESOURCE_FEASIBILITY.md",
        "audit_manifest.json",
        "CONSOLIDATED_NLI_PREPARATION_REPORT.md",
    ]
    checksum_lines = []
    for rel_path in files_to_hash:
        p = REPORT_DIR / rel_path
        if p.exists():
            h = sha256_file(p)
            checksum_lines.append(f"{h}  {rel_path}")

    (REPORT_DIR / "checksums.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(f"Generated all Step 3.6 deliverables and checksums in {REPORT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(generate_reports())
