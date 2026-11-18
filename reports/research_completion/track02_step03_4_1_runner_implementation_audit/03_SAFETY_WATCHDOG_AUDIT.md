# Track 2, Step 3.4.1 — Section 03: Safety Watchdogs and Guardrail Audit

## 1. Real-Time Watchdog Specification

The `WatchdogMonitor` class executes on **every single step** of training, sampling OS telemetry via `psutil`:

| Guardrail | Threshold | Detection Mechanism | Abort Exception |
|-----------|:---------:|:-------------------:|:---------------:|
| **Physical Available RAM** | $< 700.0\text{ MB}$ | `vm.available / (1024 * 1024)` | `ResourceAbortError` |
| **Swap Growth** | $> 500.0\text{ MB}$ from baseline | `current_swap - baseline_swap` | `ResourceAbortError` |
| **Minimum Free Swap** | $< 1,000.0\text{ MB}$ | `sw.free / (1024 * 1024)` | `ResourceAbortError` |
| **Execution Wall-Clock** | $> 1,800.0\text{ s}$ (30 min) | `time.perf_counter() - t_start` | `TimeoutAbortError` |
| **CPU Thread Contention**| Fixed to 4 threads | `torch.set_num_threads(4)` | Managed Concurrency |
| **Pretrained Dir Overwrite**| Target == Pretrained | `target_path.resolve() == base_path.resolve()` | `SecurityViolationError` |
| **Test Set Access** | Path/Record contains 'test' | String & Schema validation | `SecurityViolationError` |

---

## 2. Fail-Fast & No Automated Retry Policy

If any threshold is breached:
1. Training loop halts immediately without completing the step.
2. An informative error message with the exact breached value and threshold is printed.
3. Temporary variables and gradients are released.
4. Process exits with status code 1.
5. **No automated restart or loop retry is attempted.**
