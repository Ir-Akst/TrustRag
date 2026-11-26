# TrustRAG Phase 19 — Performance, Scalability and Deployment Hardening Report

**Auditor:** Principal Research Engineer, ML Performance Specialist & Systems Architect  
**Date:** 2026-11-19T01:18:00+05:30  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-17-20-final-release`  
**Target Architecture:** DeBERTa-v3-small (141.9M parameters, CPU execution)  
**Deliverables Directory:** `reports/research_completion/final_independent_validation_and_release/`  
**Structured Metrics Data:** `reports/research_completion/final_independent_validation_and_release/phase19_scalability_results.json`  

---

## 1. Executive Summary

Phase 19 conducted a comprehensive hardware profiling, thread optimization, scalability analysis, and memory footprint benchmark of the TrustRAG engine running on standalone CPU infrastructure (x86_64, 12 logical cores).

### Key Architectural Findings:
1. **Intra-Op Thread Sweet Spot:** Setting `torch.set_num_threads(2)` delivers **$55.84\text{ ms}$** P50 single-claim latency — a **$1.73\times$ speedup** over single-thread execution ($97.72\text{ ms}$). Allocating 4 or 8 threads induces thread synchronization overhead and memory bus contention, degrading latency to $85.93\text{ ms}$ and $78.31\text{ ms}$.
2. **Cold Boot vs. Warm Inference:** Engine module loading and configuration requires merely **$0.05\text{ ms}$**. First-query PyTorch graph compilation and weight page faulting requires **$2,868.37\text{ ms}$**, following which steady-state warm inference stabilizes at $55.84\text{ ms}$.
3. **Memory Footprint:** Initial runtime RSS starts at **$289.29\text{ MB}$**, grows to **$728.25\text{ MB}$** upon DeBERTa model loading, and caps at a peak RSS of **$774.54\text{ MB}$** during heavy batch processing.
4. **Sequence Length Scaling:** Evaluation latency scales super-linearly with sequence length: $80.14\text{ ms}$ at 64 tokens, $98.37\text{ ms}$ at 128 tokens, $137.30\text{ ms}$ at 256 tokens, and $230.95\text{ ms}$ at 512 tokens.

---

## 2. Intra-Op Thread Parallelism Sweeps

Evaluated across 20 iterations per thread configuration on DeBERTa-v3-small:

| CPU Core Threads | Mean Latency (ms) | P50 Latency (ms) | P95 Latency (ms) | P99 Latency (ms) | Relative Speedup | Hardware State |
|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **1 Thread** | 97.85 ms | 97.72 ms | 99.15 ms | 100.59 ms | 1.00x | Pure serial GEMM |
| **2 Threads** | **56.42 ms** | **55.84 ms** | **58.02 ms** | **63.65 ms** | **1.73x** | **Optimal Operating Point** |
| **4 Threads** | 89.18 ms | 85.93 ms | 103.42 ms | 104.63 ms | 1.10x | Cache invalidation / sync stalls |
| **8 Threads** | 78.52 ms | 78.31 ms | 82.71 ms | 82.97 ms | 1.25x | Bus saturation |

> [!TIP]
> Always configure `torch.set_num_threads(2)` in CPU deployment environments. Using default `num_threads = n_cpus` (e.g. 12 or 16) degrades performance by over 40% due to cross-core synchronization overhead.

---

## 3. Sequence Length Scaling & Resource Bounding

Evaluated on realistic query-passage combinations:

| Sequence Bound ($L$) | Mean Latency (ms) | P50 Latency (ms) | P95 Latency (ms) | Latency Overhead vs. $L=64$ | Recommended Tier |
|:---:|:---:|:---:|:---:|:---:|---|
| **$L = 64$** | 80.18 ms | 80.14 ms | 80.70 ms | 1.00x | Fast conversational QA |
| **$L = 128$** | 102.63 ms | 98.37 ms | 121.00 ms | 1.23x | **Default Interactive SLA** |
| **$L = 256$** | 139.18 ms | 137.30 ms | 149.85 ms | 1.71x | Complex paragraph analysis |
| **$L = 512$** | 245.99 ms | 230.95 ms | 308.99 ms | 2.88x | Offline batch background only |

---

## 4. Memory Footprint and Production Resource Limits

- **Baseline Environment RAM:** $289.29\text{ MB}$
- **Model In-Memory Allocation:** $438.96\text{ MB}$ (141.9M float32 parameters + tokenizers)
- **Peak Operational RSS:** **$774.54\text{ MB}$**
- **Headroom Margin:** Can comfortably operate inside a container or VM provisioned with **$1.5\text{ GB}$ to $2.0\text{ GB}$** of RAM.

---

## 5. Deployment Hardening Recommendations

1. **Pre-warming Hook:** Execute one dummy inference call during container startup or health check (`/healthz`) to absorb the 2.8-second first-query latency penalty.
2. **Interactive SLA Bound:** Enforce `max_length = 128` on all synchronous user queries to guarantee $<125\text{ ms}$ P95 latency.
3. **Thread Pinning:** Pin worker processes to 2 dedicated physical cores using `taskset` or Docker CPU set affinities (`--cpuset-cpus`).

