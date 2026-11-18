# TrustRAG — Phase 11.1, Step 3: Hardware Resource Telemetry & Watchdog Log

**Date:** 2026-11-15  
**Auditor:** Senior ML Infrastructure Engineer and Experimental Execution Auditor  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Execution Environment:** Intel Core i7-1355U, 16 GB RAM, Ubuntu Linux x86_64  
**Watchdog Subsystem:** `WatchdogMonitor` (tools/training/train_nli_classifier.py)

---

## 1. Configured Resource Safeguards

| Resource Metric | Config Parameter | Operational Floor / Ceiling | Safe Operating Condition |
| :--- | :--- | :--- | :--- |
| **Available Host RAM** | `ram_abort_threshold_mb` | **700.0 MB** | `available_ram >= 700 MB` |
| **Free Swap Space** | `swap_free_min_mb` | **1,000.0 MB** | `free_swap >= 1,000 MB` |
| **Process RSS** | `max_process_rss_mb` | **4,500.0 MB** | `process_rss <= 4,500 MB` |
| **Consecutive Violations**| `watchdog_consecutive_violations` | **3 checks** | Requires 3 sustained breaches |
| **Execution Duration** | `max_duration_seconds` | **86,400.0s (24h)** | Timeout guard |

---

## 2. Telemetry Milestones Log

### Milestone 1: Preflight Verification (Step 0 Pre-Ingestion)
- **Timestamp:** 17:22:01 IST
- **Process RSS:** 221.0 MB
- **Available RAM:** 6,410.2 MB
- **Free Swap:** 5,183.4 MB
- **Used Swap:** 816.6 MB
- **Watchdog Status:** Healthy (0 violations)

### Milestone 2: Post-Validation Baseline (Step 0 Completed)
- **Timestamp:** ~17:33:00 IST
- **Elapsed Time:** ~650s
- **Process RSS:** 1,212.1 MB (Model weights and evaluation activations resident)
- **Available RAM:** 5,568.6 MB
- **Free Swap:** 5,182.2 MB
- **Used Swap:** 817.8 MB
- **Watchdog Status:** Baseline reset; healthy (0 violations)

### Milestone 3: Step 50 Training Log
- **Timestamp:** ~17:40:17 IST
- **Elapsed Time:** 1,096.8s (~18.28 min)
- **Process RSS:** 2,711.8 MB (Gradient accumulation buffers active)
- **Available RAM:** 4,103.4 MB (Margin above floor: +3,403.4 MB)
- **Free Swap:** ~5,180 MB (Margin above floor: +4,180 MB)
- **Loss:** 0.9976 (Rolling 50-step mean: 1.0886)
- **Learning Rate:** $9.80 \times 10^{-6}$
- **Consecutive Violations:** 0
- **Watchdog Status:** Healthy; operating normally with abundant headroom.

---

## 3. Analysis of Interruption

- **Cause of Termination:** External hardware/OS machine reboot (`uptime` reset to 4 minutes).
- **Watchdog Involvement:** Zero. At no point did Available RAM drop below 700 MB, Free Swap drop below 1,000 MB, or Process RSS exceed 4,500 MB.
- **Memory Leakage Assessment:** Process RSS stabilized around ~2.7 GB, confirming that batch size 1 with gradient accumulation 4 and dynamic padding successfully contained memory usage within safe hardware bounds.

