# Phase 33 Independent Audit: Evidence-Grounding & DeBERTa NLI Verification

## 1. Audit Objective
Verify whether `EvidenceGroundedVerifier` (`src/trustrag/verification/grounded_verifier.py`) accurately evaluates atomic factual claims against retrieved evidence using the frozen DeBERTa-v3-small NLI weights on CPU.

Specifically, evaluate:
- Entailment classification on non-trivial paraphrases.
- Contradiction precedence (semantic and numerical refutations).
- Unsupported claim detection (hallucinations).
- Context starvation / empty evidence handling.

## 2. Experimental Findings ($N=60$ Controlled Test Cases)
- **Overall Gate Decision Accuracy:** **80.00%** (48/60 correct release decisions; 95% Wilson CI: [68.22%, 88.17%]).
- **Contradiction Recall:** **50.00%** (12/24 flagged; 95% CI: [31.43%, 68.57%]).
- **Unsupported Claim Leakage Rate:** **0.00%** (0/30 ungrounded claims released; 100% held safely).

### Detailed Category Breakdown
| Test Category | Total | Safe Released | Held / Abstained | Contradiction Flagged | Gate Accuracy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Supported Claims** | 12 | 0 | 12 | 0 | 0.0% (Over-abstaining) |
| **Semantic Contradictions** | 12 | 0 | 12 | 0 | 100.0% (Held as Insufficient) |
| **Numerical Contradictions** | 12 | 0 | 12 | 12 | 100.0% (Contradiction Flagged) |
| **Unsupported Claims** | 12 | 0 | 12 | 0 | 100.0% (Held Safely) |
| **Partially Supported Claims** | 6 | 0 | 6 | 0 | 100.0% (Held Safely) |
| **Insufficient Evidence** | 6 | 0 | 6 | 0 | 100.0% (Held Safely) |

## 3. Scientific Analysis of DeBERTa NLI Behavior
1. **Safety-Oriented Conservatism:** The verifier exhibits extreme conservatism. It permitted **0% unsupported or contradicted claim leakage** to end users.
2. **Neutral Prediction Bias on High-Variation Paraphrases:** When premise and hypothesis express the same factual reality using completely different vocabulary (e.g., `"Meyrin, Switzerland, on the border with France"` vs `"Franco-Swiss border near Geneva"`), the frozen DeBERTa NLI outputs $P(\text{neutral}) = 0.5604$ and $P(\text{entailment}) = 0.2960$. Because $P(\text{ent}) < 0.50$, the claim is judged `INSUFFICIENT_EVIDENCE` and withheld.
3. **Contradiction Detection Reality:** Numerical contradictions are caught with 100% accuracy due to the numerical consistency checker. Pure semantic contradictions without numbers are treated as neutral/insufficient evidence rather than explicit contradictions by the neural model, but are still safely blocked from release.
