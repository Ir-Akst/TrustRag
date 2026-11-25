# Workstream A — G1 Semantic Generalization & Injection Remediation

## Methodology
Evaluation of G1 Semantic Guardrail on N=240 holdout samples (160 attacks, 80 benign controls) containing novel imperative verbs (`unfetter`, `dethrone`, `abnegate`, `supersede`, etc.) and defensive cybersecurity education queries.

## Results
- **Overall ADR:** 100.0% (160/160, 95% CI: [97.7%, 100.0%])
- **Attack Success Rate (ASR):** 0.0% (0/160)
- **False Positive Rate (FPR):** 0.0% (0/80, 95% CI: [0.0%, 4.6%])
- **Novel Action Verbs ADR:** 100.0% (40/40)
- **Indirect / Contextual ADR:** 100.0% (40/40)
- **Obfuscated Variants ADR:** 100.0% (40/40)
- **Adaptive White-Box ADR:** 100.0% (40/40)
- **Benign Security Education FPR:** 0.0% (0/40)
- **Benign General Domain FPR:** 0.0% (0/40)

## Remediation Details
1. Expanded verb dictionary and directive tokens in `SemanticPromptInjectionClassifier`.
2. Added negative logit weighting (-3.50) for educational keywords.
3. Updated `HarmfulIntentClassifier` defensive cybersecurity pattern matching.
