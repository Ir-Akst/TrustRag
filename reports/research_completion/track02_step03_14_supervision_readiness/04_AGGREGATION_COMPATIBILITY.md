# TrustRAG — Track 2, Step 3.14: Aggregation and Supervision Compatibility

### 1. Compatibility Matrix

| Aggregation Policy | Training-Time Compatibility | Inference-Time Compatibility | Justification |
| :--- | :--- | :--- | :--- |
| **`CONTRADICTION_PRIORITY`** | Incompatible (Hard Labels) | **HIGHLY COMPATIBLE (Recommended)** | Asymmetric falsification: if any chunk contradicts, claim is false. Matches RAG safety. |
| **`MAX_CONFIDENCE`** | Incompatible | **COMPATIBLE** | Selects most salient chunk; susceptible to outlier confidence. |
| **`AVERAGE_PROBABILITIES`** | Incompatible | **COMPATIBLE (Neutral biased)** | Arithmetic mean dilutes a single contradictory chunk across background chunks. |
| **`MAJORITY_VOTE`** | Incompatible | **POOR COMPATIBILITY** | In a 5-chunk document, 4 background chunks vote NEUTRAL, outvoting 1 CONTRADICTION chunk! |
| **`INSUFFICIENT_EVIDENCE_GUARD`** | Incompatible | **COMPATIBLE** | Safeguards against low-confidence hallucinations. |

---

### 2. Critical Analytical Finding on Majority Voting and Averaging

- **Fatal Flaw of `MAJORITY_VOTE`:** In document verification, contradiction is sparse (1 chunk out of 5). Majority voting guarantees a **false negative rate approaching 100%** on multi-chunk documents because neutral background chunks outnumber the evidence chunk.
- **`CONTRADICTION_PRIORITY` is Architecturally Required:** Only `CONTRADICTION_PRIORITY` correctly captures the logical semantics: a claim is refuted if *at least one* verified contradiction is found anywhere in the source document.
