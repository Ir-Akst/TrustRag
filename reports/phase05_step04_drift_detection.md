# Phase 05 — Step 04: Distribution and Attack Drift Detection

**Date:** 2026-11-11  
**Branch:** `phase-5`  
**Status:** PASS (Observational PSI/KS/JSD monitor verified; zero false attack-drift alerts)

---

## 1. Subsystem Architecture

Step 4 implements passive sliding-window drift detection in [drift.py](file:///home/aditya/rags/TrustRag/src/trustrag/adaptive/drift.py) across all 9 telemetry streams (`F1_perplexity`, `F2_embedding_norm`, `F3_query_match`, `F4_instruction_risk`, `F5_consensus_dev`, `F6_provenance`, `G2_trust_score`, `G3_verdict`, `retrieval_quality`).

### Statistical Design & Privacy Controls
- **Continuous streams (`F1`–`F5`, `G2_trust_score`, `retrieval_quality`):** Smoothed Population Stability Index (`PSI >= 0.25`, `eps=1e-2`) paired with two-sample Kolmogorov–Smirnov (`ks_stat >= 0.28` and `p < 0.05`).
- **Categorical streams (`F6_provenance`, `G3_verdict`):** Bounded base-2 Jensen–Shannon divergence (`JSD >= 0.15`).
- **Small-sample suppression:** Windows with `min(baseline_n, current_n) < min_samples` (`15`) emit `classification = "insufficient_sample"` and `recommended_action = "none"`.
- **Attack vs Benign Separation:** Attack drift requires rising security indicators (`F4` high-risk surge >= `+0.10`, or dual `G2_trust` drop + `F5` drop, or statistically significant `F5_consensus_dev` collapse `<= -0.18`). Clean relevance/domain changes classify cleanly as `"benign_distribution_drift"` or `"quality_degradation"` without false attack alarms.
- **Zero Query-Text Retention & Passive Guarantee:** `TelemetryRecord` retains only numeric metrics and categorical state labels (zero raw query/document text), and `DriftMonitor` never mutates G1/G2/G3 decisions silently.

---

## 2. Experimental Evidence Across Live Streams (`reports/evaluation/phase05_step04_drift.json`)

Clean baseline (`n = 180` candidate telemetry records from `boolq/validation[0:25]`) evaluated against five distinct operational windows:

| Window Scenario | Samples (`n`) | Classification | Severity | Action | Confidence | Drifted Streams |
| :--- | :---: | :--- | :--- | :--- | :---: | :--- |
| `boolq_val_in_distribution` (`[25:50]`) | `120` | **`stable`** | `none` | `none` | `0.48` | `[]` |
| `clean_rag_val_domain_shift` | `26` | **`quality_degradation`** | `moderate` | `propose_review` | `0.84` | `F3, F5, F6, G2_trust, rq` |
| `adv_val_attack_stream` | `36` | **`suspected_attack_drift`** | **`high`** | **`tighten_thresholds`** | **`0.95`** | `F3, F4, F5, F6, G2_trust, rq` |
| `kp_val_attack_stream` | `16` | **`suspected_attack_drift`** | **`moderate`** | **`propose_review`** | **`0.95`** | `F3, F5, F6, G2_trust, rq` |
| `small_sample_n5` | `5` | **`insufficient_sample`** | `insufficient_sample` | `none` | `0.3333` | `[]` |

- **In-distribution false drift alert rate:** `0%` (`boolq_val_in_distribution` cleanly classified `stable` with `0` drifted streams).
- **Benign domain shift false attack-drift alert rate:** `0%` (`clean_rag/val` flagged `quality_degradation` / `log_only`/`propose_review`, never `suspected_attack_drift`).
- **Disabled upstream signals (`F1`, `F2`):** Automatically marked `insufficient_sample=True` without emitting errors or spurious drift alerts.

---

## 3. Focused & Regression Verification

- **Focused tests:** `PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest tests/unit/test_phase_05_step04_drift.py -W error -v` -> **`3 passed` in `0.81s`**.
- **Full regression:** `PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest -W error -q` -> **`321 passed, 2 deselected` in `7.96s`**, exit `0`.
- **Static typing:** `PYTHONPATH=src /home/aditya/rags/.venv/bin/mypy src/trustrag/ --ignore-missing-imports` -> **`Success: no issues found in 79 source files`**, exit `0`.

---

## 4. Step 4 Acceptance Decision

- [x] PSI, KS, JSD, and sliding-window calculations validated on real clean and attack streams.
- [x] Small-sample (`n=5 < 15`) and disabled-signal (`F1`, `F2`) behaviors handled cleanly.
- [x] `0%` false drift alert on held-out in-distribution BoolQ and `0%` false attack alert on clean domain shift.
- [x] Monitoring strictly observational (`DriftMonitor` never mutates security decisions silently).

**Acceptance Verdict:** **PASS** — Proceed to Step 5 (Adversarial Adaptation Evaluation).

