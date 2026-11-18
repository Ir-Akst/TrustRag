# TrustRAG Track 2 — Step 3.15.1
## 02 — Watchdog Audit

**Audit timestamp:** 2026-11-14T14:35:44Z

---

## 1. Watchdog Architecture (Source: `train_nli_classifier.py`)

### 1.1 Initialization (L648–L654)

```python
watchdog = WatchdogMonitor(
    ram_abort_threshold_mb=config.ram_abort_threshold_mb,    # 700.0 MB
    swap_growth_abort_mb=config.swap_growth_abort_mb,        # 1000.0 MB
    swap_free_min_mb=config.swap_free_min_mb,                # 1000.0 MB
    max_duration_seconds=config.max_duration_seconds,        # 3600.0 s ← TOO SHORT
)
init_telemetry = watchdog.check(step=0)
```

The timer `self.t_start = time.perf_counter()` (L130) is set during `__init__`,
which runs **before** data loading, model loading, and all evaluation.

### 1.2 Global Timeout Guard (L163–L178)

```python
elapsed = time.perf_counter() - self.t_start
if elapsed > self.max_duration:
    raise TimeoutAbortError(...)
```

- **Scope:** Measures wall time from watchdog construction to each `check()` call.
- **What it covers:** Entire pipeline including model load, data load, pre-training eval,
  AND training steps.
- **What it does NOT protect:** Evaluation phases (no `watchdog.check()` inside `evaluate()`).
- **Termination:** Raises `TimeoutAbortError` exception (uncaught in `execute_training`).

### 1.3 RAM Guard (L180–L184)

```python
if current["available_ram_mb"] < self.ram_threshold:
    raise ResourceAbortError(...)
```

- Threshold: 700 MB available RAM.
- Fires if system RAM drops below 700 MB at any `check()` call.
- Current available RAM: ~6,814 MB → ~6,114 MB margin above threshold.

### 1.4 Swap Growth Guard (L186–L192)

```python
swap_growth = current["swap_used_mb"] - self.baseline_telemetry["swap_used_mb"]
if swap_growth > self.swap_growth_threshold:
    raise ResourceAbortError(...)
```

- Baseline reset at L754 (`watchdog.reset_baseline()` before training loop).
- Threshold: 1,000 MB growth from post-eval baseline.
- Protects against runaway swap consumption during training.

### 1.5 Minimum Free Swap Guard (L194–L198)

```python
if current["swap_free_mb"] < self.swap_free_min:
    raise ResourceAbortError(...)
```

- Threshold: 1,000 MB minimum free swap.
- Current free swap: ~2,828 MB → 1,828 MB margin.

---

## 2. Per-Step Timeout: NOT PRESENT

There is no per-step timeout. The watchdog measures elapsed wall clock from construction
to the current check. There is no `max_step_duration_seconds` parameter.

This means:
- A single hanging tokenization step or forward pass will not be detected until the
  next `watchdog.check()` call.
- In practice, CPU operations do not hang indefinitely for DeBERTa forward passes.

---

## 3. Watchdog Check Placement

| Location | Line | Called During |
|---|---|---|
| Initialization check | L654 | Before everything |
| Training step check | L762 | Each of the 1,000 steps |
| Inside `evaluate()` | — | **NEVER** |
| After post-training eval | — | **NEVER** |

**Critical gap:** Neither the pre-training eval (L749) nor the post-training eval (L810)
calls `watchdog.check()`. Both can run for 88+ minutes without any timeout guard.
If the evaluation hangs (e.g., PyTorch deadlock), there is no timeout mechanism to
abort it.

---

## 4. Termination Behavior on Timeout

When `TimeoutAbortError` is raised at training step 1:

1. Exception propagates up from `watchdog.check()` (L762) through the `for` loop.
2. No `try/except` wraps the training loop in `execute_training()`.
3. Exception propagates to the caller (CLI `__main__` block or unit test).
4. **No checkpoint is written** (`save_checkpoint_atomic()` at L815 is never reached).
5. **No `.tmp_` directory** is created (the `save_checkpoint_atomic` function is never called).
6. **No partial checkpoint corruption risk** — the output directory is clean.
7. Pre-training eval results (`step0_metrics`) exist in RAM only — lost on abort.

---

## 5. Atomic Checkpoint Safety

`save_checkpoint_atomic()` (L551–L590) uses a staged write pattern:
1. Create `.tmp_<name>_<timestamp>` directory.
2. Write all files to `.tmp_` directory.
3. Atomically rename `.tmp_` → final directory.
4. On any exception inside: `shutil.rmtree(tmp_dir)` cleans up.

If a timeout fires **during** checkpoint write (edge case if timeout value is set
very close to completion):
- The `.except Exception` block (L582–L584) catches it and cleans up `.tmp_`.
- The final output directory is never created in a partial state.
- **However:** `TimeoutAbortError` is a subclass of `Exception`, so it IS caught by
  the cleanup handler inside `save_checkpoint_atomic`. This means checkpoint cleanup
  is safe even on timeout during write.

---

## 6. Resume Safety

The pipeline does NOT support checkpoint resumption. If aborted:
- No intermediate checkpoints are saved during training.
- Resuming requires restarting from the beginning.
- Pre-training eval must be re-run on restart.

---

## 7. Watchdog Audit Summary

| Property | Status | Notes |
|---|---|---|
| Global timeout | ✅ Implemented | 3,600 s — **TOO SHORT** |
| Timer scope | ⚠️ Entire pipeline | Includes model load + eval |
| Per-step timeout | ❌ Not present | Acceptable for CPU |
| RAM guard | ✅ Implemented | 700 MB threshold, 6,114 MB margin |
| Swap growth guard | ✅ Implemented | 1,000 MB, baseline reset at step 0 |
| Swap minimum guard | ✅ Implemented | 1,000 MB, 1,828 MB margin |
| Eval timeout | ❌ Not present | Gap: eval can hang indefinitely |
| Atomic checkpoint | ✅ Implemented | Clean on exception including timeout |
| Resume support | ❌ Not present | Full restart required after abort |
| Incomplete checkpoint | ✅ Protected | Never written on training abort |

---
*Generated by Step 3.15.1 Runtime Audit — 2026-11-14T14:35:44Z*
