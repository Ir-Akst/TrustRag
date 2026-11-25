# G3 Evidence Verifier Reliability Audit

## Quantitative Results (N=100)
- Overall Gate Accuracy: 49.00% (49/100, 95% CI: [39.42%, 58.65%])
- Supported Claim Acceptance Rate: 40.00% (10/25, 95% CI: [23.40%, 59.26%])
- False Abstention Rate: 60.00% (15/25)
- Contradiction Detection Recall: 40.00% (10/25, 95% CI: [23.40%, 59.26%])
- Unsupported Hallucination Leakage: 32.00% (8/25, 95% CI: [17.21%, 51.59%])
- Partially Supported Leakage: 52.00% (13/25)

## Critical Safety Finding: Lexical Overlap Shortcut
Phase 36 lowered the entailment acceptance threshold to $P(\text{ent}) \ge 0.26$ when lexical overlap $\ge 0.20$.
Under this rule, ungrounded claims containing high lexical overlap with retrieved documents bypass the verifier and are released to users as verified facts.
