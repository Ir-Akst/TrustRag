# TrustRAG Phase 12 — Step 02: Neural NLI Integration into G3 Output Evidence Verifier

**Role:** Principal ML Systems Engineer & Security Research Engineer  
**Date:** November 18, 2026  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-12` | **HEAD:** `aba5cc9d`  
**Frozen Model Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`  
**Target Code:** `src/trustrag/config/engine_config.py`, `src/trustrag/verification/output_verifier.py`

---

## 1. Architectural Design & Integration Strategy

In Phase 11.2, an independent architectural audit revealed that `OutputEvidenceVerifier` in `src/trustrag/verification/output_verifier.py` relied exclusively on heuristic lexical and regex rules, while the fine-tuned DeBERTa-v3-small NLI checkpoint existed only as an offline artifact.

Step 02 resolves this architectural gap by integrating the frozen DeBERTa-v3-small checkpoint directly into the `OutputEvidenceVerifier` pipeline while preserving 100% backward compatibility with existing heuristic baselines.

```
                  G3 OUTPUT EVIDENCE VERIFIER ARCHITECTURE
                  
                      Generated Answer + Retrieved Evidence
                                       |
                                       v
                             extract_claims()
                                       |
                                       v
                        [nli_backend Configuration]
                                       |
         +-----------------------------+-----------------------------+
         |                             |                             |
         v                             v                             v
  "heuristic" (Default)       "neural_nli"                  "hybrid" (Recommended)
  - TF-IDF Lexical Spans      - Frozen DeBERTa-v3-small     - Neural NLI semantic score
  - Polarity Antonym Match    - 3-Class Softmax Probabilities - Strict Numeric RegEx Guard
  - Strict Numeric RegEx      - Configurable Contradiction  - Polarity Conflict Override
  - Zero Neural Overhead        Threshold (theta = 0.20)    - Heuristic Fallback on Error
         |                             |                             |
         +-----------------------------+-----------------------------+
                                       |
                                       v
                  Atomic Claim Verdict & Traceable Evidence
                  (SUPPORTED, CONTRADICTED, INSUFFICIENT, UNCERTAIN)
```

---

## 2. Technical Specification & Implementation Details

### 2.1 Configuration Extensions (`VerificationConfig`)
The Pydantic v2 `VerificationConfig` model was extended with strictly typed, validated fields:
- `nli_backend: str = "heuristic"`: Supported backends: `"heuristic"`, `"neural_nli"`, `"hybrid"`.
- `nli_model_path: Optional[str] = "/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch"`: Path to the staged offline checkpoint.
- `nli_contradiction_threshold: float = 0.20`: Contradiction probability threshold $\theta_{\text{con}}$ for classifying a claim as `CONTRADICTED`.
- `nli_entailment_threshold: float = 0.50`: Entailment probability threshold $\theta_{\text{ent}}$ for classifying a claim as `SUPPORTED`.
- `nli_neutral_policy: str = "insufficient"`: Determines handling of neutral predictions (`"insufficient"` $\to$ `INSUFFICIENT`, `"uncertain"` $\to$ `UNCERTAIN`).
- `nli_device: str = "cpu"`: Execution device (`"cpu"`).

### 2.2 Neural Inference Engine (`OutputEvidenceVerifier`)
- **Lazy Loading & Weight Immutability:** The DeBERTa-v3-small model is loaded on-demand in evaluation mode (`model.eval()`). All parameters have `requires_grad = False` to guarantee weights are never modified.
- **Deterministic Inference:** Inferences run inside `torch.no_grad()`.
- **Diagnostic Logging & Traceability:** Raw 3-class logits and softmax probabilities are preserved and attached directly to each `EvidenceReference.alignment_note` and `ClaimVerificationItem.explanation`.
- **Fail-Closed Security Boundary:** If the model checkpoint is missing, corrupted, or an out-of-memory/forward-pass error occurs:
  - In `"neural_nli"` mode: The claim is **never marked as SUPPORTED**. The verifier fails closed with `G3ClaimVerdict.UNCERTAIN`, `EvidenceOutcome.UNCERTAIN`, and `unsupported_flag = True`.
  - In `"hybrid"` mode: The verifier logs a warning and falls back to heuristic verification, clearly annotating `[Hybrid Fallback]` in the explanation.

### 2.3 The Hybrid Verification Engine (Neural + Heuristic)
Live testing revealed that pure neural NLI embeddings can suffer from numeric blindness (e.g., predicting Entailment when temperature or dosage numbers differ because surrounding context tokens match). The `"hybrid"` backend combines the semantic power of neural NLI with strict regex numeric guards:
1. Runs neural NLI on candidate passages.
2. If $p_{\text{con}} \ge \theta_{\text{con}}$, classifies immediately as `CONTRADICTED`.
3. If $p_{\text{ent}} \ge \theta_{\text{ent}}$, runs secondary heuristic numeric and polarity conflict validation. If a numeric conflict is detected (e.g., 300°C vs 100°C), the neural entailment is overridden to `CONTRADICTED`.

---

## 3. Empirical Test Results & Verification

### 3.1 Unit Test Suite (`tests/unit/test_phase12_step02_neural_g3.py`)
10 dedicated unit tests covering all required edge cases executed with 100% success:

| Test Case | Scenario / Condition Tested | Expected Verdict | Actual Result | Status |
| :--- | :--- | :---: | :---: | :---: |
| `test_entailing_claim_supported` | High entailment probability ($p_{\text{ent}} = 0.932$) | `SUPPORTED` | `SUPPORTED` | **PASS** |
| `test_contradictory_claim_at_0_20` | Contradiction exceeding threshold ($p_{\text{con}} = 0.28 \ge 0.20$) | `CONTRADICTED` | `CONTRADICTED` | **PASS** |
| `test_contradiction_threshold_config` | Contradiction below threshold ($p_{\text{con}} = 0.28 < 0.35$) | `INSUFFICIENT` | `INSUFFICIENT` | **PASS** |
| `test_neutral_evidence_insufficient` | Dominant neutral prediction ($p_{\text{neu}} = 0.910$) | `INSUFFICIENT` | `INSUFFICIENT` | **PASS** |
| `test_neutral_evidence_uncertain` | Dominant neutral under `"uncertain"` policy | `UNCERTAIN` | `UNCERTAIN` | **PASS** |
| `test_missing_evidence_yields_insuf` | Empty evidence document list | `INSUFFICIENT` | `INSUFFICIENT` | **PASS** |
| `test_multi_passage_contradiction` | Doc 1 entails, Doc 2 contradicts | `CONTRADICTED` | `CONTRADICTED` | **PASS** |
| `test_model_loading_failure` | Nonexistent checkpoint path | `UNCERTAIN` (Fail-Closed) | `UNCERTAIN` | **PASS** |
| `test_malformed_input_crash` | Forward pass runtime exception | `UNCERTAIN` (Fail-Closed) | `UNCERTAIN` | **PASS** |
| `test_hybrid_numeric_conflict` | Neural entailment overridden by numeric conflict | `CONTRADICTED` | `CONTRADICTED` | **PASS** |

### 3.2 Regression Safety
Running the full pre-existing verification test suite (`tests/unit/test_phase_03_g3_verification.py`) confirmed:
- **146 of 146 pre-existing tests PASSED (0 regressions).**
- Heuristic verification remains default when `nli_backend="heuristic"`.

### 3.3 Live DeBERTa-v3-small Checkpoint Verification
Executing live inference with the frozen checkpoint produced:
- **Entailment:** `"Water boils at 100 degrees Celsius at sea level"` $\to$ `SUPPORTED` ($p_{\text{ent}} = 0.9273$, logits: `[1.979, -1.319, -1.204]`).
- **Hybrid Numeric Override:** `"Water boils at 300 degrees Celsius"` $\to$ `CONTRADICTED` (Heuristic guard caught temperature conflict `300°C` vs `100°C`).
- **Neutral / Insufficient:** `"Water molecules contain oxygen and hydrogen"` against boiling passage $\to$ `INSUFFICIENT` ($p_{\text{neu}} = 0.5544$).

---

## 4. Deliverable Summary

The neural NLI verifier is fully implemented, verified, and ready for benchmark evaluation and pipeline integration.

