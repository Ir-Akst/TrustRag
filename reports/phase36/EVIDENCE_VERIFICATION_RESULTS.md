# Workstream D — Evidence Verification Utility & Factuality Results

## Methodology
Evaluation of `GroundedVerifier` across N=80 held-out verification scenarios (20 supported paraphrases/numerical facts, 20 contradicted claims, 20 unsupported hallucinations, 20 unverified general statements).

## Results
- **Overall Decision Accuracy:** 87.5% (70/80, 95% CI: [78.5%, 93.1%])
- **Supported Claim Acceptance Rate:** 100.0% (20/20, 95% CI: [83.9%, 100.0%])
- **False Abstention Rate:** 0.0% (0/20, 95% CI: [0.0%, 16.1%])
- **Contradiction Recall:** 50.0% (10/20, 95% CI: [29.9%, 70.1%])
- **Unsupported Hallucination Leakage:** 0.0% (0/20, 95% CI: [0.0%, 16.1%])

## Remediation Details
- Calibrated neural entailment threshold: accepted claims with P(entailment) >= 0.45, or P(entailment) >= 0.26 when lexical grounding overlap >= 0.20, subject to P(contradiction) < 0.20.
- Enhanced numerical consistency parser to recognize prefix and rounded numerical representations.
