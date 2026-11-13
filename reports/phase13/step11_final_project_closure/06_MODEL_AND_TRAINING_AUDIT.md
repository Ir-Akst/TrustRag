# TrustRAG Phase 13 Step 11 — Neural Model & Training Reality Audit

**Target Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Auditor:** Independent Senior ML Research Evaluator & Model Auditor  
**Audit Dimension:** Checkpoint Inventory, Training Pipelines, and Inference Backends  
**Evaluation Date:** 2026-11-13  
**Overall Model Status:** **BLOCKED (0 TRAINED NEURAL WEIGHTS / 0 TRAINING SCRIPTS)**  

---

## 1. Executive Summary

TrustRAG's architectural documentation and referenced research papers specify multiple neural machine learning components:
1. A **Small Reasoning Model (SRM)** (`Qwen/Qwen2.5-3B-Instruct`) utilizing `<think>` reasoning tags and trained via ORPO + LoRA on synthetic reasoning datasets (`FineWeb -> Dclean -> HalluClaim`).
2. A **Dense Embedding Model** for FAISS-based semantic vector retrieval and embedding-norm anomaly detection (F2).
3. A **Neural Autoregressive LLM** for generative RAG answer synthesis and perplexity anomaly detection (F1).
4. An **SLM Filter Model** for comparative baseline execution (`FilterRAG` and `ML-FilterRAG`).

**Audit Finding:**  
A exhaustive search across the repository filesystem, virtual environments, and host Hugging Face cache reveals:
- **Zero neural model checkpoints or weights exist** (`*.pt`, `*.safetensors`, `*.bin`, `*.gguf`).
- **Zero training or fine-tuning scripts exist** (no ORPO, LoRA, DPO, or SFT scripts).
- **Core deep learning frameworks are absent** (`torch`, `transformers`, `peft`, `trl` are neither installed in the active environment nor packaged as local dependencies).
- **All neural inference calls execute via deterministic CPU fallback proxies or are marked `UNAVAILABLE`**.

---

## 2. Model & Checkpoint Reality Matrix

| Model Component | Target Architecture | Local Checkpoints Found? | Training Pipeline Found? | Active Inference Backend | Real Model or Fallback? | Audit Status |
|---|---|---|---|---|---|---|
| **Small Reasoning Model (SRM)** | `Qwen/Qwen2.5-3B-Instruct` | **0 Found** | **0 Scripts** | `DeterministicFallbackBackend` | **DETERMINISTIC FALLBACK** | **BLOCKED** |
| **Dense Vector Embedder** | e.g. `bge-small-en-v1.5` | **0 Found** | None | `TfidfVectorizer` (scikit-learn) | **HEURISTIC PROXY** | **FALLBACK** |
| **Generative LLM Generator** | `Qwen` / `Llama` / API | **0 Found** | None | Extractive Sentence Copier | **HEURISTIC PROXY** | **FALLBACK** |
| **G2 F1 Perplexity Model** | Causal LM Loss | **0 Found** | None | `UNAVAILABLE` (Bypassed) | **NONE (OFFLINE SKIP)** | **UNAVAILABLE** |
| **G2 F2 Embedding Norm Model** | Transformer Embeddings | **0 Found** | None | `UNAVAILABLE` (Bypassed) | **NONE (OFFLINE SKIP)** | **UNAVAILABLE** |
| **ML-FilterRAG Classifier** | Intermediate SLM | **0 Found** | Logistic Regression | Scikit-learn LogisticRegression | **SHALLOW PROXY** | **PROXY ONLY** |
| **Adaptive Calibrators** | Platt / Temperature | JSON files | Offline fit on 8 samples | Static JSON Parameters | **STATIC SCALARS** | **VERIFIED** |

---

## 3. Deep-Dive Audit of Specific Model Subsystems

### 3.1 Neural Small Reasoning Model (SRM) (`src/trustrag/srm/client.py`)
- **Claimed Architectural Role:** Evaluates extracted candidate claims against retrieved context within `<think>` tags, assigning 5-class span judgments (`SUPPORTED`, `CONTRADICTED`, etc.).
- **Software Implementation:** `SRMClient` contains well-written connection classes for `hf_local`, `local_ollama`, and `openai_compatible`, as well as a `<think>` tag parser.
- **Physical Reality:**
  - `hf_local`: Fails immediately because no local checkpoint exists and `torch` is not installed.
  - `local_ollama`: Fails with connection refusal (no local Ollama daemon running on host).
  - `openai_compatible`: Fails because no external API keys are configured.
  - Active Execution: Runs `DeterministicFallbackBackend` (`halluguard-srm-fallback`), which performs string matching and keyword heuristics.
- **Audit Verdict:** The software interface is ready, but neural execution is **BLOCKED**.

### 3.2 Model Training, Fine-Tuning & Weights
- **Claimed Methodology:** Paper A specifies ORPO (Odds Ratio Preference Optimization) with LoRA rank 16 on synthetic triples.
- **Codebase Reality:**
  - A recursive search across the repository found **0 training scripts** (`training_scripts_found: []`).
  - No loss functions, optimizer loops, gradient accumulation routines, or evaluation callbacks exist in `src/`.
  - The repository contains only two static calibration files: `configs/adaptive/platt_calibrator_v1.json` and `temperature_calibrator_v1.json`. These are 1-parameter logistic regression coefficients fitted on synthetic micro-fixtures.

### 3.3 FilterRAG & ML-FilterRAG Baselines (`evaluation/filterrag_experiment.py`)
- **Claimed Methodology:** Replicating Paper C (`2508.02835v2`), where an intermediate SLM computes frequency density `a_j = SLM(q_i, d_j)`.
- **Codebase Reality:**
  - `MSDConfig.enable_freq_density` defaults to `False`.
  - In offline mode, FilterRAG defaults to `BLOCKED_NO_LIVE_SLM`.
  - `ML_FilterRAG` was executed solely as a shallow `scikit-learn` logistic regression over 4 heuristic features, achieving an AUC of `0.2990` (below random guessing).
- **Audit Verdict:** FilterRAG comparative baselines are **PROXY_ONLY** heuristics, not authentic neural baselines.

---

## 4. Why Fallbacks Cannot Be Equated to Neural Models

In academic literature and enterprise AI, evaluating a deterministic fallback (e.g. TF-IDF word matching) and reporting the results under the name of a neural model (e.g. `Qwen-2.5-3B-Instruct`) constitutes an invalid claim.

| Dimension | Neural SRM Claim | Actual Fallback Reality |
|---|---|---|
| **Inference Compute** | GPU Matrix Multiplications (3B parameters) | CPU String Split and Regex Overlap |
| **Reasoning Capacity** | Multi-hop inference & semantic entailment | Literal token matching |
| **Execution Latency** | $\sim 200\text{ ms} - 1,500\text{ ms}$ per prompt | $\sim 0.05\text{ ms}$ per sentence |
| **Adversarial Resilience** | Susceptible to semantic adversarial manipulation | Immune to semantic evasion; brittle to syntax changes |

---

## 5. Audit Conclusion

The neural model and training subsystem is **BLOCKED**. TrustRAG operates entirely as a deterministic, rule-based, CPU-bound software pipeline. Release claims must clearly state that all neural capabilities are running in deterministic fallback mode.

