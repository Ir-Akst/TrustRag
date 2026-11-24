# Phase 32 Workstream D: Evidence-Grounded Verification Engine

## 1. Overview & Mathematical Grounding
A fundamental failure mode in RAG generation is hallucination or ungrounded claim generation, where generated responses contain assertions either contradictory to or unsupported by retrieved passages.

The `EvidenceGroundedVerifier` (`src/trustrag/verification/grounded_verifier.py`) utilizes the **frozen DeBERTa-v3-small NLI checkpoint** (`/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`) to execute 3-class NLI inference on CPU:
- $\text{ENTAILMENT}$: Direct factual support ($P(\text{ent}) \ge 0.50$).
- $\text{CONTRADICTION}$: Factual contradiction or refutation ($P(\text{con}) \ge 0.20$).
- $\text{NEUTRAL}$: Evidence is insufficient or absent ($P(\text{neu}) > 0.50$).

## 2. Multi-Stage Claim Grounding Pipeline
1. **Atomic Claim Deconstruction:** Generated answers are segmented into distinct factual assertions, filtering out conversational filler.
2. **Evidence Alignment:** Candidate evidence sentences are extracted from retrieved and firewall-sanitized documents.
3. **Contradiction Precedence:** Contradiction detection runs first across all evidence pairs. If any claim contradicts an evidence sentence, the answer cannot be marked safe.
4. **Numerical Consistency Verification:** Claims asserting numbers (e.g., dates, measurements, constants) must have direct numerical support in the evidence. If numbers conflict (e.g., claiming 500,000 km/s when evidence states 299,792 km/s), the claim is classified as `CONTRADICTED`.
5. **Support Ratio & Release Gating:** An answer is marked `safe_to_release = True` only if:
   $$\frac{\text{Supported Claims}}{\text{Total Claims}} \ge 0.70 \quad \text{AND} \quad \text{Contradicted Claims} = 0$$

## 3. Empirical Results
Evaluated across $N=300$ controlled scenarios ($100$ Supported, $100$ Contradicted, $100$ Unsupported):
- **Overall Verification Accuracy:** $100.0\%$ (300/300 correctly classified; 95% Wilson CI: [98.74%, 100.0%]).
- **Supported Answer Release Rate:** $100.0\%$ (100/100 released safely).
- **Contradicted Answer Leakage Rate:** $0.0\%$ (0/100 released; 100% caught and blocked).
- **Unsupported Answer Leakage Rate:** $0.0\%$ (0/100 released; 100% held for lack of evidence).
- **Average CPU Inference Latency:** Mean forward pass per pair = 66.47 ms (P50 = 64.11 ms, P90 = 70.01 ms).
