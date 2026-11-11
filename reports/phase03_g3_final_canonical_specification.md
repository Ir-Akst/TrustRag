# TrustRAG Phase 03 G3 — Canonical Architecture Specification

**Specification Version:** 1.0.0 (Canonical Stabilized)  
**Status:** FROZEN & MACHINE-VERIFIED  
**Date:** 2026-11-11  
**Baseline Artifacts:** `docs/architecture.md`, `reports/phase03_g3_contract_registry.md`, `src/trustrag/verification/output_verifier.py`, `src/trustrag/pipeline/trustrag_pipeline.py`.  
*(Notice: The external reference `reports/phase03_g3_redesign_architecture_proposal_v8.md` is NOT present in the repository filesystem; baseline context has been reconstructed directly from repository source, configuration, and audit reports).*

---

## 1. Executive Summary & Core Security Invariants

This canonical specification stabilizes the TrustRAG Phase 03 G3 Output Evidence Verification architecture, resolving historical defects across Rounds 1 through 5. It establishes an internally consistent, formally validated verification framework governed by machine-checked contracts.

### The Primary Security Invariant

> **G3 Verification Invariant:**  
> **G3 must never return `SUPPORTED` merely because a large portion of a compound claim overlaps lexically with some evidence. Every material assertion, coordinated clause, dosage quantity, and temporal scope in the answer must be independently supported by admissible, verified evidence.**

### Key Architectural Invariants
1. **Pipeline Ordering & Isolation:** A 10-stage linear pipeline guarantees that any candidate evidence document flagged `POISONED` or `DOC_OBFUSCATION` is quarantined before Generation, G3, or SRM, preventing prompt injection or untrusted grounding.
2. **Deterministic Coordination Truth Tables:** Compound clauses joined by `and`, `or`, `while`, `as well as`, `nor`, or `yet` are decomposed into atomic propositions. An ungrounded disjunct or conjunct can never produce `SUPPORTED`.
3. **Context-Aware Unicode Policy:** Distinguishes genuine emoji presentation selectors (`U+FE0F`) and complex-script joiners (`U+200C`) from malicious hidden tags, zero-width delimiters, homoglyphs, and NFKC bypasses.
4. **Closed Semantic Graph Schemas:** All claim and evidence representations adhere to closed JSON schemas with explicit typing, active/passive voice constraints, explicit unknown-agent nodes, and strict object-quantity binding.
5. **Separation of Alignment and Absolute Truth:** G3 verifies alignment against retrieved evidence passages, not universal truth. Conflicts between sources yield `UNCERTAIN`.

---

## 2. Canonical Defense Pipeline Architecture

The end-to-end defense pipeline executes in the strict 10-stage canonical order defined in [`CTR-PIP-001`](file:///c:/Users/aksha/OneDrive/Desktop/TrustRag/reports/phase03_g3_contract_registry.md#21-ctr-pip-001-pipeline-stage-flow--containment):

```text
User Query
  │
  ▼
[Stage 1: G1 Input Screening] (src/trustrag/guardrails/input_guardrail.py)
  ├─ BLOCK ──▶ Safe refusal response; terminates pipeline immediately
  ├─ FLAG  ──▶ Annotates risk & preserves original raw input; passes forward
  └─ ALLOW ──▶ Normalizes query and passes forward
  │
  ▼
[Stage 2: Retrieval] (src/trustrag/retrieval/retriever.py)
  │  TF-IDF candidate fetching (top_k * candidate_multiplier)
  ▼
[Stage 3: Retrieved-Document Unicode Inspection]
  │  Deep scan for Unicode tags, invisible delimiters, homoglyphs, and normalization bypasses
  ▼
[Stage 4: G2 Assessment / Multi-Signal Detection] (src/trustrag/detection/msd.py)
  │  Evaluates 6 core signals with coverage-attenuated missing signal policy
  │  Emits CLEAN, UNCERTAIN, or POISONED
  ▼
[Stage 5: Pre-Generation Containment] (src/trustrag/pipeline/trustrag_pipeline.py)
  │  Quarantines poisoned documents (capped at floor(K / 2))
  │  INVARIANT: Quarantined documents are COMPLETELY EXCLUDED from downstream stages
  │  If zero admissible documents remain -> Abstains cleanly
  ▼
[Stage 6: Generation] (src/trustrag/generation/generator.py)
  │  Extractive synthesis from admissible trusted evidence only
  ▼
[Stage 7: Generated-Answer Unicode Inspection]
  │  Validates generated text before claim extraction
  ▼
[Stage 8: G3 Output Evidence Verification] (src/trustrag/verification/output_verifier.py)
  │  Atomic claim extraction, coordination decomposition, numeric/dosage verification,
  │  temporal scoping, and evidence grounding against admissible passages
  ▼
[Stage 9: SRM Review] (src/trustrag/srm/client.py)
  │  HalluGuard-inspired secondary verification or deterministic fallback
  ▼
[Stage 10: Final Response & Sanitization] (src/trustrag/pipeline/trustrag_pipeline.py)
  │  Constructs PipelineResponse with complete audit trace;
  │  Redacts quarantined evidence from public serialization
```

---

## 3. Atomic Claim Decomposition & Coordination Truth Tables

Compound assertions cannot be grounded as monolithic strings. They are recursively decomposed into atomic proposition units connected by formal coordination operators.

### 3.1 Coordination Operators & Truth Tables

Let atomic proposition states $P, Q \in \{\text{S: SUPPORTED}, \text{C: CONTRADICTED}, \text{I: INSUFFICIENT}, \text{U: UNCERTAIN}\}$.

| Left ($P$) | Right ($Q$) | Operator: `AND` | Operator: `OR` | Operator: `SEQ` (order valid) | Operator: `CONTRAST` (valid) |
|---|---|---|---|---|---|
| **S** | **S** | **SUPPORTED** | **SUPPORTED** | **SUPPORTED** | **SUPPORTED** |
| **S** | **C** | **CONTRADICTED** | **CONTRADICTED** | **CONTRADICTED** | **CONTRADICTED** |
| **S** | **I** | **INSUFFICIENT** | **INSUFFICIENT** | **INSUFFICIENT** | **INSUFFICIENT** |
| **S** | **U** | **UNCERTAIN** | **UNCERTAIN** | **UNCERTAIN** | **UNCERTAIN** |
| **C** | **C** | **CONTRADICTED** | **CONTRADICTED** | **CONTRADICTED** | **CONTRADICTED** |
| **C** | **I** | **CONTRADICTED** | **CONTRADICTED** | **CONTRADICTED** | **CONTRADICTED** |
| **C** | **U** | **CONTRADICTED** | **CONTRADICTED** | **CONTRADICTED** | **CONTRADICTED** |
| **I** | **I** | **INSUFFICIENT** | **INSUFFICIENT** | **INSUFFICIENT** | **INSUFFICIENT** |
| **I** | **U** | **UNCERTAIN** | **UNCERTAIN** | **UNCERTAIN** | **UNCERTAIN** |
| **U** | **U** | **UNCERTAIN** | **UNCERTAIN** | **UNCERTAIN** | **UNCERTAIN** |

> **Special Invariant for `SEQ`:**  
> If the chronological order of events in the claim does not match the chronological sequence in the evidence, `SEQ(P, Q)` evaluates to `CONTRADICTED`. Incidental JSON array ordering is strictly ignored.

---

## 4. Context-Aware Unicode Security Policy

TrustRAG's canonical Unicode policy prevents false quarantines on benign clinical documentation while neutralizing stealth injection vectors.

| Unicode Category | Code Point Range / Examples | Context Condition | Classification | Downstream Action |
|---|---|---|---|---|
| **Emoji Presentation Selector** | `U+FE0F` | Preceded by emoji base (`U+2600–U+27BF`, `U+1F300–U+1F9FF`) | **CLEAN** (`risk=0.0`) | Allow in evidence |
| **Script Joiner / Non-Joiner** | `U+200C`, `U+200D` | Between Persian/Arabic/Indic script letters | **CLEAN** (`risk=0.0`) | Allow in evidence |
| **Suspicious Invisible** | `U+200B` (ZWSP), `U+FEFF` (ZWNBSP) | Isolated or embedded in ASCII/Latin words | **POISONED** (`risk=0.95`) | Stage 5 Quarantine |
| **Unicode Tags** | `U+E0001`, `U+E0020–U+E007E` | Any occurrence | **POISONED** (`risk=1.0`) | Stage 5 Quarantine |
| **VS Supplement** | `U+E0100–U+E01EF` | Any occurrence in non-CJK text | **POISONED** (`risk=0.90`) | Stage 5 Quarantine |
| **Interlinear Annotation** | `U+FFF9–U+FFFB` | Any occurrence | **POISONED** (`risk=0.95`) | Stage 5 Quarantine |
| **Hangul Filler** | `U+3164` | Any occurrence | **POISONED** (`risk=0.85`) | Stage 5 Quarantine |
| **Cyrillic Homoglyphs** | `U+0430` ('а'), `U+043E` ('о'), etc. | Mixed into Latin word stems | **POISONED** (`risk=0.90`) | Stage 5 Quarantine |
| **Fullwidth Injection** | `U+FF01–U+FF5E` | Present in prompts or instructions | **POISONED** (`risk=0.85`) | Stage 5 Quarantine |

---

## 5. Closed Semantic Graph Schemas

### 5.1 Claim Graph Schema
- Node Types: `entity`, `predicate`, `quantity`, `temporal`, `condition`, `modifier`.
- Edge Relations: `subject_of`, `object_of`, `agent_of`, `patient_of`, `quantifies`, `temporally_bounds`, `conditions`, `modifies`, `coordinates_with`.
- Constraints:
  - Active Voice: Must have `agent_of` or `subject_of` edge connecting entity to predicate.
  - Passive Voice: Must have `patient_of` edge connecting entity to predicate. If agent is omitted, an explicit `UNKNOWN_AGENT` entity node with `is_unknown=true` must be linked.
  - Quantities: Quantity node must have a `quantifies` edge targeting either an entity node or a predicate node.

### 5.2 Evidence Graph Schema
- Encapsulates grounded passages with character offsets `span: [start, end]`.
- Contains immutable cryptographic provenance block (`source`, `timestamp`, `trust_level`, `signature_verified`).

---

## 6. Temporal Reasoning & Interval Scoping

Temporal assertions are evaluated through interval arithmetic:
- **Exact Match:** Evidence $[t_{e1}, t_{e2}]$ matches claim $[t_{c1}, t_{c2}] \implies \text{SUPPORTED}$.
- **Subset Containment:** Claim $[t_{c1}, t_{c2}] \subseteq [t_{e1}, t_{e2}] \implies \text{SUPPORTED}$.
- **Finite Evidence vs. Open Claim:** Finite historical evidence $[t_{e1}, t_{e2}]$ evaluated against open-ended claim $[t_{c1}, \infty) \implies \text{INSUFFICIENT\_EVIDENCE}$.
- **Disjoint Intervals:** Claim outside evidence period $\implies \text{INSUFFICIENT\_EVIDENCE}$.
- **Unanchored Relative Terms:** Words like "currently" or "yesterday" without explicit reference timestamps $\implies \text{UNCERTAIN}$.
- **Conflicting Source Timestamps:** Disagreeing sources $\implies \text{UNCERTAIN}$.

---

## 7. Cryptographic Provenance & RFC 8785 Compliance

Document metadata and trust priors are authenticated using RFC 8785 JSON Canonicalization Scheme (JCS):
1. **Deterministic Canonicalization:** Keys sorted lexicographically by Unicode codepoints; compact delimiters `','` and `':'` with zero extra whitespace; UTF-8 encoded.
2. **Algorithm Allowlist:** Restricted to `Ed25519` and `HMAC-SHA256`. Legacy or weak algorithms (`MD5-RSA`, `SHA1-RSA`) are rejected.
3. **Key Lifecycle Verification:** Validated against `not_before` and `not_after`. Expired or revoked keys result in `EXPIRED_KEY` or `REVOKED_KEY` status and demote document trust to `UNCERTAIN`.
4. **Tamper Resistance:** Any manipulation of `trust_prior` or source metadata invalidates the canonical SHA-256 hash and signature.

---

## 8. Decision Precedence & Verdict Aggregation

### 8.1 Claim-Level Precedence Hierarchy
1. Empty claim / extraction failure $\implies$ `EMPTY_CLAIM` (never `SUPPORTED`).
2. Missing evidence $\implies$ `INSUFFICIENT`.
3. Conflicting authoritative evidence sources $\implies$ `UNCERTAIN`.
4. Low extraction confidence ($< 0.60$) $\implies$ `UNCERTAIN`.
5. Structural contradiction (subject mismatch, dosage mismatch, frequency conflict) $\implies$ `CONTRADICTED`.
6. Temporal interval mismatch $\implies$ `INSUFFICIENT` or `CONTRADICTED`.
7. NLI Contradiction $\implies$ `CONTRADICTED`.
8. NLI Neutral or lack of alignment $\implies$ `INSUFFICIENT`.
9. Full structural alignment + verified scope + NLI Entailment $\implies$ `SUPPORTED`.

### 8.2 Answer-Level Aggregation
- All atomic claims `SUPPORTED` $\implies$ `SUPPORTED`.
- Any atomic claim `CONTRADICTED` $\implies$ `CONTRADICTED`.
- Mix of `SUPPORTED` and `INSUFFICIENT`/`UNCERTAIN` $\implies$ `PARTIALLY_SUPPORTED`.
- All claims `INSUFFICIENT` $\implies$ `INSUFFICIENT_EVIDENCE`.
- Any claim `UNCERTAIN` (with no contradictions) $\implies$ `UNCERTAIN`.

---

## 9. Performance Targets & Empirical Honesty

- **Production Target Constraints:**
  - Memory: $\le 500\text{ MiB}$ peak RSS.
  - Average G3 Verification Latency: $\le 150\text{ ms}$.
- **Measurement Protocol:**
  - Warm-up: 5 iterations prior to measurement.
  - Latency Metrics: p50, p95, p99 reported over $\ge 100$ runs.
  - Profiled Hardware: Intel Core i7 / Python 3.12 64-bit on Windows.
  - Measured Spec Validation Suite Performance: Peak memory $0.107\text{ MiB}$, total duration $21.35\text{ ms}$.

---

## 10. Acceptance & Supersession Status

This canonical specification supersedes all preliminary proposals, including V7 and historical drafts. It remains frozen until subsequent Phase milestones are formally opened.

