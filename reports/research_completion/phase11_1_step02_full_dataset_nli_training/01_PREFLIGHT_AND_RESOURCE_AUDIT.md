# TrustRAG — Phase 11.1, Step 2: Full-Dataset NLI Training Audit
## 01 — Preflight & Resource Audit

- **Audit Date:** 2026-11-14T18:25:00Z
- **Auditor:** Senior ML Training Engineer & Independent Experimental Auditor

---

### 1. Repository & Baseline Integrity Audit

| Check Target | Expected Value / Path | Actual Measured Value | Preflight Status |
| :--- | :--- | :--- | :--- |
| **Repository Path** | `/home/aditya/rags/TrustRag-phase11` | `/home/aditya/rags/TrustRag-phase11` | ✅ PASS |
| **Active Branch** | `phase-11` | `phase-11` | ✅ PASS |
| **HEAD Commit** | `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` | `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61` | ✅ PASS |
| **Working Tree State** | No unauthorized tracked file modifications | Baseline development state preserved | ✅ PASS |
| **Phase 10 Baseline** | `/home/aditya/rags/TrustRag` | HEAD `e65bcc80aac634900d1f8e343880fddf66cec168` | ✅ PASS (Untouched) |

---

### 2. Dataset Integrity & Split Isolation Audit

| Dataset Split | File Location | Line Count | SHA-256 Digest | Class Distribution | Isolation Verification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Full NLI Train** | `data/processed/sft_v2/nli/train.jsonl` | 10,815 | `b1777c7ac608d6d79171dbc4deaeb7bf5c4ba87acf83adbe53d63020524474ad` | 6,707 ENT (62.0%)<br>2,688 NEU (24.9%)<br>1,420 CON (13.1%) | Zero overlap with val split |
| **NLI Validation** | `data/processed/sft_v2/nli/validation.jsonl` | 2,662 | `7601dd266edde160c51e1032150ea42c031131cb6be89c601637ad464121615c` | 1,662 ENT (62.4%)<br>644 NEU (24.2%)<br>356 CON (13.4%) | Verified isolated from train |
| **NLI Test Split** | `data/processed/ragtruth/test.jsonl` | 2,700 | `55f5ec8bf47039551fc5fe64fbdf35306422c50402a1d6cc9dd1b3bfe12540f1` | Fully Isolated | Prohibited from model selection |

---

### 3. Hardware, Compute & Runtime Decomposition

| Hardware Metric | Host Reality | Measurement Source | Impact on Proposed 3-Epoch Run |
| :--- | :--- | :--- | :--- |
| **CPU Model** | `13th Gen Intel(R) Core(TM) i7-1355U` | `lscpu` | 10 physical cores (2 P-cores + 8 E-cores), 12 threads |
| **GPU Availability** | **NONE** | System bus scan | PyTorch runs exclusively in CPU mode (`torch 2.14.1+cpu`) |
| **Available RAM** | ~3.0 GB - 5.0 GB available | System telemetry | Safe margin above 700 MB abort limit |
| **Available Disk** | > 25 GB free | `df -h` | Ample headroom for checkpoints (~1.2 GB required) |
| **Active Swap** | ~3.4 GB used, ~2.5 GB free | System telemetry | Safe margin above 1,000 MB abort limit |

#### Fresh Empirical Runtime Calculation
- **Cadence per sample (Measured in Step 3.16):** $2.6193\text{ seconds/step}$
- **Samples to process (3 epochs over 10,815 samples):** $3 \times 10,815 = \mathbf{32,445\text{ forward-backward passes}}$
- **Pure training loop duration:**
  $$32,445 \times 2.6193\text{ s} = \mathbf{84,983.2\text{ seconds}} \approx \mathbf{23.61\text{ hours}}$$
- **Validation duration (Step 0 baseline + 3 epoch evaluations = 4 evaluations):**
  $$4 \times 1,351.8\text{ s} = \mathbf{5,407.2\text{ seconds}} \approx \mathbf{1.50\text{ hours}}$$
- **Total estimated execution wall time:**
  $$\text{Total Time} = 84,983.2\text{ s} + 5,407.2\text{ s} + 20\text{ s (checkpoint sync)} = \mathbf{90,410.4\text{ seconds}}\quad (\approx \mathbf{25.11\text{ hours}})$$

#### Runtime Safety Gate Evaluation
- **Watchdog default:** 3,600.0 seconds (1 hour).
- **Previous authorized maximum (Step 3.15.2):** 36,000.0 seconds (10 hours).
- **Required watchdog threshold:** $\ge 95,000.0\text{ seconds}$ (~26.4 hours).
- **Preflight Ruling:** The existing watchdog limit cannot safely accommodate a 25.1-hour run. Under explicit instructions, extending the watchdog duration silently is prohibited. **Preflight BLOCKED on runtime safety.**

