# Dataset Integrity, Provenance & Split Audit

## 1. Independence Verification
All Phase 37 holdout datasets were independently generated and sealed prior to testing:
- `reports/phase37/datasets/g1_independent_holdout.jsonl` (N=260: 160 attacks, 100 controls)
- `reports/phase37/datasets/firewall_generator_holdout.jsonl` (N=140: 90 attacks, 50 controls)
- `reports/phase37/datasets/multilingual_holdout.jsonl` (N=270: 9 languages * 30 samples)
- `reports/phase37/datasets/evidence_verification_holdout.jsonl` (N=100: 25 sup, 25 con, 25 unsup, 25 part)

## 2. Cross-Phase Contamination Audit
- Zero overlap with Phase 35 or Phase 36 evaluation datasets.
- Test examples feature completely novel semantic constructions, formal diction, and adversarial framing.
