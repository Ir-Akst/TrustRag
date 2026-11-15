# TrustRAG — Track 2, Step 3.14: Executive Readiness Report
## Multi-Chunk NLI Supervision & Training Readiness Audit

- **Date:** 2026-11-14T14:10:00Z
- **Role:** Independent Senior NLP Dataset Engineer, ML Training Architect & Adversarial Experimental Auditor
- **Repository:** `/home/aditya/rags/TrustRag-phase11` (`phase-11` @ `aba5cc9d8369f3d7a69e6fd7e81bc055173dde61`)
- **Baseline Repository:** `/home/aditya/rags/TrustRag` (`phase-10` @ `e65bcc80aac634900d1f8e343880fddf66cec168`, strictly immutable)
- **Pretrained Base:** `/home/aditya/rags/models/pretrained/deberta-v3-small` (FP32, 141.9M parameters, untouched)
- **Protected Checkpoints:**
  - Binary Pilot: `/home/aditya/rags/models/trained/deberta-v3-small-binary-pilot1000` (byte-for-byte immutable)
  - Failed NLI Pilot: `/home/aditya/rags/models/trained/deberta-v3-small-nli-pilot1000` (byte-for-byte immutable)
- **Final Readiness Verdict:** **`CONDITIONALLY_READY_WITH_LIMITATIONS`**

---

### Executive Readiness Summary

An exhaustive supervisory audit was conducted to determine whether the existing RAGTruth-derived NLI dataset (`data/processed/sft_v2/nli/`) can support multi-chunk training. 

#### Critical Supervisory Finding

In RAGTruth, human annotators marked hallucination and conflict spans exclusively on the **candidate responses (the hypothesis)**. **Zero ground-truth premise document character spans exist.**
- For `CONTRADICTION`, the refuting fact lives in a localized portion of the document premise.
- For `ENTAILMENT`, annotators verified response factuality against the whole document, but never aligned specific sentences.
- For `NEUTRAL` (unmentioned info), by definition, no corresponding evidence exists in the premise.

When a long document premise is partitioned into overlapping chunks $[P_1, P_2, \dots, P_K]$:
1. **Naive Label Copying is Catastrophic:** Copying the example label `CONTRADICTION` to every chunk assigns contradiction to ~4.5 non-contradictory chunks per example, introducing an **~80% label noise rate** in the minority contradiction class.
2. **Naive Entailment Copying is Corrupting:** Copying `ENTAILMENT` to every chunk teaches the cross-encoder that irrelevant background paragraphs entail the claim.
3. **Assuming Unannotated Chunks are NEUTRAL is Fallacious:** Because positive entailment was never annotated at the span level, an unannotated chunk may actually be the sole ground-truth support.

#### Architectural Recommendation

- **Supervised Chunk-Level Training (Hard Labels):** **FROZEN & REJECTED.** Hard-label chunk supervision is scientifically indefensible on RAGTruth without synthetic teacher models.
- **Defensible Pilot Training Architecture:** Bounded 1,000-step training must utilize **Single-Window 384 with hypothesis preservation (Step 3.10 remediation)**, with multi-chunk cross-encoder serialization deployed **strictly at inference / evaluation time via `CONTRADICTION_PRIORITY`**.
- **Alternative Formulation:** Multiple-Instance Learning (MIL) bag-level loss optimization is theoretically compatible, but requires substantial architectural overhaul unsuited for a bounded pilot.

#### Final Readiness Verdict

**`CONDITIONALLY_READY_WITH_LIMITATIONS`**
*(Ready for a bounded 1,000-step pilot ONLY under Single-Window 384 example-level supervision, with multi-chunking restricted to inference aggregation. Strictly requires separate explicit user authorization before execution.)*
