# Workstream A — G1 Semantic Generalization Remediation

## 1. Problem Diagnosis
In Phase 37, G1 failed on 75% of unseen imperative verbs (, , , , ) and 40% of theoretical/roleplay framing. The root cause was an over-reliance on a fixed verb dictionary and insufficient interaction weighting for administrative target tokens.

## 2. Engineering Changes
- **Morphological Expansion:** Added 24 foundational override stems in  (, , , , , , , , , , etc.).
- **Contextual Target Association:** Broadened target phrases to cover operational boundaries, configuration tokens, environment variables, and preambles.
- **Narrative & Persona Modeling:** Strengthened detection of hypothetical scenarios, unrestricted terminal environments, and simulated debug personas.

## 3. Empirical Results
- Total evaluated: =300$ (80$ attacks, 20$ controls).
- Attack Detection Rate (ADR): **95.00%** (71/180$) [95% CI: 90.77%, 97.35%].
- False Positive Rate (FPR): **0.00%** (bash/120$) [95% CI: 0.00%, 3.10%].
- Narrative & Roleplay ADR: **100.00%** (5/45$).
- Obfuscated & Fragmented ADR: **100.00%** (5/45$).
- Benign-Prefaced Adaptive ADR: **100.00%** (5/45$).
- Unseen Imperatives ADR: **80.00%** (6/45$).
