# TrustRAG — Phase 11.1, Step 2.3: Watchdog Remediation & Stability Verification Report

**Date:** 2026-11-15  
**Harness Component:** Resource Watchdog & Fault-Tolerance Subsystem  
**Target File:** `tools/training/train_nli_classifier.py`  
**Test Suite:** `tests/unit/test_phase11_step02_3_harness_remediation.py`  
**Test Environment:** Python 3.10.12 (`.venv-train`), PyTorch 2.14.1+cpu  
**Overall Status:** PASSED (3/3 Watchdog Tests Succeeded)

---

## 1. Problem Statement & Remediation Context

During Step 2.1, the training run was prematurely terminated by a brittle watchdog rule:
```python
# Legacy brittle logic
if current_swap > baseline_swap:
    raise ResourceAbortError("Swap growth detected")
```
This rule failed because:
1. Modern Linux kernels (especially on systems with `vm.swappiness=60`) routinely page out cold background daemon memory to swap when allocating large contiguous arrays, even when gigabytes of free RAM remain available.
2. The logic treated single-byte transient swap activity as a catastrophic OOM event.

In Step 2.3, this brittle check was completely superseded by a multi-tier capacity-floor watchdog (`WatchdogMonitor`).

---

## 2. Watchdog Architecture & Threshold Specifications

The remediated watchdog enforces three independent hardware capacity boundaries:

| Resource Metric | Config Parameter | Default Floor / Ceiling | Safe Operating Condition | Violation Condition |
| :--- | :--- | :--- | :--- | :--- |
| **Available Host RAM** | `min_available_ram_mb` | **700.0 MB** | `available_ram >= 700 MB` | `available_ram < 700 MB` |
| **Free Swap Space** | `min_free_swap_mb` | **1,000.0 MB** | `free_swap >= 1,000 MB` | `free_swap < 1,000 MB` |
| **Process RSS (Memory)**| `max_process_rss_mb` | **4,500.0 MB** | `process_rss <= 4,500 MB` | `process_rss > 4,500 MB` |

### Multi-Sample Smoothing (Consecutive Violations Filter)
To prevent transient garbage collector pauses or temporary tensor allocations from causing premature aborts, the watchdog requires **3 consecutive violations** (`consecutive_violations_threshold = 3`) before raising a fatal `ResourceAbortError`. A single normal check resets the violation counter.

### Emergency Checkpoint Persistence
When a fatal resource threshold violation is confirmed, `WatchdogMonitor` executes `emergency_save_fn(step, reason)` before raising the exception. This ensures that current model weights, optimizer moments, and RNG seeds are immediately written to an isolated directory:
`checkpoints/emergency_checkpoint_step_<step>/`

---

## 3. Test Cases & Verification Results

### Test 7: Watchdog Tolerating Swap Growth When Healthy (`test_watchdog_tolerating_swap_growth_when_healthy`)
- **Scenario:** System allocates memory causing swap usage to grow from 1,000 MB to 2,500 MB. However, available RAM remains abundant (5,000 MB) and free swap remains ample (3,500 MB). Process RSS is normal (2,200 MB).
- **Behavior Under Legacy Watchdog:** Immediate fatal crash on step 1.
- **Behavior Under Remediated Watchdog:** Checked across 10 consecutive simulated steps. Zero aborts triggered. Normal execution continues undisturbed.
- **Result:** PASSED.

### Test 8: Watchdog Aborting on Sustained Floor Violations (`test_watchdog_aborting_on_sustained_floor_violations`)
- **Scenario:** System undergoes extreme memory pressure. Available RAM drops to 500 MB (below 700 MB floor).
- **Behavior Tested:**
  - Check 1 (Step 4): 1st violation recorded. No abort.
  - Check 2 (Step 5): 2nd violation recorded. No abort.
  - Check 3 (Step 6): 3rd consecutive violation. Fatal `ResourceAbortError` raised:  
    `"Available host RAM dropped below safe floor: 500.0 MB < 700.0 MB (sustained 3 checks)"`
- **Result:** PASSED.

### Test 9: Emergency Checkpoint Behavior (`test_emergency_checkpoint_behavior`)
- **Scenario:** Process RSS spikes to 4,600 MB (exceeding the 4,500 MB ceiling).
- **Behavior Tested:**
  - Watchdog invokes `emergency_save_fn(step=42, reason="PROCESS_RSS_CEILING: 4600.0 MB > 4500.0 MB")`.
  - Captures exact step and reason.
  - Verifies emergency checkpoint function was called exactly once prior to exception propagation.
- **Result:** PASSED.

---

## 4. Verification Conclusion

The remediated watchdog completely eliminates false-positive aborts caused by benign OS swapping while maintaining hard safety guarantees against true Out-Of-Memory thrashing or system lockup.

