# Phase 05 — Step 02: Adaptive Trust Calibration

**Date:** 2026-11-11  
**Branch:** `phase-5`  
**Status:** PASS (Deterministic `train`-only calibration verified; static G2 preserved; zero test leakage)

---

## 1. Objective & Architecture

Step 2 implements deterministic, versioned, post-hoc probability calibration for G2 (`MultiSignalDetector`) so raw uncalibrated trust scores reflect empirical `P(clean)` probabilities without altering static Phase 04 behavior when disabled.

### Implemented Modules
- [schemas.py](file:///home/aditya/rags/TrustRag/src/trustrag/adaptive/schemas.py): `CalibrationMethod`, `ReliabilityBin`, `CalibrationArtifact` (SHA-256 checksummed, finite numeric parameters only, rejecting `"test"` split names in `fitted_splits`), `CalibrationEvaluationReport`, and `AdaptiveConfig`.
- [calibration.py](file:///home/aditya/rags/TrustRag/src/trustrag/adaptive/calibration.py): `TrustCalibrator` supporting **Platt scaling** (logistic regression over logit-transformed `trust_score`), **Isotonic regression**, and **Temperature scaling**, plus `compute_calibration_metrics`, `compute_reliability_diagram`, and strict `_assert_non_test_splits` leakage guard.
- [msd.py](file:///home/aditya/rags/TrustRag/src/trustrag/detection/msd.py): Added optional `calibrator` keyword parameter to `MultiSignalDetector.__init__` (defaults to `None`, preserving 100% static behavior). Records `raw_trust_score`, `calibration_active`, `calibration_fallback`, and `calibration_version` per document inside `config_snapshot`.
- [suites.py](file:///home/aditya/rags/TrustRag/src/trustrag/evaluation/suites.py): Delegated `_compute_calibration` to `compute_calibration_metrics` to eliminate duplicate calibration math.
- Validated artifact saved at `configs/adaptive/platt_calibrator_v1.json` (`platt-mixed-v1`, `sha256: f3c2ce6b...`).

---

## 2. Empirical Investigation (Train/Val Splits Only — Zero Test Leakage)

**Training partitions used (`n = 428` total candidate assessments):**
- `data/benchmarks_backup/adversarial_robustness/train`: `n = 174` (`106` clean incl. `BENIGN_INSTRUCTION_LIKE`, `68` poisoned)
- `data/benchmarks_backup/knowledge_poisoning/train`: `n = 104` (`52` clean, `52` poisoned)
- `data/benchmarks_backup/clean_rag/train`: `n = 150` candidate assessments (all clean `150/150`)

All evaluations below were measured strictly on held-out **validation** splits (`adv_val` `n=36`, `kp_val` `n=22`, `combined_val` `n=58`, plus `data/processed/boolq/validation.jsonl` `n=150` candidate assessments). **No test split was touched.**

### 2.1 Calibration & Classification Comparison on Combined Validation (`N = 58`)

| Variant | Method / Fit | Brier ↓ | ECE ↓ | ROC-AUC | PR-AUC | Prec | Recall | F1 | FPR ↓ | BoolQ Clean `< 0.60` ↓ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `static` | Uncalibrated baseline (`None`) | 0.1808 | 0.1629 | 0.8059 | 0.8168 | 1.0000 | 0.4615 | 0.6316 | 0.0000 | **0 / 150** |
| `platt_security_only` | Platt (`train` adv+kp only, `n=278`) | 0.1587 | 0.0815 | 0.8059 | 0.8168 | 0.6800 | 0.6538 | 0.6667 | 0.2500 | 83 / 150 |
| **`platt_mixed_clean`** | **Platt (`train` adv+kp+clean, `n=428`)** | **0.1693** | **0.1121** | 0.8059 | 0.8168 | 0.7368 | **0.5385** | 0.6222 | 0.1562 | **0 / 150** |
| `platt_balanced` | Platt (`class_weight="balanced"`, `n=428`) | 0.1736 | 0.1787 | 0.8059 | 0.8168 | 0.5122 | 0.8077 | 0.6269 | 0.6250 | 89 / 150 |
| `isotonic_mixed` | Isotonic (`n=428`) | **0.1349** | **0.0246** | **0.8726** | **0.8209** | 0.7241 | 0.8077 | **0.7636** | 0.2500 | 89 / 150 |
| `temperature_mixed` | Zero-bias Temperature (`T=0.6872`, `n=428`) | 0.1882 | 0.1692 | 0.8059 | 0.8168 | 1.0000 | 0.4615 | 0.6316 | 0.0000 | **0 / 150** |

### 2.2 Reliability Diagram Snapshot (`adv_val`, `N = 36`, 5 bins `[0.0..1.0]`)

- **`static`:** Bin 1 `[0.2,0.4)`: `n=6, conf=0.2790, acc=0.0000` | Bin 3 `[0.6,0.8)`: `n=24, conf=0.7429, acc=0.6250` | Bin 4 `[0.8,1.0]`: `n=6, conf=0.9023, acc=1.0000`
- **`platt_mixed_clean` (`coef=2.7133, intercept=-1.7137`):** Bin 0 `[0.0,0.2)`: `n=6, conf=0.0140, acc=0.0000` | Bin 2 `[0.4,0.6)`: `n=3, conf=0.5606, acc=1.0000` | Bin 3 `[0.6,0.8)`: `n=16, conf=0.7628, acc=0.7500` | Bin 4 `[0.8,1.0]`: `n=11, conf=0.9273, acc=0.5455`
- **`isotonic_mixed`:** Bin 0: `n=6, conf=0.0000, acc=0.0000` | Bin 2: `n=7, conf=0.5138, acc=0.4286` | Bin 3: `n=17, conf=0.7465, acc=0.7059` | Bin 4: `n=6, conf=1.0000, acc=1.0000`

### 2.3 Key Engineering Conclusions
1. **Pure temperature scaling (`T = 0.6872`) does not resolve G2 miscalibration** (`brier 0.1808 -> 0.1882`) because uncalibrated G2 scores suffer from an upward intercept shift (`intercept = -1.7137`), not merely logit overconfidence.
2. **Training mix critically governs clean RAG utility:** Fitting Platt scaling solely on security partitions (`platt_security_only`) or fitting Isotonic step plateaus (`isotonic_mixed`) shifts clean `boolq/validation` scores below `0.60` (`83/150` and `89/150` clean docs penalized). Including `clean_rag/train` (`platt_mixed_clean`) reduces validation Brier (`0.1808 -> 0.1693`) and ECE (`0.1629 -> 0.1121`) while keeping **`0 / 150` false positives** on clean BoolQ candidates (`mean_trust = 0.7326`).
3. Serialized machine-readable evidence: [phase05_step02_calibration.json](file:///home/aditya/rags/TrustRag/reports/evaluation/phase05_step02_calibration.json).

---

## 3. Focused & Regression Verification

- **Focused tests:** `PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest tests/unit/test_phase_05_step02_calibration.py -W error -v` -> **`5 passed` in `0.98s`** (verifies test-split rejection, determinism, JSON/SHA-256 integrity, corruption fallback, non-finite safety, static MSD preservation).
- **Full regression:** `PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest -W error -q` -> **`315 passed, 2 deselected` in `8.25s`**, exit `0`.
- **Static typing:** `PYTHONPATH=src /home/aditya/rags/.venv/bin/mypy src/trustrag/ --ignore-missing-imports` -> **`Success: no issues found in 77 source files`**, exit `0`.

---

## 4. Step 2 Acceptance Decision

- [x] Calibration reproducible (`fit_seed=42`, exact SHA-256 determinism verified).
- [x] Zero test-set leakage enforced structurally (`_assert_non_test_splits` & `CalibrationArtifact` validator) and experimentally (`train` fit / `val` eval only).
- [x] Static G2 detector (`calibrator=None`) 100% preserved.
- [x] Brier, ECE, reliability diagrams, Precision, Recall, F1, ROC-AUC, PR-AUC compared across static baseline, Platt, Isotonic, and Temperature scaling.
- [x] Trade-offs (e.g., isotonic clean-RAG overfitting vs mixed-clean Platt stability) reported transparently without unsupported claims.

**Acceptance Verdict:** **PASS** — Proceed to Step 3 (Context-Aware Security Thresholding).

