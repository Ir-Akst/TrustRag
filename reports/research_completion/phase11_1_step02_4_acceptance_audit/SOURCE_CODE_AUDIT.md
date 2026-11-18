# TrustRAG — Phase 11.1, Step 2.4: Independent Source Code Audit

**Date:** 2026-11-15  
**Auditor:** Independent Senior ML Systems Auditor  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**Commit HEAD:** `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`  
**Audit Scope:** Independent inspection of Step 2.3 changes across:
1. `tools/training/train_nli_classifier.py`
2. `tests/unit/test_phase11_step02_3_harness_remediation.py`

---

## 1. Summary of Changes Under Audit

The Step 2.3 changes introduced training infrastructure improvements to ensure fault tolerance, eliminate false-positive watchdog terminations, and optimize CPU execution without executing model training:

1. **`NLITrainingConfig` & CLI Interface:**
   - Added parameters: `checkpoint_every_steps` (default: 500), `keep_last_n_checkpoints` (default: 2), `resume_from_checkpoint` (default: None), `auto_resume` (default: True), `ram_abort_threshold_mb` (default: 700.0), `swap_free_min_mb` (default: 1000.0), `max_process_rss_mb` (default: 4500.0), `watchdog_consecutive_violations` (default: 3), `swap_growth_abort_mb` (default: None), `num_threads` (default: 10), `interop_threads` (default: 1), `dynamic_padding` (default: True).
   - Config validation and security bounds checks against `PROTECTED_PATHS` remain active.

2. **Watchdog Redesign (`WatchdogMonitor`):**
   - Replaced single-point swap-growth abort with multi-tier floor monitoring: RAM floor (700 MB), swap floor (1,000 MB), process RSS ceiling (4,500 MB).
   - Added consecutive violations smoothing counter (`consecutive_violations_threshold = 3`).
   - Integrated `emergency_save_fn` trigger prior to exception propagation.

3. **Atomic Checkpointing Subsystem:**
   - Implemented `save_checkpoint_state`: writes to `.tmp_<name>_<timestamp>`, serializes model, optimizer, scheduler, multi-engine RNG (`torch`, `numpy`, `python`), metadata, computes SHA-256 manifest, and atomically renames to target directory.
   - Implemented `verify_checkpoint_integrity`: verifies file existence and SHA-256 cryptographic digests before allowing checkpoint load.
   - Implemented `load_checkpoint_state`: verifies integrity, loads weights, optimizer, scheduler, and RNG state.
   - Implemented `_safe_torch_load`: safely handles PyTorch 2.6+ `weights_only=False` requirement for unpickling optimizer and RNG state dictionaries.
   - Implemented `prune_old_checkpoints`: retains the last $N$ step checkpoints while protecting emergency and best checkpoints.

4. **CPU Threading and Dynamic Padding:**
   - Environment initialization calls `torch.set_num_threads(10)` and `torch.set_num_interop_threads(1)` at the start of `execute_training`.
   - `evidence_preserving_tokenize` supports `dynamic_padding=True` to trim padding to the batch maximum while strictly preserving attention mask bounds and sequence truncation $\le 384$.

---

## 2. Line-by-Line Code Review Findings

### 2.1 Implemented vs. Reported Behavior
| Capability | Target File & Lines | Implementation Status | Reported vs. Actual Match |
| :--- | :--- | :--- | :---: |
| 500-step Checkpointing | `train_nli_classifier.py:1289-1314` | Implemented | MATCH |
| Atomic Staging & Rename | `train_nli_classifier.py:771-833` | Implemented | MATCH |
| SHA-256 Checksum Manifest | `train_nli_classifier.py:702-717, 827` | Implemented | MATCH |
| Checkpoint Integrity Check | `train_nli_classifier.py:674-700` | Implemented | MATCH |
| Pruning Old Checkpoints | `train_nli_classifier.py:720-738` | Implemented | MATCH |
| Optimizer & RNG Persistence| `train_nli_classifier.py:785-802` | Implemented | MATCH |
| Multi-Tier Watchdog Floors | `train_nli_classifier.py:208-257` | Implemented | MATCH |
| 3-Violation Filter | `train_nli_classifier.py:230-233` | Implemented | MATCH |
| Emergency Save Hook | `train_nli_classifier.py:997-1024` | Implemented | MATCH |
| Dynamic Sequence Padding | `train_nli_classifier.py:387-396` | Implemented | MATCH |
| CPU Threading Initialization | `train_nli_classifier.py:982-986` | Implemented | MATCH |

---

## 3. Discrepancies and Code Quality Observations

### Observation 1: Exception Logging Variable Typo (Non-Fatal)
- **Location:** `tools/training/train_nli_classifier.py`, line 1129.
- **Code:**
  ```python
  except Exception as exc:
      print(f"[CHECKPOINT RESUME ERROR] Could not load checkpoint from {resume_checkpoint_dir}: {exc}")
      raise exc
  ```
- **Analysis:** Inside the `except` block for checkpoint resumption, the log string references `resume_checkpoint_dir`, whereas the variable defined at line 1097 is named `resume_dir`. If `load_checkpoint_state` raises an exception during resumption, evaluating this f-string will raise `NameError: name 'resume_checkpoint_dir' is not defined` instead of printing the resume directory path. The process will still correctly crash and abort, but the underlying load error message is masked by the `NameError`.
- **Severity:** Low (only manifests if a checkpoint fails integrity check during resume).
- **Remediation Recommendation:** Change `{resume_checkpoint_dir}` to `{resume_dir}`.

### Observation 2: Unaccumulated Parameter Gradients (`param.grad`) Not Persisted
- **Location:** `tools/training/train_nli_classifier.py`, `save_checkpoint_state` (lines 784–787).
- **Analysis:** PyTorch's `optimizer.state_dict()` stores optimizer moment tensors (`exp_avg`, `exp_avg_sq`), not unaccumulated model parameter gradients (`param.grad`).
- **Impact in Current Architecture:** Negligible. Periodic checkpoints are invoked strictly after `optimizer.step()` and `optimizer.zero_grad()` when `accum_count == 0` (lines 1278–1285). Furthermore, `watchdog.check()` is evaluated only at step boundaries where `accum_count == 0`. Therefore, in standard operation and watchdog-triggered emergency checkpoints, there are zero unaccumulated gradients to lose.
- **Severity:** Informational. If mid-accumulation emergency saving is ever added in the future, unaccumulated gradients will be zeroed upon resume.

### Observation 3: Resume from Exact End-of-Epoch Boundary
- **Location:** `tools/training/train_nli_classifier.py`, lines 1115–1117 & 1238–1245.
- **Analysis:** When a checkpoint is saved at the completion of an epoch (e.g. `is_best` checkpoint at line 1367), `sample_idx` is recorded as `len(train_records) - 1`. Upon resuming, `start_sample_idx` becomes `len(train_records)`. During the resumed loop for `start_epoch`, all sample indices (`0` to `len(train_records) - 1`) satisfy `step_idx < start_sample_idx` and are skipped. The epoch validation is then re-executed for that epoch before proceeding to the subsequent epoch.
- **Severity:** Low. Progress is not lost, but redundant validation computation occurs if resuming specifically from an end-of-epoch checkpoint.

---

## 4. Security & Immutability Audits

- **Protected Path Guards:** `PROTECTED_PATHS` in `tools/training/train_nli_classifier.py` encompasses:
  - `/home/aditya/rags/models/pretrained/deberta-v3-small`
  - `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000`
  - `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000`
  - `/home/aditya/rags/models/trained/deberta-v3-small-nli-remediated`
  - `/home/aditya/rags/TrustRag`
- **Enforcement:** `save_checkpoint_state` enforces:
  ```python
  for protected in PROTECTED_PATHS:
      if out_path == protected or protected in out_path.parents:
          raise SecurityViolationError(f"Attempted overwrite of protected path: {out_path}")
  ```
  This prevents any run from writing intermediate step checkpoints into protected model directories.

---

## 5. Audit Conclusion

The source code accurately implements the capabilities documented in the Step 2.3 implementation report. Three non-fatal observations were identified and documented above. None of them compromise the core safety, integrity, or determinism of the training harness.

