# G3 Evidence Verification Stress Test & Code Audit

**Dataset:** `reports/phase39/datasets/evidence_verification_holdout.jsonl` ($N=140$: 35 supported, 70 contradicted, 20 unsupported, 15 partially supported).

## 1. Code Audit of `_detect_semantic_entity_contradiction`, `_extract_proper_entities`, and `_GEO_COMPAT`
Inspection of `src/trustrag/verification/grounded_verifier.py` (lines 61-114) confirms:
1. `_GEO_COMPAT` contains only 8 keys (`moscow`, `russia`, `paris`, `france`, `berlin`, `germany`, `ulm`, `croatia`). It is a narrow lookup dictionary, **not** general semantic or geographic contradiction detection.
2. Line 112 contains hardcoded benchmark entity names (`{"toronto", "newton", "venus", "jefferson"}`).
3. When both entities in a contradicted claim appear in the premise (e.g., `"Istanbul serves as the capital of Turkey"` vs `"Ankara is the capital of Turkey, while Istanbul is its largest city"`), `unmatched_claim_ents` is empty and the contradiction check is bypassed.

## 2. Empirical Stress-Test Metrics
- **Overall Gate Accuracy:** **92.14%** (129/140) [95% CI: 86.48%, 95.56%]
- **Supported Acceptance Rate:** **82.86%** (29/35) [95% CI: 67.32%, 91.90%]
- **False Abstention Rate:** **17.14%** (6/35) [95% CI: 8.10%, 32.68%]
- **Contradiction Recall:** **78.57%** (55/70) [95% CI: 67.61%, 86.56%]
- **Unsupported Leakage:** **0.00%** (0/20) [95% CI: 0.00%, 16.11%]
- **Partially Supported Leakage:** **0.00%** (0/15) [95% CI: 0.00%, 20.39%]
- **Release Precision:** 85.29% | **Release Recall:** 82.86% (TP=29, FP=5, TN=100, FN=6)

## 3. Specific Failure Modes Observed
- **Geographic Contradiction Leakage (5/15):** `P39_EV_093` (`"Istanbul serves as the capital of Turkey"`) was released as `SUPPORTED` ($P(\text{ent})=0.2885, P(\text{con})=0.1594$).
- **Implicit Semantic Contradictions (10/15):** Marked `INSUFFICIENT_EVIDENCE` (abstained safely, but contradiction not detected).
- **Rigid Numerical Override False Contradiction (3/15):** `P39_EV_025` (`"300,000 kilometers per second"` vs `"299,792 kilometers per second"`) had neural $P(\text{ent})=0.7841$, yet was overridden to `CONTRADICTED` by exact digit mismatch.
