# 04 — Model, Weights, SRM & Calibration Audit

**Inventory JSON:** [model_inventory.json](file:///c:/Users/Dell/Desktop/trustrag/reports/reality_audit/model_inventory.json)
**SRM Config Defaults (`configs/base.yaml`):** `srm.enabled: true`, `srm.backend: disabled`, `srm.model_name: halluguard-srm-fallback`, `generation.mode: extractive`, `llm.default_provider: openai`, `llm.default_model: null`

---

## 1. Neural Weights & Training Script Inventory (`BLACK`)

| Search Scope | Result | Details |
| :--- | :---: | :--- |
| Workspace `.pt` / `.pth` / `.safetensors` / `.bin` / `.gguf` / `.onnx` checkpoints | **`0` found** | Zero neural network model files exist anywhere in `c:\Users\Dell\Desktop\trustrag` |
| ORPO / LoRA / QLoRA / SFT / DPO training scripts | **`0` found** | Zero PyTorch/Transformers/PEFT training pipelines exist in `src/` or `tools/` |
| Local HuggingFace model cache (`~/.cache/huggingface`) | **`0` LLMs** | Contains only `datasets--alan-turing-institute--turing-synthetic-radar-dataset` |
| Saved ML artifacts in workspace | **`2` JSON files** | `configs/adaptive/platt_calibrator_v1.json` and `temperature_calibrator_v1.json` (scalar logistic/temperature fits only) |

---

## 2. Small Reasoning Model (SRM) Backend Probes (`BLUE`)

All 4 registered SRM backends in [src/trustrag/srm/](file:///c:/Users/Dell/Desktop/trustrag/src/trustrag/srm/client.py) were directly instantiated and probed:

| Backend | Configured Model | Health `available` | `is_real_model` | Observed Behavior / Failure Reason | Latency (ms) | Verdict |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: |
| `disabled` -> `DeterministicFallbackBackend` | `halluguard-srm-fallback` | `True` | `False` | Rule-based threshold combiner (`execution_status="DISABLED"`, `is_fallback=True`, emits `CAUTION`) | `0.01 – 0.377` | `YELLOW` (Fallback only) |
| `hf_local` | `Qwen/Qwen2.5-3B-Instruct` | `False` | `True` | `"Checkpoint 'Qwen/Qwen2.5-3B-Instruct' missing locally"` + missing `torch`; `reason_with_fallback()` safely falls back (`execution_status="UNAVAILABLE"`) | `4,439.97` | `BLUE` (`NOT VERIFIED`) |
| `local_ollama` | `halluguard-srm-fallback` | `False` | `True` | `Ollama unavailable: [WinError 10013] socket access forbidden` (sandbox/no local Ollama daemon) | `697.05` | `BLUE` (`NOT VERIFIED`) |
| `openai_compatible` | `halluguard-srm-fallback` | `False` | `True` | `"Missing API credential"` (`OPENAI_API_KEY` absent / offline audit) | `0.051` | `BLUE` (`NOT VERIFIED`) |

> [!IMPORTANT]
> Because `srm.backend` defaults to `"disabled"`, **100% of passing SRM tests and Phase 10 benchmark runs executed `DeterministicFallbackBackend` (`halluguard-srm-fallback`)**, NOT a neural Small Reasoning Model.

---

## 3. Adaptive Scalar Calibrators Audit (`configs/adaptive/`)

Both JSON calibrators loaded cleanly with valid SHA-256 integrity verification. Independent out-of-sample evaluation was executed on the `test.jsonl` splits of `benchmarks_backup/knowledge_poisoning` (`n=24`) and `benchmarks_backup/adversarial_robustness` (`n=40`):

### A. Fitted Artifact Metadata & Probability Mapping
- **`platt_calibrator_v1.json` (`platt-mixed-v1`):** Fitted on `n=428` (`train` splits of `adversarial_robustness`, `knowledge_poisoning`, `clean_rag`). Steep logistic curve: `0.1 -> 0.0005`, `0.3 -> 0.0178`, `0.5 -> 0.1527`, `0.7 -> 0.6423`, `0.9 -> 0.9859`.
- **`temperature_calibrator_v1.json` (`temp-train-v1`):** Fitted on `n=478` (`train` splits). Smooth monotonic scaling: `0.1 -> 0.0318`, `0.3 -> 0.2112`, `0.5 -> 0.5000`, `0.7 -> 0.7888`, `0.9 -> 0.9682`.

### B. Verified Test-Split Performance

| Dataset (`split=test`) | Calibrator | Brier | ECE | Precision | Recall | F1 | FPR | FNR | ROC AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `knowledge_poisoning` (`n=24`, 12/12) | Raw (`none`) | `0.2132` | `0.1870` | `1.0000` | `0.3333` | `0.5000` | `0.0000` | `0.6667` | `0.6528` |
| `knowledge_poisoning` (`n=24`, 12/12) | **`platt`** | `0.1867` | `0.0521` | `0.6250` | `0.8333` | `0.7143` | **`0.5000`** | `0.1667` | `0.6528` |
| `knowledge_poisoning` (`n=24`, 12/12) | `temperature` | `0.2300` | `0.2199` | `1.0000` | `0.3333` | `0.5000` | `0.0000` | `0.6667` | `0.6528` |
| `adversarial_robustness` (`n=40`, 23c/17a) | Raw (`none`) | `0.1466` | `0.1409` | `1.0000` | `0.5882` | `0.7407` | `0.0000` | `0.4118` | `0.8951` |
| `adversarial_robustness` (`n=40`, 23c/17a) | **`platt`** | `0.1334` | `0.1119` | `0.7692` | `0.5882` | `0.6667` | **`0.1304`** | `0.4118` | `0.8951` |
| `adversarial_robustness` (`n=40`, 23c/17a) | `temperature` | `0.1467` | `0.1705` | `1.0000` | `0.5882` | `0.7407` | `0.0000` | `0.4118` | `0.8951` |

**Key Audit Finding:** `platt_calibrator_v1.json` maps moderate clean trust scores (e.g., `0.50` without provenance) down to `0.1527`, triggering severe clean false-positive spikes (`FPR = 0.50` standalone on `knowledge_poisoning`, and **`0.6667`** in Phase 10 E2E where 8 clean false positives exactly cancel 8 true positives). Meanwhile `temperature_calibrator_v1.json` preserves zero clean FPR (`0.0`) at the cost of `0.3333` recall on `knowledge_poisoning`.

