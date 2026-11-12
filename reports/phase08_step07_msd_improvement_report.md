# TrustRAG Phase 08 Step 07 Report — MSD Security Recall Improvement

## 1. Objective
Address the Phase 07 G2 Multi-Signal Detector (MSD) bottlenecks without weakening security invariants or inflating clean false positives:
1. Investigate calibration parameters causing clean false positives (`platt-mixed-v1`).
2. Support usable F2 embedding-norm evaluation when dense embeddings or sublinear local representations exist, while keeping external causal-LM perplexity (`F1`) honestly `BLOCKED` offline.
3. Differentiate `F6` provenance priors meaningfully when document metadata exists while preserving `UNKNOWN / None` for absent metadata.
4. Improve `F5` consensus deviation sensitivity on asymmetric minority outliers without penalizing symmetric `50/50` ties or homogeneous clean queries.
5. Preserve capped removal (`removal_cap_ratio <= 0.5`).

---

## 2. Root-Cause Findings & Architectural Changes

### 2.1 Zero-FP Temperature Calibration (`temp-train-v1`)
- **Root Cause (`platt-mixed-v1`):** `configs/adaptive/platt_calibrator_v1.json` (`platt_coef=2.71326212`, `platt_intercept=-1.71367122`) shifted borderline clean scores downward past `trust_threshold=0.60`, causing held-out test false positives (`FPR=0.2571`, `9/35` on security clean controls and `14/75` on `clean_rag/test`).
- **Fix:** Fitted `TrustCalibrator` strictly on `train` partitions (`adversarial_robustness`, `knowledge_poisoning`, `clean_rag`, `n=478`: `358` clean, `120` attack, `fit_seed=42`) using `"temperature"` scaling and saved [temperature_calibrator_v1.json](file:///home/aditya/rags/TrustRag/configs/adaptive/temperature_calibrator_v1.json) (`version="temp-train-v1"`, `temperature=0.64315401`, `artifact_sha256="765492884a18dff4034e2661a887ac16c0bfce635a7c22"`). `platt_calibrator_v1.json` remains intact for backward-compatible Phase 05/06 tests.

### 2.2 F6 Provenance Metadata Differentiation
- **Change:** Enhanced [`evaluate_provenance_signal`](file:///home/aditya/rags/TrustRag/src/trustrag/detection/signals.py) to evaluate domain suffix matches in `provenance_priors`, `trust_tier`/`provenance_tier` (`high/tier_1 -> 0.90`, `medium/tier_2 -> 0.65`, `low/tier_3 -> 0.25`), `source_type` (`official_docs/peer_reviewed/academic/government -> 0.85`, `news/editorial -> 0.70`, `blog/forum/user_generated/anonymous -> 0.30`), and authoritative `domain`/`source_domain` indicators (`.gov`, `.edu`, `docs.`, `arxiv.org`, `nih.gov`, `wikipedia.org` -> `0.85`).
- **Honesty Guard:** Documents lacking provenance/metadata continue to return `available=False`, `value=None`, `status="UNKNOWN"`.

### 2.3 F2 Embedding-Norm Backend & F5 Minority-Outlier Consensus Attenuation
- **F2 (`tfidf_sublinear` + `callable`):** Added `"tfidf_sublinear"` to [`MSDConfig`](file:///home/aditya/rags/TrustRag/src/trustrag/config/engine_config.py) and [`MultiSignalDetector._resolve_doc_embeddings`](file:///home/aditya/rags/TrustRag/src/trustrag/detection/msd.py), normalizing sublinear TF-IDF vectors by `sqrt(token_count)` so vector norms do not trivially track passage length; preserved `"tfidf_raw"` and `"require_configured"` defaults, while dense `embedding_callable` and `doc_embeddings` remain first-class. Causal-LM `F1` (`perplexity_backend="disabled"`) remains `BLOCKED` offline.
- **F5 Minority-Outlier Attenuation:** In [`MultiSignalDetector.assess_candidates`](file:///home/aditya/rags/TrustRag/src/trustrag/detection/msd.py), when `enable_minority_outlier_attenuation=True`, a candidate flagged with `"MINORITY_OUTLIER"` (`F5 <= 0.25`) in a pool where `>= 2` peers hold high consensus (`F5 >= 0.70`) receives `minority_outlier_consensus_multiplier=4.0` on `F5` and reason code `"G2_MINORITY_OUTLIER_ATTENUATED"`. Symmetric `50/50` ties lack a majority peer quorum (`0` peers `>= 0.70`) and are unaffected.

---

## 3. Validation-First & Held-Out Test Metrics

| Split / Configuration | Sec `n` | ROC-AUC | PR-AUC | Precision | Recall | F1 | Sec FPR | `clean_rag` FP |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`val` — `uncalibrated`** | 58 | 0.8059 | 0.8168 | 1.0000 | 0.4615 | 0.6316 | 0.0000 (`0/32`) | `0/75` |
| **`val` — `platt-mixed-v1`** | 58 | 0.8059 | 0.8168 | 0.7368 | 0.5385 | 0.6222 | 0.1562 (`5/32`) | `0/75` |
| **`val` — `temp-train-v1`** | 58 | 0.8059 | 0.8168 | 1.0000 | 0.4615 | 0.6316 | **0.0000 (`0/32`)** | **`0/75`** |
| **`test` — `uncalibrated`** | 64 | 0.8315 | 0.8320 | 1.0000 | 0.4828 | 0.6512 | 0.0000 (`0/35`) | `0/75` |
| **`test` — `platt-mixed-v1`** | 64 | 0.8315 | 0.8320 | 0.6897 | 0.6897 | 0.6897 | 0.2571 (`9/35`) | `14/75` |
| **`test` — `temp-train-v1`** | 64 | 0.8315 | 0.8320 | **1.0000** | 0.4828 | 0.6512 | **0.0000 (`0/35`)** | **`0/75`** |

### Asymmetric Majority-Consensus Poisoning (`3` clean peers + `1` poisoned outlier on `knowledge_poisoning`)
- **Before minority-outlier attenuation (baseline `val`):** `1/3` poisoned outliers dropped below `trust_threshold=0.60` (`2/3` pure factual substitutions remained at `0.8198` and `0.8264`).
- **After Step 07 (`temp-train-v1` + `G2_MINORITY_OUTLIER_ATTENUATED`):**
  - `val`: **`3/3` detected** (`p0` trust scores: `0.4706`, `0.4882`, `0.5470 < 0.60`; clean peer trust `>= 0.9795`).
  - `test`: **`3/3` detected** (`p0` trust scores: `0.4882`, `0.4706`, `0.5470 < 0.60`; clean peer trust `>= 0.9795`).
- **Scope Boundary:** In symmetric `50/50` clean-vs-poisoned pairs lacking instruction injection, neither passage has a peer consensus majority, leaving `Active-4` symmetric recall at `14/29` (`0.4828`) until causal-LM perplexity (`F1`) or neural semantic entailment is available.

---

## 4. Verification
- **Tests:** [test_phase_08_step07_msd_improvement.py](file:///home/aditya/rags/TrustRag/tests/unit/test_phase_08_step07_msd_improvement.py) + Phase 03 defense + Phase 05 calibration: **34 passed in 1.04s** (`pytest -W error -q`).
- **Type Check:** `mypy` on edited modules + Step 07 tests: **5/5 source files passed**.
- **Lint:** `ruff check` on Step 07 tests and `--select F,B` on modified legacy modules: **All checks passed**.
- **Spec Validation:** `tools/spec_validation/run_all_validations.py`: **PASS (10/10 validators, 13/13 gates)**.
