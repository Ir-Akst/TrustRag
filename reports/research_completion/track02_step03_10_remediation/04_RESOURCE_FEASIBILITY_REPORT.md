# TrustRAG — Track 2, Step 3.10: Forward-Only Resource Feasibility Report

## 1. Experimental Profiling Setup

- **Model:** DeBERTa-v3-small (141,897,219 parameters in FP32)
- **Runtime:** `/home/aditya/rags/.venv-train/bin/python` (PyTorch 2.14.1+cpu)
- **Execution Mode:** Strictly Forward-Only (`torch.no_grad()`, `model.eval()`).
- **Optimization Restrictions:** Zero backward passes, zero optimizer steps, zero weights modified.
- **Concurrency:** 16 OpenMP/MKL CPU threads (`torch.set_num_threads(16)`).
- **Test Dataset:** Real NLI validation records from `validation.jsonl`.

---

## 2. Measured Resource Benchmarks

| Sequence Length | Mean Latency (ms) | Throughput (samples/s) | Process RSS (MB) | Swap Delta (MB) | Available Host RAM (MB) | Est. 1k Step Time |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **128** | 298.3 ms | 3.35 | 1,081.2 MB | -0.17 MB | 5,267.6 MB | ~5.0 min |
| **256** | 406.3 ms | 2.46 | 1,077.1 MB | -0.16 MB | 5,309.1 MB | ~6.8 min |
| **384** | **549.8 ms** | **1.82** | **1,107.7 MB** | **-0.49 MB** | **5,272.1 MB** | **~9.2 min** |
| **512** | 799.4 ms | 1.25 | 1,129.4 MB | +0.26 MB | 4,885.0 MB | ~13.3 min |

---

## 3. Resource Feasibility Assessment

1. **Host Memory Safety:**
   - At `max_seq_len = 384`, total RSS was only **1,107.7 MB**, leaving **5,272.1 MB of available RAM** (far above the 700 MB abort threshold).
   - Swap delta was negative (zero swap allocation), maintaining >2,700 MB of free swap (far above the 1,000 MB minimum).
2. **Execution Time Budget:**
   - 1,000 training forward passes at 550 ms require ~9.2 minutes.
   - Backward pass on CPU with batch size 1 typically requires ~1.5× forward time (~14 minutes).
   - Two 2,662-record validation passes (Step 0 and Step 1000) require ~24 minutes.
   - Total runtime is approximately 38–48 minutes, comfortably within the 60-minute watchdog cutoff.
3. **Disk Space:**
   - DeBERTa-v3-small checkpoint requires ~568 MB. Host disk has >50 GB available.

**Verdict:** `max_seq_len = 384` is **FULLY RESOURCE-FEASIBLE** on CPU.
