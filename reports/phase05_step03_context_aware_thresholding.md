# Phase 05 — Step 03: Context-Aware Security Thresholding

**Date:** 2026-11-11  
**Branch:** `phase-5`  
**Status:** PASS (Bounded, deterministic, document-immune threshold selection verified)

---

## 1. Objective & Design Invariants

Step 3 implements controlled context-aware threshold selection across `G1` (`flag_threshold`, `block_threshold`), `G2` (`trust_threshold`, `poison_threshold`), and retrieval filtering (`removal_cap_ratio`) in [thresholding.py](file:///home/aditya/rags/TrustRag/src/trustrag/adaptive/thresholding.py).

### Security & Anti-Manipulation Guarantees
1. **Document-Text Immunity (`extract_context_features`):** Feature extraction inspects ONLY query structure, G1 assessment metadata, source diversity, provenance coverage, and aggregate conflict/signal statistics—**never raw retrieved document text or injected instruction strings**.
2. **Hard Bounds (`ThresholdBounds`):** All adjustments are clamped strictly within:
   - `g1_flag_threshold`: `[0.25, min(static=0.35, 0.40)]` (tighten-only)
   - `g1_block_threshold`: `[0.55, min(static=0.70, 0.75)]` (tighten-only)
   - `g2_poison_threshold`: `[max(static=0.38, 0.35), 0.50]` (tighten-only)
   - `removal_cap_ratio`: `[max(static=0.50, 0.50), 0.75]` (removal capacity preserved at `floor(K * cap_ratio)` with cap `>= 0.50`)
   - `g2_trust_threshold`: `[0.52, 0.75]` (gently stabilizes to `0.55` ONLY when `g1_risk=0.0`, `conflict_ratio=0.0`, `security_uncertainty_ratio=0.0`, `candidate_count>=3`, and high provenance/diversity; otherwise tightens up to `0.68`)
3. **Fail-Safe & Auditability:** Disabled mode (`AdaptiveMode.DISABLED`), empty candidates (`candidate_count == 0`), missing context (`None`), or invariant violation (`poison >= trust` or non-finite values) revert deterministically to `configs/base.yaml` static thresholds with `used_static_fallback=True`. Every decision is appended to `selector.audit_log`.

---

## 2. Empirical Validation Results (`val` Splits Only)

Evaluated across `data/benchmarks_backup/adversarial_robustness/val` + `knowledge_poisoning/val` (`N = 58` across 8 query groups) and clean `data/processed/boolq/validation.jsonl` (`N = 100`). Artifact: [phase05_step03_thresholding.json](file:///home/aditya/rags/TrustRag/reports/evaluation/phase05_step03_thresholding.json).

| Benchmark / Metric | Static Baseline | Context-Aware Selector | Observed Delta |
| :--- | :---: | :---: | :--- |
| Security Val (`N=58`) — `POISONED` Prec / Rec / F1 / FPR | `1.000 / 0.4615 / 0.6316 / 0.000` | `1.000 / 0.4615 / 0.6316 / 0.000` | Preserved `0.000` FPR (`8/8` query groups tightened `g2_trust: 0.60 -> 0.64`, `g2_poison: 0.38 -> 0.40`, `cap: 0.50 -> 0.60`) |
| Security Val (`N=58`) — Flagged-or-Poisoned F1 | `0.7222` | `0.7222` | Stable (`Recall=1.000`, `FPR=0.625` under sibling conflict) |
| Clean BoolQ Val (`N=100`) — `Recall@5` | `0.8200` | `0.8200` | Unchanged (`0` regression); mean candidate retention `0.794` |
| Clean BoolQ Val Threshold Distribution | `100` x `[0.60]` | `[0.55: 12, 0.60: 21, 0.62: 32, 0.64: 35]` | Deterministic adaptation (`0` invalid fallbacks) |

### Diagnostic Finding (No Overclaiming)
Adjusting thresholds alone (`0.60 -> 0.55` on clean diverse pools; `0.60 -> 0.64` on risky pools) preserves clean `Recall@5 = 0.8200` rather than reversing the `0.90 -> 0.82` Phase 04 gap, because BoolQ rank shifts stem from `G2_CONFLICT_DETECTED` cross-passage `UNCERTAIN` tiering (`tier_factor=0.65`) and `trust_weight=0.45` reranking rather than the `0.60` decision boundary. Conversely, all `8/8` adversarial/poisoned query groups are accurately identified as elevated risk and tightened automatically without false weakening.

---

## 3. Focused & Regression Verification

- **Focused tests:** `PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest tests/unit/test_phase_05_step03_thresholding.py -W error -v` -> **`3 passed` in `0.82s`** (determinism, static fallback, immunity to adversarial document instructions, strict bounding & risk tightening).
- **Full regression:** `PYTHONPATH=src /home/aditya/rags/.venv/bin/pytest -W error -q` -> **`318 passed, 2 deselected` in `7.73s`**, exit `0`.
- **Static typing:** `PYTHONPATH=src /home/aditya/rags/.venv/bin/mypy src/trustrag/ --ignore-missing-imports` -> **`Success: no issues found in 78 source files`**, exit `0`.

---

## 4. Step 3 Acceptance Decision

- [x] Threshold decisions deterministic for identical inputs and configuration.
- [x] Bounded thresholds enforced by `ThresholdBounds` and invariant assertions.
- [x] Zero security-policy bypass (adversarial document instructions cannot weaken thresholds).
- [x] Static fallback (`AdaptiveMode.DISABLED`, `None`, empty pool) and removal cap (`floor(K * cap_ratio)` with cap `>= 0.50`) verified.

**Acceptance Verdict:** **PASS** — Proceed to Step 4 (Distribution and Attack Drift Detection).

