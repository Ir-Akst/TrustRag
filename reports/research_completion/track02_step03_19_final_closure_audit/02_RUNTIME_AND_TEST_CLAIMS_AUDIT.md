# TrustRAG — Track 2, Step 3.19: Final Closure Audit
## 02 — Hardware, Runtime & Test Claims Audit

- **Audit Date:** 2026-11-14T18:05:00Z
- **Auditor:** Independent Research Auditor & Final Evidence-Governance Reviewer

---

### 1. Host Hardware & Threading Reconciled

| Hardware / Resource Claim | Reported in Earlier Summaries | Actual Host Reality / Telemetry | Governance Finding |
| :--- | :--- | :--- | :--- |
| **CPU Model** | "8-core CPU" / Generic CPU | `13th Gen Intel(R) Core(TM) i7-1355U` | **ERRONEOUS CLAIM IN SUMMARIES** |
| **Core & Thread Count** | "8 cores" | **10 physical cores** (2 P-cores + 8 E-cores)<br>**12 logical threads** (`CPU(s): 12`) | Host possesses 10 cores / 12 threads. |
| **PyTorch Thread Configuration**| Unspecified / Default | `torch.set_num_threads(16)` | Set explicitly in `tools/training/train_nli_classifier.py` (`NLITrainingConfig.num_threads = 16`). |
| **Total Process Wall Time** | 5,461 s (91.0 min / 1.52 h) | **5,461.0 seconds** (Launch 20:27:54, Exit 21:58:55) | **VERIFIED ACCURATE** |
| **Peak Process RSS** | ~2.18 GB - 2.78 GB | **2,788.3 MB** (`peak_rss_mb` in `training_results.json`) | **VERIFIED ACCURATE** |
| **Minimum Available RAM** | > 2.0 GB | **2,977.2 MB** (Recorded at Step 1,000) | **VERIFIED ACCURATE** (Safely above 700 MB abort limit) |
| **Swap Utilization** | "0.0 GB (0 B) — zero disk paging" | **3,352.8 MB to 3,571.1 MB used** | **FALSE CLAIM IN SUMMARIES** |
| **Swap Growth** | "Zero swap growth" | **219.6 MB to 437.9 MB growth** | **FALSE CLAIM IN SUMMARIES** |
| **Minimum Free Swap** | > 1,000 MB | **2,428.9 MB free** | **VERIFIED ACCURATE** (Safely above 1,000 MB abort limit) |

---

### 2. Cadence & Timing Decomposition: Measured vs. Extrapolated

The reported cadence of **2.62 seconds per step** and total execution time were audited for mathematical consistency:

```
+---------------------------------------------------------------------------------------------------+
| Training Telemetry Timeline (Step 3.16)                                                           |
+----------------------+--------------------+-------------------------------------------------------+
| Event / Step         | Elapsed Timestamp  | Measured Operation                                    |
+----------------------+--------------------+-------------------------------------------------------+
| T_0 (Launch)         | 0.0 s              | Process initialization and dataset loading            |
| Pre-Evaluation End   | ~1,351.8 s         | Evaluated 2,662 validation samples (inferred)        |
| Step 50 Logged       | 1,482.73 s         | Pre-eval (~1,351.8s) + 50 training steps (~130.9s)   |
| Step 1,000 Logged    | 3,971.08 s         | Completion of optimizer step 1,000                    |
| Process Exit         | 5,461.00 s         | Post-eval (2,662 samples), serialization & teardown   |
+----------------------+--------------------+-------------------------------------------------------+
```

1. **Measured Steps 51–1,000 Duration:**
   $$\Delta t_{50\to 1000} = 3,971.0755\text{ s} - 1,482.7302\text{ s} = \mathbf{2,488.35\text{ seconds}}\quad (\text{over } 950\text{ steps})$$
2. **Empirically Measured Step Cadence:**
   $$\text{Cadence} = \frac{2,488.35\text{ s}}{950\text{ steps}} = \mathbf{2.6193\text{ seconds/step}}\quad (\approx 2.62\text{ s/step})$$
3. **Extrapolated 1,000-Step Training Time:**
   $$1,000 \times 2.6193\text{ s} = \mathbf{2,619.31\text{ seconds}}\quad (\approx 43.66\text{ minutes})$$
   *(The first 50 steps were not measured in isolation; their duration is extrapolated at $50 \times 2.6193 = 130.97\text{ s}$)*
4. **Post-Training Phase & The 135-Second Discrepancy:**
   - Total process duration: 5,461.00 s
   - Step 1,000 completion: 3,971.08 s
   - Post-training phase: $5,461.00 - 3,971.08 = \mathbf{1,489.92\text{ seconds}}$
   - Reports estimated post-evaluation as identical to pre-evaluation (~1,352 s) and serialization as ~3 s ($1,352 + 3 = 1,355\text{ s}$).
   - The remaining **134.92 seconds** (~2.25 min) represents unmodeled metric aggregation, tokenizer generation, and process cleanup. While minor (2.47% of total runtime), it proves that post-training evaluation cannot be casually assumed to equal pre-training evaluation.

---

### 3. Unit Test Execution vs. Research Completeness

Inspection of test evidence across Track 2 reveals:

1. **Exact Test Counts:**
   - Test command: `PYTHONPATH=. pytest tests/unit/test_track02_step03_6_nli_training_runner.py tests/unit/test_track02_step03_14_supervision_readiness.py`
   - Total test cases collected: **56 items**.
   - Passed: **55 items**.
   - Skipped: **1 item** (`test_prepare_nli_model_architecture` in `test_track02_step03_6_nli_training_runner.py`, marked `@pytest.mark.skip(reason="requires local model weights or network")`).
   - Failed: **0 items**.
   - Describing this as "55/55 passed" is technically misleading; the accurate description is **55 passed and 1 documented skip out of 56 total tests**.
2. **Python Environment Scope:**
   - Tests were executed under `/home/aditya/rags/.venv/bin/pytest` running **Python 3.14.9**.
   - Model training and inference executed under `/home/aditya/rags/.venv-train/bin/python` running **Python 3.10.22** with PyTorch 2.14.1+cpu.
   - The test suites do not execute within `.venv-train` directly, though core modules import cleanly.
3. **Implementation Completeness vs. Research Completeness:**
   > [!IMPORTANT]
   > Passing 55 unit tests proves **software and interface correctness**: functions take arguments properly, tensor shapes align, starvation counters increment, and sliding windows overlap without IndexError.
   > 
   > **Passing unit tests does NOT prove empirical research success.** It does not validate model convergence, semantic understanding, contradiction discrimination, or pipeline faithfulness. Conflating passing unit tests with research completion is an error of scientific methodology.

