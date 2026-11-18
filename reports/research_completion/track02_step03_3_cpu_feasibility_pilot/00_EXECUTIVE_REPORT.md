# Track 2, Step 3.3: Full-Architecture DeBERTa-v3-small CPU Feasibility Pilot — Executive Report

**Auditor:** Senior ML Infrastructure Engineer & Experimental Auditor  
**Date:** 2026-11-14  
**Target Repository:** `/home/aditya/rags/TrustRag-phase11` (Branch: `phase-11`, HEAD: `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)  
**Protected Baseline:** `/home/aditya/rags/TrustRag` (Branch: `phase-10`, HEAD: `e65bcc80aac634900d1f8e343880fddf66cec168`, UNTOUCHED)  
**Execution Environment:** `/home/aditya/rags/.venv-train` (Python 3.10.22, PyTorch 2.14.1+cpu, Transformers 5.20.2)  
**Model Directory:** `/home/aditya/rags/models/pretrained/deberta-v3-small` (`microsoft/deberta-v3-small`, Commit `a36c739020e01763fe789b4b85e2df55d6180012`)  
**Dataset:** `data/processed/sft_v2/binary/train.jsonl` (26,054 records, SHA-256 verified)  

---

## 1. Executive Verdict: `PILOT_PASSED`

The strictly bounded full-architecture feasibility pilot on CPU has **PASSED** across all empirical dimensions. 

Unlike the preliminary Step 3.1 smoke test (which utilized a 0.48M parameter toy model and synthetic token sequences), Step 3.3 executed **genuine optimization steps** using:
1. The **full 141.9M parameter** official `microsoft/deberta-v3-small` architecture.
2. The official `DebertaV2Tokenizer` with a 128,001-token vocabulary.
3. **Real domain examples** from `data/processed/sft_v2/binary/train.jsonl`.
4. Strict offline enforcement (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `local_files_only=True`).
5. Complete forward passes, CrossEntropy loss computation, reverse-mode backward propagation, finite gradient verification, and AdamW optimizer parameter updates.

---

## 2. 11-Point Evaluation Summary

| # | Evaluation Dimension | Status | Key Metric / Finding |
|---|----------------------|:------:|----------------------|
| 1 | **Actual Pretrained Model Loading** | **PASSED** | 141,896,450 params loaded in 0.34s; backbone weights 100% intact; classification head randomly initialized. |
| 2 | **Real Tokenizer & Dataset Input** | **PASSED** | Tokenizer loaded in 166.8ms; real text tokenized (62–100 active tokens); label mapping strictly adhered to schema. |
| 3 | **Forward Pass** | **PASSED** | Average forward latency: 177.5 ms; clean logits and loss values ([0.5788 to 0.8187]). |
| 4 | **Backward Pass** | **PASSED** | Average backward latency: 286.3 ms; reverse-mode autograd through all 12 transformer layers. |
| 5 | **Optimizer Step** | **PASSED** | AdamW parameter updates verified; non-zero weight deltas (0.00033 to 0.00073). |
| 6 | **Gradient Integrity** | **PASSED** | 100% finite gradients (no NaN, no Inf); non-zero gradients across 106/106 trainable parameter tensors; L2 norm: 8.92 to 11.54. |
| 7 | **Peak Memory & Swap Safety** | **PASSED** | Peak RSS: 2,370 MB (~2.31 GB); Available RAM maintained > 4,597 MB (well above 700 MB abort limit); Swap drift: +200 MB. |
| 8 | **CPU Throughput** | **MEASURED** | Overall: 0.71 samples/sec (2,552 samples/hr); Steady-state: 0.87 samples/sec (3,130 samples/hr) on 4 threads. |
| 9 | **Binary Objective Readiness** | **CONDITIONALLY_PASSED** | Mathematically & architecturally ready; CPU training feasible for pilots/small subsets; 1 epoch of 26k examples takes ~8.3 to 10.2 hrs on CPU. |
| 10 | **NLI Objective Readiness** | **NOT_READY** | Requires 3-class classification head (`num_labels=3`), premise/hypothesis formatting, and separate pilot. |
| 11 | **Span Objective Readiness** | **BLOCKED** | Requires token-level classification head (`DebertaV2ForTokenClassification`) and resolution of token-character alignment gap. |

---

## 3. Telemetry Highlights

- **Total Steps Executed:** 3 / 3 (batch size 1, sequence length 128, seed 42)
- **Total Elapsed Execution Time:** 6.83 seconds
- **Pre-pilot Available RAM:** 6,122.45 MB
- **Peak Process RSS:** 2,369.99 MB (~2.31 GB)
- **Post-pilot Available RAM:** 4,629.59 MB (safety margin > 4.5 GB)
- **Swap Drift:** +200.68 MB (Swap used: 2,848.6 MB / 6,000 MB, plenty of free headroom)
- **Average Step Latency:** 1,410.6 ms (Fwd: 177.5 ms, Bwd: 286.3 ms, Opt: 808.1 ms)
- **Steady-State Step Latency:** ~1,145.4 ms (after initial AdamW state allocation)
