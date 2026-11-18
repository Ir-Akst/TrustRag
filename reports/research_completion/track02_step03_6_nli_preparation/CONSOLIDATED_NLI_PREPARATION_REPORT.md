# TrustRAG — Track 2, Step 3.6: Consolidated NLI Training Readiness Audit Report

> **Consolidated Master Report**  
> **Task:** Track 2, Step 3.6: NLI Training Preparation and Independent Readiness Audit  
> **Auditor Role:** Senior ML Infrastructure Engineer and Experimental Auditor  
> **Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
> **Protected Repository:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`)  
> **Preserved Binary Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`  
> **Final Readiness Verdict:** **`READY_FOR_EXPLICIT_TRAINING_AUTHORIZATION`**

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


---



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


---



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


---



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
  {
    "id2label": {"0": "ENTAILMENT", "1": "CONTRADICTION", "2": "NEUTRAL"},
    "label2id": {"ENTAILMENT": 0, "CONTRADICTION": 1, "NEUTRAL": 2}
  }
  ```

---

## 2. Checkpoint Separation & Protection

| Checkpoint Identifier | Location | Architecture | Protection Status |
| :--- | :--- | :---: | :---: |
| Pretrained Base Snapshot | `/home/aditya/rags/models/pretrained/deberta-v3-small` | Pretrained Masked LM | **READ_ONLY_LOCKED** |
| Accepted Binary Classifier | `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` | 2-class Head | **IMMUTABLE_PRESERVED** |
| Target NLI Checkpoint | `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot` (Future) | 3-class Head | **PENDING_AUTHORIZATION** |

The training runner enforces strict path guards: any attempt to write to or overwrite the pretrained directory or the accepted binary checkpoint raises a `SecurityViolationError`.


---



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


---



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

