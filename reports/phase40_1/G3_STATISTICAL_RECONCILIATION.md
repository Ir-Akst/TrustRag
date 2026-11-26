# G3 Statistical Reconciliation & Fresh Validation

## 1. Reconciliation of Phase 40's 120-Example Accounting
Inspection of `reports/phase40/g3/predictions.jsonl` ($N=120$) confirms:
- `supported` (30): 30/30 `SUPPORTED` (`safe_to_release=True`).
- `partially_supported` (15): 15/15 `PARTIALLY_SUPPORTED` (`safe_to_release=False`).
- `entity_contradiction` (9), `geo_contradiction` (19), `implicit_contradiction` (18), `numerical_contradiction` (9): 55/55 `CONTRADICTED` (`safe_to_release=False`).
- `unsupported` (20, expected `INSUFFICIENT_EVIDENCE`, `safe_to_release=False`): **20/20 were labeled `CONTRADICTED`** instead of `INSUFFICIENT_EVIDENCE` because claims contained numbers absent from number-free premises. Thus, binary release-gate accuracy was **120/120 (100%)**, while exact 4-class status accuracy was **100/120 (83.33%)**.

## 2. Phase 40.1 Fresh Evaluation ($N=140$)
In Phase 40.1, `grounded_verifier.py` was updated so number-free premises return `has_num_match=False, num_conflict=False`:
- **Release-Gate Accuracy:** **100.00%** (140/140) [95% CI: 97.33%, 100.00%]
- **Exact 4-Class Status Accuracy:** **91.43%** (128/140) [95% CI: 85.62%, 95.03%] (13/25 `unsupported` labeled `INSUFFICIENT_EVIDENCE`, 12/25 labeled `CONTRADICTED` via NLI/slot checks)
- **Supported Acceptance:** **100.00%** (30/30) | **False Abstention:** **0.00%** (0/30)
- **Contradiction Recall:** **100.00%** (65/65) | **Unsupported Leakage:** **0.00%** (0/25)
