# TrustRAG — Phase 11.1, Step 3: Mandatory Preflight Audit & Certification Report

**Date:** 2026-11-15  
**Auditor:** Senior ML Infrastructure Engineer and Experimental Execution Auditor  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**Commit HEAD:** `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`  
**Preflight Certification Status:** ALL 10 PREFLIGHT CHECKS PASSED (Zero Blockers)

---

## 1. Preflight Verification Checklist

### Check 1: Repository Path, Branch & HEAD Alignment
- **Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Confirmed)
- **Active Branch:** `phase-11` (Confirmed)
- **Commit HEAD:** `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` (Exact match)
- **Status:** **PASSED**

### Check 2: Protected Checkpoint Cryptographic Audits
Verified via `sha256sum`:
- `models/pretrained/deberta-v3-small/pytorch_model.bin`:  
  `d4b0ebcc7799a2c2dde1a39199cb0ed709f2c6b63a48b8c05133b77955f271a9` (**MATCH**)
- `models/trained/deberta-v3-small-binary-pilot1000/model.safetensors`:  
  `472ea687cae7b9d3caf1feb97adb35bef6acd31260b7b2ab7564a48eaf3fdb1b` (**MATCH**)
- `models/trained/deberta-v3-small-nli-pilot1000/model.safetensors`:  
  `500832fa1b9b7c67c2c08d9e1f4d4c76d235d15fa9960d76e1e6e81c220a2f8a` (**MATCH**)
- `models/trained/deberta-v3-small-nli-remediated/model.safetensors`:  
  `bb4c26bab4a147c2ad6bdae7ec8a1ecc56841ea56fc89922fd377fb5d70fe113` (**MATCH**)
- **Status:** **PASSED** (100% Immutability Verified)

### Check 3: Dataset Cryptographic Hashes & Split Isolation
Verified against `data/processed/sft_v2/nli/checksums.sha256`:
- `train.jsonl`: `b1777c7ac608d6d79171dbc4deaeb7bf5c4ba87acf83adbe53d63020524474ad` (10,815 natural distribution examples) — **OK**
- `validation.jsonl`: `5ffdc2e9c1f609e9db6786a489745347f71755dc039864d4b1a415ff68f121d5` (2,704 total, 2,662 active imbalanced examples) — **OK**
- `dataset_manifest.json`: `d72023bb4129b0a70f443b3db97fba034032d1ef10851897d5a5cf2b0124fe76` — **OK**
- `exclusion_manifest.json`: `3780fbca8dc2d4d9cc2a05cf4c28135832a26514fc7dc8161ba05db3a84e6260` — **OK**
- `schema.json`: `4359ebaa000abf0cff83ebc2efd8616a19f4a569d67b845d4c9f131a941e7d23` — **OK**
- **Status:** **PASSED**

### Check 4: Step 2.3–2.5 Implementation & Unit Test Verification
- Step 2.3 Harness Remediation Tests: 10 / 10 **PASSED**
- Step 2.5 Final Limitation Remediation Tests: 7 / 7 **PASSED**
- Historical Regression Tests (pytest): 55 / 55 **PASSED** (1 skipped intentionally for offline mode)
- Total Verified Suite: 72 passed, 1 skipped, 0 failed.
- **Status:** **PASSED**

### Check 5: Python Environment & Dependencies
- Runtime: Python 3.10.22 (`/home/aditya/rags/.venv-train/bin/python`)
- PyTorch: `2.14.1+cpu` (FP32 CPU execution confirmed)
- Transformers: `5.20.2`
- Safetensors: `0.8.0`
- Psutil: `7.2.2`
- **Status:** **PASSED**

### Check 6: Disk Space Availability
- Filesystem: `/dev/nvme0n1p3` mounted on `/home/aditya/rags`
- Available Disk Space: **43 GB** (Exceeds mandatory 8 GB requirement by > 5x)
- Estimated footprint for 3 checkpoints + models + logs: ~2.5 GB
- **Status:** **PASSED**

### Check 7: Host Resource Baseline (RAM, Swap, CPU)
- Total System RAM: 15.29 GB
- Available RAM: **6.41 GB (6,564 MB)** (Significantly exceeds 700 MB floor)
- Total Swap: 5.86 GB
- Free Swap: **5.06 GB (5,183 MB)** (Significantly exceeds 1,000 MB floor)
- Used Swap: 816.6 MB
- CPU Architecture: Intel Core i7-1355U (10 physical cores, 12 threads)
- **Status:** **PASSED**

### Check 8: Output Directory Cleanliness
- Target Output Directory: `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`
- Status: Confirmed non-existent. No conflicting previous runs exist.
- **Status:** **PASSED**

### Check 9: Resume Mechanism & Watchdog Policy Configuration
- Checkpoint Interval: Every 500 optimizer steps.
- Retention: Last 2 step checkpoints kept + emergency + best model directory.
- Watchdog Floors: Available RAM $\ge 700$ MB, Free Swap $\ge 1,000$ MB, Process RSS $\le 4,500$ MB.
- Smoothing: 3 consecutive violations required before abort.
- Emergency checkpoint hook: Persists current weights, moments, and seeds before exit.
- Fast-forward resume: Exact `sample_idx + 1` resume with zero duplicate optimizer updates.
- **Status:** **PASSED**

### Check 10: Step Arithmetic & Runtime Estimation
- Dataset: 10,815 natural distribution training examples
- Epochs: exactly 3
- Micro-batch size: 1
- Gradient accumulation steps: 4
- Effective batch size: 4
- Passes per epoch: 10,815 forward+backward passes
- Optimizer steps per epoch: $\lceil 10,815 / 4 \rceil = 2,704$ steps
- Total forward+backward passes: $10,815 \times 3 = \mathbf{32,445 \text{ passes}}$
- Total optimizer steps: $2,704 \times 3 = \mathbf{8,112 \text{ optimizer steps}}$
- Total validation inferences: $2,662 \times 4 = 10,648 \text{ inferences}$
- Empirical throughput (10 threads, dynamic padding): ~1.237s / pass ($\approx 4.95$s / optimizer step)
- Projected Training Duration: $\approx 40,134$s ($\approx 11.15$ hours)
- Projected Validation Duration: $\approx 3,420$s ($\approx 0.95$ hours)
- **Total Projected Campaign Duration:** $\approx 43,554$s ($\approx 12.10$ hours)
- Watchdog timeout configuration: 86,400s (24 hours), preventing premature timeout aborts.
- **Status:** **PASSED**

---

## 2. Preflight Determination

All 10 mandatory preflight checks are strictly satisfied. Zero preflight blockers exist. The execution harness is certified ready to execute the authorized full-dataset NLI training campaign.

