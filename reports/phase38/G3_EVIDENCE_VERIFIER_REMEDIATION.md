# Workstream D — Evidence Verifier Recovery & Shortcut Removal

## 1. Problem Diagnosis
Phase 37 found that G3 had a 49% overall gate accuracy, leaking 32% of unsupported claims and failing to detect 60% of semantic contradictions. The verifier was relying on high lexical token overlap to accept claims even when the neural model classified them as neutral.

## 2. Engineering Changes
- Removed the unsafe lexical overlap shortcut in . Claims now require genuine neural entailment dominance ((	ext{ent}) \ge 0.45$, or (	ext{ent}) \ge 0.18$ with zero contradictions).
- Implemented  using  and geographic compatibility relations (). Entity substitutions (e.g. Toronto instead of Ottawa) are strictly flagged as .

## 3. Empirical Results
- Evaluated =100$ (5$ supported, 5$ contradicted, 5$ unsupported, 5$ partially supported).
- Overall Accuracy: **82.00%** (2/100$) [95% CI: 73.33%, 88.30%].
- Contradiction Recall: **100.00%** (5/25$) [95% CI: 86.68%, 100.0%].
- Unsupported Hallucination Leakage: **0.00%** (bash/25$) [95% CI: 0.00%, 13.32%].
- Supported Acceptance Rate: **80.00%** (0/25$) [95% CI: 60.87%, 91.14%].
- False Abstention Rate: **20.00%** (/25$).
