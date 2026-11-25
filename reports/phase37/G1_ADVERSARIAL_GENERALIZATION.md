# G1 Independent Semantic Generalization Audit

## Quantitative Results (N=260)
- Attack Detection Rate (ADR): 71.25% (114/160, 95% CI: [63.80%, 77.70%])
- Attack Success Rate (ASR): 28.75% (46/160)
- False Positive Rate (FPR): 0.00% (0/100, 95% CI: [0.00%, 3.70%])
- Precision: 100.0% (114/114)
- Recall: 71.25% (114/160)
- F1 Score: 83.21%

## Breakdown by Archetype
- `unseen_imperative_verbs`: 10/40 blocked (25.0% ADR) — FAILED
- `indirect_narrative_framing`: 24/40 blocked (60.0% ADR) — VULNERABLE
- `obfuscated_fragmented`: 40/40 blocked (100.0% ADR) — PASS
- `adaptive_benign_prefaced`: 40/40 blocked (100.0% ADR) — PASS
- `benign_cybersecurity_education`: 0/50 blocked (0.0% FPR) — PASS
- `benign_imperative_general`: 0/50 blocked (0.0% FPR) — PASS
