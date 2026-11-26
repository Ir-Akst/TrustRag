# Data Provenance, Split Hygiene & Anti-Contamination Audit

## Dataset Provenance
All Phase 36 evaluation datasets were independently generated using strictly decoupled test generation scripts:
- `reports/phase36/datasets/g1_semantic_holdout.jsonl` (N=240, SHA256 sealed)
- `reports/phase36/datasets/firewall_generator_holdout.jsonl` (N=120, SHA256 sealed)
- `reports/phase36/datasets/multilingual_holdout.jsonl` (N=270, SHA256 sealed)
- `reports/phase36/datasets/evidence_verification_holdout.jsonl` (N=80, SHA256 sealed)

## Contamination Verification
- Hash comparison confirmed zero overlap with Phase 33, Phase 34, or Phase 35 datasets.
- Semantic prompt injection tests evaluated newly constructed phrasing not present in any previous training sets or earlier benchmark evaluations.
