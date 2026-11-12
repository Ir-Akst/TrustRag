# TrustRAG Phase 10 — G3 Evidence & Claim Verification Report

**Run ID:** `phase10_20261112T073204Z_canonical_v2`

## 1. Phase 08 Linguistic Generalization Suite (`n=25`)
- **Total Cases:** `25` | **Passed:** `25/25` (`1.0000`) | **False Supported Count:** `0`
- **Latency:** Mean `4.1236 ms`, `p50=2.1837 ms`, `p95=14.4834 ms`, `p99=14.9943 ms`.

## 2. Unseen Numeric / Temporal / Insufficient Probes (`n=4`, Exploratory)
- **Claim Accuracy:** `0.5000` | **Macro-F1:** `0.5000` | **False-Supported Rate:** `0.0000` | **False-Contradicted Rate:** `0.0000` | **Unsupported-Claim Recall:** `1.0000`
- **Supported Precision:** `1.0000` | **Mean Latency:** `2.6532 ms`
- **Per-Probe Breakdown:**
  - `unseen_num_exact` (`100C` vs `100C`): `SUPPORTED` (correct)
  - `unseen_insufficient` (`2030 tournament` vs `2024 Madrid`): `INSUFFICIENT_EVIDENCE` (correct)
  - `unseen_num_contra` (`85C` vs `100C`): predicted `INSUFFICIENT_EVIDENCE` instead of `CONTRADICTED`
  - `unseen_temp_contra` (`2018` vs `1998`): predicted `INSUFFICIENT_EVIDENCE` instead of `CONTRADICTED`

**Finding:** G3 strictly preserves zero false `SUPPORTED` verdicts (`false_supported_rate = 0.0000`), safely abstaining (`INSUFFICIENT_EVIDENCE`) on unseen numeric/temporal mismatches rather than hallucinating support, though strict `CONTRADICTED` classification on bare numeric/year mismatches without explicit negation cues remains conservative.
