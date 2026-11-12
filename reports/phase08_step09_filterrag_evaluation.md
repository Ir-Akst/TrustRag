# TrustRAG Phase 08 Step 09 Report — FilterRAG & ML-FilterRAG Evaluation

## 1. Objective
Implement and experimentally evaluate Paper C (FilterRAG & ML-FilterRAG — Frequency Density of query/answer-related words and SLM intermediate-answer filtering) strictly in an isolated experimental harness without enabling `enable_freq_density` in production `configs/base.yaml`.

---

## 2. Architecture Summary
- **Isolated Module:** [filterrag_experiment.py](file:///home/aditya/rags/TrustRag/src/trustrag/evaluation/filterrag_experiment.py)
  - Supports genuine SLM intermediate answers `a_j = SLM(q_i, d_j)` via an explicit `slm_answer_callable` interface.
  - Refuses to mask missing SLM inference as live FilterRAG: default offline execution marks `FilterRAG_Threshold_SLM`, `ML_FilterRAG_SLM`, and `Combined_MSD_FilterRAG` explicitly as **`BLOCKED`** (`evaluation_mode="BLOCKED_NO_LIVE_SLM"`).
  - Separately exposes an explicitly labeled **`extractive_proxy`** mode (`allow_extractive_proxy=True`, top query-overlapping sentence proxy) and trains `MLFilterRAGModel` (`LogisticRegression`, `class_weight="balanced"`) strictly on non-test splits (`train`), guarding against accidental `"test"` split fitting.
  - Production default [base.yaml](file:///home/aditya/rags/TrustRag/configs/base.yaml) preserves `msd.enable_freq_density: false`.

---

## 3. Experimental Comparison (`data/benchmarks_backup`, `seed=42`)

### 3.1 Default Offline Mode (`slm_answer_callable=None`)
- `evaluation_mode`: **`BLOCKED_NO_LIVE_SLM`**
- `Original_RAG`: `COMPLETED`
- `TrustRAG_MSD`: `COMPLETED`
- `FilterRAG_Threshold_SLM`, `ML_FilterRAG_SLM`, `Combined_MSD_FilterRAG`: **`BLOCKED`** (no causal/instruct SLM available offline).

### 3.2 Extractive-Proxy Reproducibility Run (`PROXY_ONLY`, `allow_extractive_proxy=True`, `selected_eps=0.70` tuned on `val`)
Evaluated on held-out `test` security pools (`n=64`) and held-out `clean_rag/test` (`75` assessments across `15` queries x `5` docs; fitted/tuned only on `train`/`val`):

| Variant | Status | ROC-AUC | PR-AUC | Precision | Recall | F1 | Sec Clean FPR | `clean_rag/test` Retention | `clean_rag/test` FP |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`Original_RAG`** | `COMPLETED` | 0.5000 | 0.4531 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | **1.0000** | `0/75` |
| **`TrustRAG_MSD` (`temp-train-v1`)** | `COMPLETED` | **0.8315** | **0.8320** | **1.0000** | **0.4828** | **0.6512** | **0.0000** | **1.0000** | **`0/75`** |
| **`FilterRAG_Threshold` (`eps=0.70`)** | `PROXY_ONLY` | 0.6897 | 0.6606 | 1.0000 | 0.3793 | 0.5500 | 0.0000 | **0.2000** | **`60/75`** |
| **`ML_FilterRAG` (`LogReg`, `train`)** | `PROXY_ONLY` | 0.2990 | 0.3710 | 0.4167 | 0.8621 | 0.5618 | 1.0000 | 0.8000 | `15/75` |
| **`Combined_MSD_FilterRAG`** | `PROXY_ONLY` | 0.8315 | 0.8320 | 1.0000 | 0.4828 | 0.6512 | 0.0000 | **0.2000** | **`60/75`** |

---

## 4. Scientific Conclusions
1. **Extractive Proxy Hurts Utility:** Thresholding extractive `freq_density` (`eps=0.70`) falsely rejects **80% (`60/75`) of clean BoolQ multi-sentence Wikipedia paragraphs** (where background sentences dilute query-sentence token concentration), whereas `TrustRAG_MSD` preserves **100% (`75/75`)** with higher security F1 (`0.6512` vs `0.5500`).
2. **Union Offers Zero Recall Gain Here:** Combining `TrustRAG_MSD` with extractive `FilterRAG_Threshold` did not increase recall (`0.4828` unchanged) while degrading clean retention (`1.0000 -> 0.2000`).
3. **ML-FilterRAG Fragility Under Length Shift:** `ML_FilterRAG` suffered `1.0000` security clean FPR under domain/length shift between training splits and multi-sentence passages (`ROC-AUC=0.2990`).
4. **Live SLM FilterRAG Remains `BLOCKED`:** True Paper C evaluation with generative `a_j = SLM(q_i, d_j)` requires a live SLM backend, so keeping `msd.enable_freq_density: false` in production `configs/base.yaml` is empirically justified.

---

## 5. Verification
- **Unit Tests:** [test_phase_08_step09_filterrag.py](file:///home/aditya/rags/TrustRag/tests/unit/test_phase_08_step09_filterrag.py): **4 passed in 1.50s** (`pytest -W error -q`), testing `configs/base.yaml` isolation, `BLOCKED` offline status, injectable SLM test double, split leakage guard, and extractive-proxy utility trade-off.
- **Type Check (`mypy`):** **2/2 source files passed**.
- **Lint (`ruff check`):** **All checks passed**.
