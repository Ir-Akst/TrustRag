# TrustRAG — Phase 11.1, Step 2.4: Watchdog Safety & Telemetry Audit

**Date:** 2026-11-15  
**Auditor:** Independent Senior ML Systems Auditor  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Subsystem:** Resource Watchdog & Fault-Tolerance Architecture  
**Evaluation Status:** FULLY VERIFIED & COMPLIANT

---

## 1. Metric Unit Analysis & Measurement Correctness

The telemetry measurement function `_default_telemetry()` in `WatchdogMonitor` was inspected line by line:
```python
@staticmethod
def _default_telemetry() -> dict[str, float]:
    telemetry = {
        "rss_mb": 0.0,
        "available_ram_mb": 0.0,
        "swap_total_mb": 0.0,
        "swap_used_mb": 0.0,
        "swap_free_mb": 0.0,
    }
    try:
        import psutil
        proc = psutil.Process()
        telemetry["rss_mb"] = proc.memory_info().rss / (1024 * 1024)
        vm = psutil.virtual_memory()
        telemetry["available_ram_mb"] = vm.available / (1024 * 1024)
        sw = psutil.swap_memory()
        telemetry["swap_total_mb"] = sw.total / (1024 * 1024)
        telemetry["swap_used_mb"] = sw.used / (1024 * 1024)
        telemetry["swap_free_mb"] = sw.free / (1024 * 1024)
    except Exception:
        pass
    return telemetry
```

### Verification Findings
1. **Resident Set Size (RSS):**
   - Source: `proc.memory_info().rss`.
   - Native unit returned by `psutil`: Bytes.
   - Conversion: Divided by `1024 * 1024` ($2^{20}$).
   - Standard output unit: Megabytes (MB / MiB).
   - **Correctness:** EXACT.
2. **Available Host RAM:**
   - Source: `psutil.virtual_memory().available`.
   - Native unit returned by `psutil`: Bytes (accounts for free memory + active buffers/cache that can be immediately reclaimed).
   - Conversion: Divided by `1024 * 1024`.
   - Standard output unit: Megabytes (MB / MiB).
   - **Correctness:** EXACT.
3. **Swap Metrics (Total, Used, Free):**
   - Source: `psutil.swap_memory().total`, `.used`, `.free`.
   - Native unit returned by `psutil`: Bytes.
   - Conversion: Divided by `1024 * 1024`.
   - Standard output unit: Megabytes (MB / MiB).
   - **Correctness:** EXACT.

---

## 2. Process Identification Audit

- **Method:** `psutil.Process()` instantiated without arguments.
- **Behavior in POSIX/Linux:** Defaults to `os.getpid()`, representing the current running Python process executing the training loop.
- **Multi-Process Hazards:** None. Training does not fork background DataLoader child workers. All training operations run synchronously within this primary PID.
- **Conclusion:** RSS tracking targets the exact process executing model forward/backward passes.

---

## 3. Three-Consecutive-Violation Logic Audit

In `WatchdogMonitor.check()`:
```python
ram_breached = current["available_ram_mb"] < self.ram_threshold
swap_breached = current["swap_free_mb"] < self.swap_free_min

if ram_breached or swap_breached or swap_growth_breached:
    self.consecutive_violations += 1
    current["consecutive_violations"] = self.consecutive_violations
    if self.consecutive_violations >= self.consecutive_violations_threshold:
        ...
        raise ResourceAbortError(...)
else:
    self.consecutive_violations = 0
    current["consecutive_violations"] = 0
```

### Behavioral Audit
1. **Isolated Transient Spikes:** A single violation increments the counter to 1. If the next check reports healthy values, the `else` branch executes and resets `self.consecutive_violations = 0`.
2. **Sustained Memory Depletion:** Only when three consecutive checks report violations without intermittent recovery does `self.consecutive_violations >= 3` trigger, invoking `emergency_save_fn` and raising `ResourceAbortError`.
3. **Verification:** Verified via Test 8 (`test_watchdog_aborting_on_sustained_floor_violations`):
   - Violation at Step 2 $\rightarrow$ counter = 1.
   - Normal at Step 3 $\rightarrow$ counter resets to 0.
   - Violations at Steps 4, 5, 6 $\rightarrow$ abort triggered at Step 6.

---

## 4. Emergency Checkpoint & Fail-Safe Behavior

```python
if self.consecutive_violations >= self.consecutive_violations_threshold:
    if self.emergency_save_fn:
        try:
            self.emergency_save_fn(step, "SUSTAINED_MEMORY_PRESSURE")
        except Exception as exc:
            print(f"[Watchdog Emergency Save Failed] {exc}")
    raise ResourceAbortError(...)
```

### Fail-Safe Invariants
- **Checkpoint Prior to Exit:** `self.emergency_save_fn` is invoked **before** `raise ResourceAbortError`.
- **No Silent Continuation on Checkpoint Failure:** If `self.emergency_save_fn` raises an exception (e.g. out of disk space, I/O error), the exception is logged, but the watchdog does **not** catch and swallow the condition to continue running. The subsequent lines immediately execute `raise ResourceAbortError(...)`, guaranteeing that execution unconditionally halts.
- **Ceiling Violations:** Process RSS ceiling violations (> 4,500 MB) bypass the 3-step filter and immediately trigger emergency save and abort.

---

## 5. Elimination of False-Positive Swap Aborts

In Step 2.1, the previous training run was terminated because `swap_used` increased by ~700 MB even though the system had > 4,000 MB of free RAM and > 3,000 MB of free swap.

### Audit of Remediated Swap Logic
1. `swap_growth_abort_mb` is configured as `Optional[float] = None` by default in `NLITrainingConfig`.
2. When `swap_growth_abort_mb is None`, the watchdog evaluates swap strictly against the absolute free capacity floor (`swap_free_min_mb = 1000.0`).
3. If background system processes page memory into swap, but `free_swap >= 1,000 MB` and `available_ram >= 700 MB`, `ram_breached = False` and `swap_breached = False`.
4. **Verification:** Verified via Test 7 (`test_watchdog_tolerating_swap_growth_when_healthy`). Swap growing from 0 MB to 1,500 MB triggered zero violations when free RAM and free swap remained above thresholds.

---

## 6. Audit Verdict on Watchdog Safety

The resource watchdog architecture is **ACCEPTED**. It provides robust, floor-based hardware protection, eliminates spurious swap aborts, prevents silent failure propagation, and ensures state persistence during emergency shutdowns.

