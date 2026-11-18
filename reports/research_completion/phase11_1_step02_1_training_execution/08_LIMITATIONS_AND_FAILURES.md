# TrustRAG — Phase 11.1, Step 2.1: Root Cause Analysis, Limitations & Failure Audit

## 1. Primary Failure Mode Analysis

The training campaign encountered two independent failure events across two execution attempts:

### 1.1 Incident 1: Host Involuntary Reboot (Run 1, `task-9745`)
- **Point of Interruption:** Step 1,750 / 8,112 (Epoch 1, ~64.7% through epoch 1)
- **Elapsed Duration:** 13,838.0s (~3.84 hours)
- **Root Cause:** External system event. The host operating environment underwent an unannounced full reboot at 2026-11-14 23:42:13 UTC, terminating the active background runner.
- **Consequence:** Because checkpoint serialization was designed to trigger at epoch boundaries, zero interim weights had been committed to disk, resulting in the loss of 1,750 completed optimizer steps.

### 1.2 Incident 2: Rigid Delta-Based Watchdog Abort (Run 2, `task-9774`)
- **Point of Interruption:** Step 325 / 8,112 (Epoch 1, ~12.0% through epoch 1)
- **Elapsed Duration:** ~3,800s (~1.05 hours)
- **Root Cause:** Premature watchdog trip via `ResourceAbortError: Swap usage grew by 1038.4 MB from baseline (Threshold: 1000.0 MB)!`
- **Mechanism:**
  1. Because the host had just rebooted, baseline swap usage was recorded at **0.0 MB**.
  2. As PyTorch allocated ~2.8 GB RSS for the FP32 DeBERTa graph, the Linux kernel's memory management subsystem opportunistically paged out idle system daemons and desktop processes to swap.
  3. Total host swap expanded to 1,038.4 MB, crossing the 1,000.0 MB delta threshold.
  4. Crucially, **the host was not in any genuine memory distress**:
     - Host Available RAM: **3,750.0 MB** (far above the 700 MB abort threshold)
     - Host Free Swap: **4,961.6 MB** (far above the 1,000 MB minimum swap requirement)
     - Process RSS: **2,845.0 MB** (flat and stable across all steps; zero memory leaks)
  5. The watchdog evaluated a purely differential condition ($\Delta \text{Swap} > 1,000\text{ MB}$) without conditioning on the fact that baseline swap was 0.0 MB and nearly 5 GB of free swap remained.

---

## 2. Engineering Limitations & Design Vulnerabilities

| Vulnerability | Manifestation | Forensic Impact |
| :--- | :--- | :--- |
| **Coarse Checkpoint Granularity** | Checkpoints only saved at epoch boundaries ($\approx 5.8$ hours apart on CPU). | When Run 1 was interrupted at 3.84 hours (Step 1,750), all progress within that epoch was lost. |
| **Rigid Delta Swap Watchdog** | Swap threshold defined as fixed growth delta ($\Delta \le 1,000\text{ MB}$) from arbitrary initial baseline. | When baseline swap is 0.0 MB on a 6.0 GB swap host, normal OS background paging inevitably exceeds 1,000 MB even with 5 GB free swap. |
| **Lack of Step-Level Resumption** | Training runner lacked `--resume-from-checkpoint` logic. | When revived in Run 2, training had to restart from step 0 rather than resuming from step 1,750. |

---

## 3. Actionable Remediation Recommendations for Future Authorization

Before requesting authorization for any subsequent training campaign, the following architectural upgrades should be implemented:

1. **Floor-Based Memory Safeguards:**
   Replace the rigid delta threshold with an absolute floor:
   ```python
   # Recommended Watchdog Logic
   if current["swap_free_mb"] < self.swap_free_min_mb:  # e.g., 1,000 MB floor
       raise ResourceAbortError(...)
   ```
   Alternatively, if delta monitoring is retained, allow a higher ceiling when free swap exceeds 4,000 MB:
   ```python
   swap_ceiling = min(2500.0, current["swap_free_mb"] - 1000.0)
   ```
2. **Periodic Step-Level Interim Checkpointing:**
   Save a rolling `interim_latest_checkpoint` every 500 or 1,000 steps with optimizer state and dataloader offsets to prevent catastrophic loss of compute time from system interruptions.
3. **Warm Baseline Telemetry Sampling:**
   Allow the watchdog baseline to be sampled after the model and initial batch are allocated, or calibrate baseline swap against historical host norms.

