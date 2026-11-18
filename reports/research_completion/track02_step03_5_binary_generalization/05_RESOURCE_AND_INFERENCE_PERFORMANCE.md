# TrustRAG — Track 2, Step 3.5: Resource and Inference Performance Audit

## 1. Latency & Throughput Telemetry

- **Inference Hardware:** CPU Only
- **Execution Concurrency:** 1 process, 10 threads
- **Batch Size:** 1
- **Sequence Length:** 128 tokens
- **Total Samples Evaluated:** 1000
- **Total Wall-Clock Time:** 141.49 seconds
- **Throughput:** **7.07 samples/sec**

### Latency Percentiles
- **Median Latency:** **137.02 ms**
- **Mean Latency:** **141.43 ms**
- **P95 Latency:** **160.35 ms**
- **Min Latency:** 86.63 ms
- **Max Latency:** 437.42 ms

---

## 2. Host Resource Consumption

- **Initial RSS:** 595.61 MB
- **Peak RSS:** **1127.90 MB**
- **Net RSS Growth:** +532.29 MB
- **Available Host RAM:** **6187.18 MB**
- **Swap Total / Used / Free:** 6000.00 MB / 2489.93 MB / 3510.07 MB
- **Offline Integrity:** Verified (Zero remote HTTP/HTTPS connections).
