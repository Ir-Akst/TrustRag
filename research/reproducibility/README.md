# TrustRAG Reproducibility Guide & Evaluation Protocols

This directory contains instructions, configurations, and verification manifests required to independently reproduce all empirical findings reported in the TrustRAG research manuscript and Phase 21–27 audit reports.

---

## 1. Environment & Prerequisites

### 1.1 Hardware Specifications
- **CPU**: x86_64 architecture, minimum 4 cores (8+ recommended).
- **RAM**: Minimum 16 GB system memory.
- **GPU (Optional)**: CUDA-enabled GPU (NVIDIA RTX 3090, A100, V100, etc.) with $\ge 8$ GB VRAM for neural NLI evaluation. When absent, the system operates in CPU deterministic fallback mode.
- **Storage**: Minimum 10 GB free disk space.

### 1.2 Python Environment
- Python version: `3.10.x` (strictly required; tested with Python 3.10.12).
- Virtual environment location: `/home/aditya/rags/.venv-phase15-clean10`.

```bash
# Activation
source /home/aditya/rags/.venv-phase15-clean10/bin/activate
cd /home/aditya/rags/TrustRag-phase11
export PYTHONPATH=.:src
```

---

## 2. Frozen Checkpoints & Integrity Manifest

The research anchor checkpoint is frozen and cryptographically signed.

| File | SHA-256 Checksum |
| :--- | :--- |
| `checkpoint_meta.json` | `77d3aa663e2715767eb2e1b1d7d27e77a06f7aa566d8b2d187747bbd35272a56` |
| `config.json` | `9b56f849cf24c5e3f16fbc8a13ea2eb35ba05b0a373d6bb64c7684d081f969eb` |
| `model.safetensors` | `d720c242a42095f32eb24e4d7d130a0058b76dfb37c0eb8971fce3f8a44ca708` |
| `optimizer.pt` | `1c8bbaaa7b5b5976bfe4f6e5a04469d4d5a9daffca6ffbb3c329881643c516bc` |
| `rng_state.pt` | `e9f291e5c26b52a5ca2cae2d93eeb6d729db527c76a9537d4022ca4a44b82db1` |
| `scheduler.pt` | `f59992f96cfb33bcff5ce7f28ffb08bb25d1945bebb759dc3f1400d43f0ae90f` |
| `tokenizer.json` | `cf613c77840130dbbe06eb664aebf8ef946be41ebf108f902ea6fb3a525f257a` |
| `tokenizer_config.json` | `cefe06f2cfc3b31649646b9aeb6993be783fcb101ce1fa6d30e38a2e1d054e79` |

To verify checkpoint integrity:
```bash
python tools/evaluation/verify_checkpoint_integrity.py
```

---

## 3. Reproduction Commands

### 3.1 G1 Malicious Prompt Generalization Evaluation ($N=1000$)
To reproduce the Phase 26 benchmark evaluating 500 adversarial attack prompts and 500 benign control queries:
```bash
python tools/evaluation/run_phase26_evaluation.py
```
- **Raw Predictions Output**: `reports/phase26/raw_predictions/phase26_raw_predictions.jsonl`
- **Expected Results**:
  - Attack Detection Rate (ADR): **71.80%** (Wilson 95% CI: $[67.70\%, 75.57\%]$)
  - Attack Success Rate (ASR): **28.20%**
  - Benign Clean Delivery: **100.00%**
  - False Positive Rate (FPR): **0.00%** (Wilson 95% CI: $[0.00\%, 0.76\%]$)

### 3.2 G2 Retrieval Poisoning & Sybil Frontier Evaluation ($N=500$)
To reproduce the Sybil poisoning curve evaluating retrieval poisoning rates from 10% to 80%:
```bash
python tools/evaluation/run_phase26_sybil_frontier_benchmark.py
```
- **Expected Results**:
  - At $p \le 0.50$: 100% poison elimination, 0 poisoned passages in LLM context.
  - At $p = 0.60$: Removal cap ($C_r = 0.50$) preserves 1 poisoned passage in context.
  - At $p = 0.80$: Removal cap preserves 2 poisoned passages in context.

### 3.3 End-to-End Latency Benchmark ($N=1000$)
To verify latency characteristics across the triple-guardrail pipeline:
```bash
python tools/evaluation/run_phase25_latency_benchmark.py
```
- **Expected Results**:
  - G1 CPU Filter: $0.11$ ms median ($0.23$ ms $p99$).
  - Full Pipeline (CPU Deterministic Mode): $1.42$ ms median.

### 3.4 Unit & Integration Test Suite
To verify system integrity and zero regressions across all core components:
```bash
pytest tests/unit/ -k "test_phase_05 or test_guardrail" --tb=short -q
```
- **Expected Status**: 68 passed.

---

## 4. Architectural Transparency

- **G1 Query Guardrail**: Implemented as deterministic high-performance compiled regular expressions (`src/trustrag/guardrails/input_guardrail.py`). Latency is $0.11$ ms; does not invoke neural weights.
- **Security Response Manager (SRM)**: Running in production with `deterministic_fallback` (`is_real_model=False`). Offline DeBERTa-v3 NLI evaluations were conducted separately and are documented in research reports.
- **G2 Removal Cap**: Controlled by `max_removal_ratio=0.50` in `RobustKMeansFilter` to prevent availability denial-of-service at the expense of residual poisoning under severe Sybil attacks.
