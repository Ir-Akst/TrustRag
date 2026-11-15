# Track 2, Step 3.3.1 — Section 04: Resource Telemetry and Throughput Reconciliation

## 1. Memory and Swap Telemetry Verification

- **Pre-Pilot RSS:** 213.52 MB
- **Post-Model Load RSS:** 1,044.57 MB (+831.05 MB for 141.9M FP32 model weights)
- **Peak Process RSS:** **2,369.99 MB** (~2.31 GB)
- **Post-Pilot RSS:** 2,336.48 MB
- **Lowest Available Host RAM:** **4,597.36 MB**
- **Safety Margin:** Maintained **3,897.36 MB** above the 700.0 MB abort threshold at all times.
- **Swap Drift:** +200.68 MB (Swap Used moved from 2,647.95 MB to 2,848.63 MB).
  - The +200 MB swap increase is directly corroborated by raw OS telemetry. Free swap remained at 3,151 MB, confirming no system thrashing.

---

## 2. Detailed Arithmetic & Throughput Reconciliation

### Telemetry Latency Summary:
- **Step 1:** Fwd = 224.7 ms, Bwd = 296.1 ms, Opt = 1,261.6 ms | Subtotal = 1,782.4 ms | Measured Step = 1,940.8 ms (Overhead = 158.4 ms)
- **Step 2:** Fwd = 152.7 ms, Bwd = 285.3 ms, Opt = 575.4 ms | Subtotal = 1,013.4 ms | Measured Step = 1,144.2 ms (Overhead = 130.8 ms)
- **Step 3:** Fwd = 154.9 ms, Bwd = 277.4 ms, Opt = 587.4 ms | Subtotal = 1,019.7 ms | Measured Step = 1,146.6 ms (Overhead = 126.9 ms)

### A. Total Script Elapsed Time vs. Step Latencies (DISC-03)
- Sum of 3 measured step times: $1,940.8 + 1,144.2 + 1,146.6 = 4,231.6 \text{ ms}$ (~$4.23 \text{ s}$).
- Total reported pilot elapsed time: **6.834 seconds**.
- Difference: $6.834 - 4.232 = 2.602 \text{ seconds}$.
- **Reconciliation:** The 2.60 seconds accounts for:
  - Process startup and psutil memory sampling: ~0.05 s
  - Loading tokenizer offline: 0.167 s
  - Loading DeBERTa-v3-small model offline: 0.336 s
  - AdamW optimizer construction: ~0.05 s
  - PyTorch library initialization and CPU thread pinning: ~2.00 s.

### B. Single-Epoch Runtime Projections (DISC-02)
Total binary training set size: **26,054 examples**.

1. **Overall Pilot Average Throughput (Including Step 1 AdamW Allocation):**
   $$\text{Average Step Time} = \frac{1,940.8 + 1,144.2 + 1,146.6}{3} = 1,410.55 \text{ ms}$$
   $$\text{Overall Throughput} = \frac{1,000}{1,410.55} = 0.70894 \text{ samples/sec} \approx 0.71 \text{ samples/sec}$$
   $$\text{Time per Epoch} = \frac{26,054}{0.70894} = 36,750.5 \text{ s} \approx \mathbf{10.21 \text{ hours}}$$

2. **Steady-State Throughput (Excluding Step 1 Allocation):**
   $$\text{Steady-State Step Time} = \frac{1,144.2 + 1,146.6}{2} = 1,145.43 \text{ ms}$$
   $$\text{Steady-State Throughput} = \frac{1,000}{1,145.43} = 0.87303 \text{ samples/sec} \approx 0.87 \text{ samples/sec}$$
   $$\text{Time per Epoch} = \frac{26,054}{0.87303} = 29,843.2 \text{ s} \approx \mathbf{8.29 \text{ hours}} \approx 8.3 \text{ hours}$$

### Adversarial Finding on the 8.3-Hour Estimate:
The Step 3.3 report's claim of an "approximately 8.3-hour epoch" is **based entirely on steady-state throughput (0.87 samples/sec)**.
Operational planners must note that 8.29 hours is an **idealized theoretical minimum**:
1. If initial allocation and GC overhead occur periodically, throughput drops closer to 0.71 samples/sec (10.2 hours).
2. It assumes **zero data loading latency** (DataLoader worker overhead).
3. It **completely excludes validation loops** (evaluating 2,895 validation records takes an additional ~1.5 hours on CPU).
4. It **excludes checkpoint serialization** to disk.
5. Continuous 8.3-hour heavy AVX CPU load on an Intel i7-1355U (15W/55W mobile processor) will inevitably induce **thermal throttling**, likely reducing effective throughput and extending run time to **12+ hours**.
