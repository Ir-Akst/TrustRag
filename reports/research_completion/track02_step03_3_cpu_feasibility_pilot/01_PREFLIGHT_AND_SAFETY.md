# Track 2, Step 3.3 — Section 01: Preflight and Resource Safety Telemetry

## 1. Repository State & Integrity Verification

Target and baseline repositories were audited prior to pilot execution:

- **Target Repository:** `/home/aditya/rags/TrustRag-phase11`
  - Active Branch: `phase-11`
  - Baseline Commit: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`
  - Status: Working tree clean of unauthorized code changes.
- **Protected Repository:** `/home/aditya/rags/TrustRag` (Phase 10 Baseline)
  - Active Branch: `phase-10`
  - HEAD Commit: `e65bcc80aac634900d1f8e343880fddf66cec168`
  - Status: Strictly untouched. Zero modifications.

## 2. Dataset Baseline Hashes

Prior to running the feasibility pilot, all 18 files across the 4 subdirectories in `data/processed/sft_v2/` were verified against their authoritative SHA-256 manifests:
- `data/processed/sft_v2/binary/` (5 files): ALL OK
- `data/processed/sft_v2/nli/` (5 files): ALL OK
- `data/processed/sft_v2/spans/` (5 files): ALL OK
- `data/processed/sft_v2/g3_readiness/` (3 files): ALL OK
- Historical baseline `data/processed/sft_v1/` (5 files): ALL OK

## 3. Host Hardware & Environment Telemetry

- **Processor:** Intel Core i7-1355U (10 physical cores: 2 P-cores, 8 E-cores, 12 logical threads).
- **Execution Concurrency:** `torch.set_num_threads(4)` pinned to 4 threads to prevent context thrashing.
- **Pre-Pilot RAM Available:** 6,122.45 MB
- **Pre-Pilot Process RSS:** 213.52 MB
- **Swap Total / Used / Free:** 6,000.00 MB / 2,647.95 MB / 3,352.05 MB
- **Disk Free on NVMe:** 45.0 GB available on `/dev/nvme0n1p3`.

## 4. Memory Safety Thresholds

The pilot implemented a strict abort threshold:
- If host available RAM drops below **700.0 MB**, the pilot halts immediately.
- Realized minimum available RAM during the entire run: **4,597.36 MB**.
- At all times, the system maintained over **4.5 GB** of headroom, confirming zero risk of OOM termination during batch size 1 execution.
