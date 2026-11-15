# TrustRAG — Track 2, Step 3.7: Resource Capacity & Safety Watchdog Audit

## 1. Host Resource Telemetry

- **Available Physical RAM:** **5.3 GiB** (Total: 15 GiB)
- **Free Swap Space:** **3.9 GiB** (Total: 5.9 GiB)
- **Available Disk Space:** **45 GiB** on `/home/aditya/rags`
- **CPU Concurrency:** 16 execution threads available.

---

## 2. Watchdog Thresholds & Safety Mechanisms

| Watchdog Condition | Safety Threshold | Trigger Action | Test Suite Status |
| :--- | :---: | :--- | :---: |
| **Minimum Available RAM** | **< 700.0 MB** | Immediate `ResourceAbortError` abort | **TESTED & PASS** |
| **Maximum Swap Growth** | **> 500.0 MB** | Immediate `ResourceAbortError` abort | **TESTED & PASS** |
| **Minimum Free Swap** | **< 1,000.0 MB** | Immediate `ResourceAbortError` abort | **TESTED & PASS** |
| **Wall-Clock Timeout** | **> 1,800.0 s (30 min)** | Immediate `TimeoutAbortError` abort | **TESTED & PASS** |

---

## 3. Resource Projection for 1,000-Step Pilot

- **Estimated Peak RSS:** **~2,450 MB** (~2.45 GB).
- **Physical RAM Buffer:** **+2.85 GiB** headroom above peak RSS.
- **Estimated Runtime:** **~21 - 25 minutes** (based on measured ~1.2s/step in Step 3.4.2).
- **Disk Footprint for Checkpoint:** ~570 MB (safely within 45 GiB free disk).
