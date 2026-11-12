# TrustRAG Phase 10 — SRM Backend Evaluation Report

**Run ID:** `phase10_20261112T073204Z_canonical_v2`

| Configuration | Backend Identity | Available | Fallback | Verdict | Latency (ms) | Status |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: |
| **Deterministic Fallback** | `deterministic_fallback` | `True` | `True` | `CAUTION` | `0.0585` | **COMPLETED** |
| **SRM Disabled (`enabled=False`)** | `deterministic_fallback` (no-op route) | `True` | `True` | `CAUTION` | `< 0.1` | **COMPLETED** |
| **Neural Local (`hf_local`)** | `Qwen/Qwen2.5-3B-Instruct` | `False` | `False` | `—` | `—` | **BLOCKED** |

**Blocked Reason:** `hf_local SRM backend requires optional dependencies 'torch' and 'transformers', which are not installed in this environment: No module named 'torch'`.

Deterministic fallback is explicitly labeled `is_fallback=True` and never represented as neural model inference. HalluGuard ORPO/LoRA reproduction remains **BLOCKED** offline.
