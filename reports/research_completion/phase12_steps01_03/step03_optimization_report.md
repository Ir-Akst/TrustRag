# TrustRAG Phase 12 — Step 03: ONNX Conversion & CPU Optimization Report

**Role:** Principal ML Systems Engineer & Performance Optimization Specialist  
**Date:** November 18, 2026  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-12` | **HEAD:** `aba5cc9d`  
**Source Model:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  
**Benchmark Artifact:** `reports/research_completion/phase12_steps01_03/step03_onnx_benchmark.json`

---

## 1. Executive Summary & Optimization Objectives

Step 03 investigates the computational efficiency of the frozen DeBERTa-v3-small NLI model on CPU architectures, addressing the following targets:
1. Feasibility of ONNX format export for graph-level kernel optimization.
2. Quantization performance (INT8 dynamic quantization) vs FP32 baseline.
3. Prediction agreement, accuracy preservation, and memory footprint.
4. Investigation of whether end-to-end neural verification latency can be compressed below the **$50\text{ ms}$** target.

---

## 2. Model Conversion & Framework Status

### 2.1 ONNX Export Investigation
Both the PyTorch 2.x TorchDynamo ONNX exporter and the legacy TorchScript ONNX exporter were evaluated:
- **Dynamo Engine (`torch.onnx.export(..., dynamo=True)`):** Failed with `ModuleNotFoundError: No module named 'onnxscript'`.
- **Legacy Engine (`torch.onnx.export(..., dynamo=False)`):** Failed with `ModuleNotFoundError: Module onnx is not installed!`.

> [!NOTE]
> **Audit Integrity Standard:**
> Because the secure testing environment enforces strict read-only package boundaries (`Do NOT install packages or download external models`), third-party ONNX wheels were **not installed**. In accordance with audit instructions (*"If any component cannot be completed safely, report it separately rather than hiding the failure"*), the ONNX conversion status is objectively recorded as **`BLOCKED_OFFLINE_DEPENDENCY`**.

### 2.2 PyTorch INT8 Dynamic Quantization
PyTorch native dynamic quantization (`torch.quantization.quantize_dynamic`) was successfully applied to all linear projections across DeBERTa's transformer layers:
- **Method:** Dynamic INT8 weight quantization (`dtype=torch.qint8`) applied to `torch.nn.Linear` modules.
- **Exported Artifact:** `/home/aditya/rags/models/experimental/deberta-v3-small-nli-quantized/quantized_int8_state_dict.pt`
- **Artifact SHA-256:** `6bb058a2d0f8e72989777d97b816d6f211ee075493ee1d7820b924c5c48684c1`
- **Storage Footprint:** Compressed from **$567.4\text{ MB}$** (FP32 safetensors) to **$438.5\text{ MB}$** (INT8 state dict), achieving a **$22.72\%$ storage reduction**.

---

## 3. Quantitative Performance & Fidelity Benchmarks

Benchmarking was conducted across 100 validation pairs from `data/processed/sft_v2/nli/validation.jsonl` on an AMD EPYC 7B13 CPU:

### 3.1 Latency Distribution Comparison

| Model Architecture / Mode | Mean Latency | Median (P50) | P95 Latency | P99 Latency | Relative Speedup |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **PyTorch FP32 Baseline** | $340.54\text{ ms}$ | $335.77\text{ ms}$ | $380.94\text{ ms}$ | $429.75\text{ ms}$ | Baseline ($1.0\times$) |
| **PyTorch INT8 Quantized** | **$304.12\text{ ms}$** | **$302.33\text{ ms}$** | **$337.22\text{ ms}$** | **$390.40\text{ ms}$** | **$+10.69\%$ faster** |

### 3.2 Classification Fidelity & Prediction Agreement
- **Prediction Agreement (FP32 vs INT8):** **$94 / 100$ ($94.00\%$)** of all categorical predictions remained identical after dynamic quantization.
- **Validation Accuracy:**
  - FP32 Accuracy: **$63.00\%$** ($63 / 100$)
  - INT8 Accuracy: **$62.00\%$** ($62 / 100$)
  - Accuracy Delta: **$-1.00\%$** (negligible degradation).

---

## 4. Feasibility Analysis of the $50\text{ ms}$ Latency Target

A primary mandate was to investigate whether single-query end-to-end neural verification latency could be reduced below **$50\text{ ms}$** on CPU:

### 4.1 Findings & Engineering Reality
1. **Single-Sample Sequential Latency:** Under INT8 dynamic quantization, the achieved median CPU latency is **$302.33\text{ ms}$**, which is **$6.05\times$ above the $50\text{ ms}$ threshold**.
2. **DeBERTa-v3 Disentangled Attention Bottleneck:**
   Unlike standard BERT models where attention is computed as $\text{Softmax}(QK^T / \sqrt{d})V$, DeBERTa-v3 computes attention as:
   $$A_{i,j} = Q_i K_j^T + Q_i R_{i-j}^T + K_j R_{j-i}^T$$
   These three separate matrix multiplications and relative-position indexing lookups remain high-precision floating-point operations. On CPU, INT8 quantization accelerates the linear feed-forward projections, but the attention kernel and layer normalization operations dominate execution time.
3. **Amortized Batched Execution:**
   When queries are evaluated in batches ($B=16$), throughput reaches **$46.80\text{ samples/sec}$**, which yields an amortized latency of **$21.36\text{ ms per sample}$**.
4. **Target Verdict:** The $50\text{ ms}$ target is **REJECTED for single-sample synchronous CPU execution**. Achieving sub-50ms single-sample latency requires dedicated ONNX Runtime fused attention kernels with AVX-512 VNNI support or GPU inference.

---

## 5. Optimization Recommendations

1. **Retain Hybrid Dual-Track Verification:** In synchronous interactive serving where $3.5\text{ ms}$ response times are mandatory, use heuristic verification as the primary synchronous path and dispatch neural NLI asynchronously or in batched background audits.
2. **Batching for Offline Evidence Screening:** Where neural verification is applied, batch claim-evidence pairs in blocks of $16$ to achieve effective $< 25\text{ ms}$ per-pair throughput.
3. **Future Production Staging:** When external wheels can be approved, compile the model via `onnxruntime` with `float16` or `int8` fused attention kernels (`DebertaOptimizationModel`) to unlock sub-50ms CPU execution.

