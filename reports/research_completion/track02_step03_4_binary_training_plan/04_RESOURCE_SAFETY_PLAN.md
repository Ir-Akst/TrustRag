# Track 2, Step 3.4 — Section 04: Resource Safety and Execution Safeguards

## 1. Hard Resource Safeguards & Abort Conditions

To protect host system stability during CPU training, the execution runner will enforce strict thresholds on every step:

| Guardrail | Threshold | Action on Breach |
|-----------|:---------:|:----------------:|
| **Physical Available RAM** | $< 700.0\text{ MB}$ | **IMMEDIATE ABORT** (Process halts, dumps emergency telemetry, exits code 1). |
| **Swap Growth** | $> 500.0\text{ MB}$ increase | **IMMEDIATE ABORT** (Prevents host swapping collapse). |
| **Swap Minimum Free** | $< 1,000.0\text{ MB}$ free | **IMMEDIATE ABORT**. |
| **Wall-Clock Duration** | $> 1,800\text{ seconds}$ (30 min) | **IMMEDIATE TIMEOUT** (Terminates loop if CPU throttles). |
| **CPU Concurrency** | Limit: 4 threads | Enforced via `torch.set_num_threads(4)`. |
| **Failure Recovery** | Zero automated retries | **FAIL FAST** policy; no automatic loop restarts upon failure. |

---

## 2. Resource Budget and Timing Projections

Based on the verified Step 3.3.1 telemetry:
- **Step Latency (Steady-State):** $1,145.4\text{ ms}$ (~$1.15\text{ s/step}$).
- **1,000 Training Steps:** $1,000 \times 1.1454 = 1,145.4\text{ seconds} \approx \mathbf{19.09\text{ minutes}}$.
- **Validation (200 samples @ 177.5 ms/sample):** $200 \times 0.1775 = 35.5\text{ seconds}$.
- **Total Estimated Run Time:** **~19.68 minutes**.
- **Buffer to 30-Minute Safety Cutoff:** $\approx 10.32\text{ minutes}$ (ample headroom for garbage collection, logging, and evaluation).

---

## 3. Artifact Serialization & Post-Run Cleanup

- Model weights updated during training must NOT be committed to git.
- Checkpoints will be saved outside the repository to:
  `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000/`
- All temporary telemetry tensors will be garbage collected (`gc.collect()`) after each validation step to maintain RSS $\le 2.4\text{ GB}$.
