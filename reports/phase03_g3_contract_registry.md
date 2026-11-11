# TrustRAG Phase 03 G3 — Canonical Contract Registry

**Document Version:** 1.0.0 (Canonical)  
**Status:** FROZEN & VALIDATED  
**Date:** 2026-11-11  
**Scope:** Canonical contracts governing all G3 verification architecture, interfaces, and safety guarantees.

---

## 1. Architectural Contract Registry Overview

This registry establishes the 12 canonical contracts for TrustRAG G3 verification and defense containment. Every contract is uniquely identified, strictly typed, internally consistent, and backed by machine-checkable validation in `tools/spec_validation/`.

| Contract ID | Component | Primary Invariant / Guarantee | Validation Module |
|---|---|---|---|
| `CTR-PIP-001` | Pipeline Stage Flow | Canonical 10-stage execution; quarantined evidence never reaches Gen/G3/SRM | `validate_pipeline.py` |
| `CTR-UNI-001` | Unicode Security | Distinguishes benign emoji/scripts from hidden tags & homoglyphs; 0 false quarantines | `validate_unicode.py` |
| `CTR-CLM-001` | Claim Graph Schema | Closed node/edge schema; active/passive constraints; explicit unknown agents | `validate_schemas.py` |
| `CTR-EVD-001` | Evidence Graph Schema | Closed grounding graph; span offsets; cryptographic provenance linkages | `validate_schemas.py` |
| `CTR-CRD-001` | Coordination Logic | Deterministic truth tables (AND, OR, SEQ, CONTRAST); ungrounded clauses never SUPPORTED | `validate_coordination.py` |
| `CTR-TMP-001` | Temporal Reasoning | Finite evidence never supports open-ended claims; strict interval scoping | `validate_temporal.py` |
| `CTR-QNT-001` | Quantities & Binding | Dosage values, units, frequencies strictly bound to entity/event nodes | `validate_schemas.py` |
| `CTR-PRV-001` | Cryptographic Provenance | RFC 8785 canonicalization; Ed25519/HMAC allowlist; validity & revocation checks | `validate_provenance.py` |
| `CTR-NLI-001` | NLI Calibration | Deterministic decision precedence; NLI cannot override structural contradiction | `validate_verdicts.py` |
| `CTR-VRD-001` | Verdict Aggregation | 5 claim states, 5 answer states; empty/unsupported claims never SUPPORTED | `validate_verdicts.py` |
| `CTR-PRF-001` | Performance Constraints | Peak memory < 500 MiB, G3 latency < 150 ms; honest measurement disclosure | `run_all_validations.py` |
| `CTR-BNK-001` | Benchmark Immutability | Immutable historical regression benchmark; disjoint evaluation partitions | `validate_statistical.py` |

---

## 2. Canonical Contracts Detail

### 2.1 `CTR-PIP-001`: Pipeline Stage Flow & Containment

- **Contract ID:** `CTR-PIP-001`
- **Description:** Enforces deterministic execution of the canonical 10-stage TrustRAG defense pipeline and isolates quarantined data.
- **Stage Ordering:**
  1. `G1_INPUT_SCREENING`: Query threat analysis, prompt injection check, normalization.
  2. `RETRIEVAL`: TF-IDF candidate fetching (`top_k * candidate_multiplier`).
  3. `RETRIEVED_DOC_UNICODE_INSPECTION`: Unicode tag, variation selector, and invisible delimiter scan on retrieved passages.
  4. `G2_ASSESSMENT`: Multi-Signal Detector evaluation (6 core signals + coverage attenuation).
  5. `PRE_GENERATION_CONTAINMENT`: Quarantined document isolation (capped at `floor(K/2)`). Quarantined docs removed from context.
  6. `GENERATION`: Grounded answer synthesis (abstains if admissible context is empty).
  7. `GENERATED_ANSWER_UNICODE_INSPECTION`: Unicode inspection of synthesized answer.
  8. `G3_VERIFICATION`: Atomic claim extraction and strict factual alignment.
  9. `SRM_REVIEW`: Small Reasoning Model secondary verification or deterministic fallback.
  10. `FINAL_RESPONSE`: Response packaging, audit telemetry, public sanitization.
- **Inputs:** `UserQuery(query_text: str)`, `RetrievedDocuments(List[RawDocument])`
- **Outputs:** `PipelineResponse(answer: str, decision: DecisionEnum, public_evidence: List[EvidenceDocument], trace: AuditTrace)`
- **Preconditions:** `query_text` is non-empty; configuration loaded without errors.
- **Postconditions:** Quarantined documents are excluded from `public_evidence`, `gen_context`, `g3_context`, and `srm_context`.
- **Invariants:**
  1. Under no circumstance shall a document flagged `POISONED` or `DOC_OBFUSCATION` be supplied to Generation, G3, or SRM.
  2. Public serialization (`model_dump`, `model_dump_json`, logs, CLI) must redact quarantined passages.
- **Failure Behavior:** If all documents are quarantined or G1 blocks, pipeline returns safe abstention response with `decision="FLAGGED_ABSTAINED"` and `safe_to_display=false`.
- **Machine-Checkable Validation:** `tools/spec_validation/validators/validate_pipeline.py`
- **Linked Tests:** `test_phase_03_defense.py`, `audit_round5_independent_probes.py` (`SEC3C`, `SEC3E`).

---

### 2.2 `CTR-UNI-001`: Unicode Security & Normalization Policy

- **Contract ID:** `CTR-UNI-001`
- **Description:** Canonical Unicode inspection policy distinguishing benign presentation selectors and complex scripts from security attacks.
- **Inputs:** `text: str`
- **Outputs:** `UnicodeSecurityReport(is_suspicious: bool, risk_score: float, threat_categories: List[str], normalized_text: str)`
- **Preconditions:** Input is valid UTF-8 string.
- **Postconditions:** Benign emoji presentation sequences (`U+FE0F`) preceded by pictographs are rated `risk_score=0.0, decision="CLEAN"`. Valid ZWNJ (`U+200C`) in Persian/Arabic/Indic script context is rated `risk_score=0.0, decision="CLEAN"`.
- **Invariants:**
  1. Standalone or ASCII-embedded ZWSP (`U+200B`), ZWNBSP (`U+FEFF`), Unicode Tags (`U+E0001`, `U+E0020-E007E`), Variation Selectors Supplement (`U+E0100-E01EF`), Hangul Filler (`U+3164`), and Interlinear Annotations (`U+FFF9-U+FFFB`) must trigger `is_suspicious=True, decision="POISONED", risk_score >= 0.85`.
  2. Cyrillic homoglyphs mixed into Latin text must trigger `is_suspicious=True, risk_score >= 0.90`.
- **Failure Behavior:** Any document exceeding `risk_score >= 0.80` is quarantined at Stage 3/4.
- **Machine-Checkable Validation:** `tools/spec_validation/validators/validate_unicode.py`
- **Linked Tests:** `fixtures/unicode_test_cases.json`, `audit_round5_independent_probes.py` (`SEC2_MEDIUM01_BENIGN`, `SEC3D`).

---

### 2.3 `CTR-CLM-001`: Claim Graph Closed Schema

- **Contract ID:** `CTR-CLM-001`
- **Description:** Closed semantic graph schema representing atomic factual claims extracted from candidate answers.
- **Inputs:** Candidate factual sentence string.
- **Outputs:** Canonical Claim Graph JSON (`graph_id`, `nodes`, `edges`, `is_passive`, `unknown_agent`).
- **Preconditions:** Non-empty candidate string; sentence segmentation completed.
- **Postconditions:** All nodes belong to closed enum: `{"entity", "predicate", "quantity", "temporal", "condition", "modifier"}`. All edges belong to closed enum: `{"subject_of", "object_of", "agent_of", "patient_of", "quantifies", "temporally_bounds", "conditions", "modifies", "coordinates_with"}`.
- **Invariants:**
  1. No dangling edges: `source_id` and `target_id` must reference existing nodes.
  2. Active sentences must contain `agent_of` or `subject_of` edge.
  3. Passive sentences must contain `patient_of` edge; if agent is unspecified, an explicit node with `is_unknown=true` must be linked.
  4. Quantity nodes must have a `quantifies` edge targeting an entity or predicate.
- **Failure Behavior:** If parsing fails or constraints are violated, extraction returns `EMPTY_CLAIM` and verdict defaults to `INSUFFICIENT_EVIDENCE`.
- **Machine-Checkable Validation:** `tools/spec_validation/validators/validate_schemas.py`
- **Linked Tests:** `fixtures/valid_claim_graphs.json`, `fixtures/invalid_claim_graphs.json`.

---

### 2.4 `CTR-EVD-001`: Evidence Grounding Graph Schema

- **Contract ID:** `CTR-EVD-001`
- **Description:** Closed semantic graph schema representing grounded evidence passages from retrieved documents.
- **Inputs:** Admissible `EvidenceDocument`.
- **Outputs:** Canonical Evidence Graph JSON (`graph_id`, `evidence_id`, `document_id`, `passage_text`, `provenance`, `nodes`, `edges`).
- **Preconditions:** Document has passed Pre-generation Containment (`quarantined=false`).
- **Postconditions:** Node spans define exact byte/character offsets into `passage_text`. Provenance block includes `source`, `timestamp`, `trust_level`, and `signature_verified`.
- **Invariants:**
  1. No dangling edges allowed.
  2. Node text must match `passage_text[span[0]:span[1]]`.
- **Failure Behavior:** Invalid evidence graph causes document to be dropped from grounding index with audit warning.
- **Machine-Checkable Validation:** `tools/spec_validation/validators/validate_schemas.py`
- **Linked Tests:** `fixtures/valid_evidence_graphs.json`, `fixtures/invalid_evidence_graphs.json`.

---

### 2.5 `CTR-CRD-001`: Coordination Truth Tables & Logic

- **Contract ID:** `CTR-CRD-001`
- **Description:** Deterministic truth tables for compound factual clauses coordinated by `AND`, `OR`, `SEQ`, and `CONTRAST`.
- **Inputs:** Pair of atomic proposition states $(P, Q) \in \{\text{SUPPORTED}, \text{CONTRADICTED}, \text{INSUFFICIENT}, \text{UNCERTAIN}\}^2$.
- **Outputs:** Coordinated compound verdict $V \in \{\text{SUPPORTED}, \text{CONTRADICTED}, \text{INSUFFICIENT}, \text{UNCERTAIN}\}$.
- **Preconditions:** Both propositions decomposed and independently verified.
- **Postconditions:** Coordinated verdict matches canonical truth tables:
  - $\text{AND}(P, Q) = \text{SUPPORTED} \iff P = \text{SUPPORTED} \land Q = \text{SUPPORTED}$.
  - $\text{OR}(P, Q) = \text{SUPPORTED} \iff P = \text{SUPPORTED} \land Q = \text{SUPPORTED}$ (in safety verification, ungrounded disjunct cannot be validated as verified factual truth).
  - $\text{SEQ}(P, Q) = \text{SUPPORTED} \iff P = \text{SUPPORTED} \land Q = \text{SUPPORTED} \land \text{order}=\text{CHRONOLOGICAL}$.
  - $\text{CONTRAST}(P, Q) = \text{SUPPORTED} \iff P = \text{SUPPORTED} \land Q = \text{SUPPORTED} \land \text{contrast}=\text{VALID}$.
- **Invariants:**
  1. Appending an unverified clause with `and`, `or`, `while`, `as well as`, `nor`, or `yet` must NEVER allow the compound claim to return `SUPPORTED`.
  2. Sequence order must be explicitly verified against temporal evidence.
- **Failure Behavior:** If order is ambiguous or reversed, returns `CONTRADICTED` or `INSUFFICIENT`.
- **Machine-Checkable Validation:** `tools/spec_validation/validators/validate_coordination.py`
- **Linked Tests:** `fixtures/coordination_cases.json`, `tests/unit/test_phase_03_g3_verification.py`.

---

### 2.6 `CTR-TMP-001`: Temporal Reasoning & Interval Scoping

- **Contract ID:** `CTR-TMP-001`
- **Description:** Interval arithmetic and scoping logic for temporal claims, schedules, and historical evidence.
- **Inputs:** `ClaimInterval([t_{c1}, t_{c2}])`, `EvidenceInterval([t_{e1}, t_{e2}])`, `reference_time: Optional[datetime]`
- **Outputs:** `TemporalVerdict(alignment: SUPPORTED | CONTRADICTED | INSUFFICIENT_EVIDENCE | UNCERTAIN)`
- **Preconditions:** Timestamps parsed as ISO-8601.
- **Postconditions:** Claim interval $[t_{c1}, t_{c2}]$ is supported only if $[t_{c1}, t_{c2}] \subseteq [t_{e1}, t_{e2}]$.
- **Invariants:**
  1. Finite historical evidence $[t_{e1}, t_{e2}]$ must NEVER support an unrestricted open-ended claim $[t_{c1}, \infty)$.
  2. Relative temporal expressions ("currently", "yesterday") without a reference timestamp must evaluate to `UNCERTAIN`.
- **Failure Behavior:** Missing or contradictory timestamps yield `UNCERTAIN`.
- **Machine-Checkable Validation:** `tools/spec_validation/validators/validate_temporal.py`
- **Linked Tests:** `fixtures/temporal_cases.json`.

---

### 2.7 `CTR-QNT-001`: Quantities, Units, and Object Binding

- **Contract ID:** `CTR-QNT-001`
- **Description:** Enforces strict numeric, unit, dimension, and entity/event binding for dosages, frequencies, and measurements.
- **Inputs:** `ClaimQuantity(value, unit, target_node_id)`, `EvidenceQuantity(value, unit, target_node_id)`
- **Outputs:** `QuantityMatchStatus(MATCHED | MISMATCHED | UNBOUND)`
- **Preconditions:** Strict numeric matching flag enabled (`strict_numeric_matching=True`).
- **Postconditions:** Quantities match only if normalized numeric values match within tolerance (0.0% for clinical dosages) AND units are dimensionally equivalent (e.g. 500 mg = 0.5 g).
- **Invariants:**
  1. A quantity bound to Object A in evidence cannot ground the same quantity for Object B in the claim.
  2. Written number words ("fifty", "50") must normalize to identical values.
- **Failure Behavior:** Unbound quantity or unit mismatch yields `CONTRADICTED` or `INSUFFICIENT`.
- **Machine-Checkable Validation:** `tools/spec_validation/validators/validate_schemas.py`
- **Linked Tests:** `test_phase_03_g3_verification.py`.

---

### 2.8 `CTR-PRV-001`: Cryptographic Provenance & RFC 8785

- **Contract ID:** `CTR-PRV-001`
- **Description:** Cryptographic verification of document provenance using RFC 8785 JSON Canonicalization Scheme (JCS).
- **Inputs:** `ProvenanceRecord(payload: dict, canonical_hash: str, signature: str, key_id: str, algorithm: str, validity_period: dict, revocation_status: dict)`
- **Outputs:** `ProvenanceVerificationResult(status: VALID_TRUSTED | EXPIRED_KEY | REVOKED_KEY | DISALLOWED_ALGORITHM | HASH_MISMATCH)`
- **Preconditions:** JSON payload parses without error.
- **Postconditions:** Payload is canonicalized using deterministic JCS before SHA-256 hashing.
- **Invariants:**
  1. Algorithm must be in allowlist: `{"Ed25519", "HMAC-SHA256"}`.
  2. Expired or revoked keys must NEVER yield `VALID_TRUSTED`.
  3. Trust scores cannot be modified without invalidating signature.
- **Failure Behavior:** Verification failure demotes provenance trust level to `UNCERTAIN` or `UNTRUSTED`.
- **Machine-Checkable Validation:** `tools/spec_validation/validators/validate_provenance.py`
- **Linked Tests:** `fixtures/provenance_cases.json`.

---

### 2.9 `CTR-NLI-001`: NLI Thresholds & Decision Precedence

- **Contract ID:** `CTR-NLI-001`
- **Description:** Calibration thresholds and deterministic decision precedence for Natural Language Inference modules.
- **Inputs:** NLI logits $(p_{\text{entail}}, p_{\text{neutral}}, p_{\text{contra}})$, Structural Alignment status, Extraction confidence.
- **Outputs:** `NLIPrecedenceVerdict(SUPPORTED | CONTRADICTED | INSUFFICIENT | UNCERTAIN)`
- **Preconditions:** $p_{\text{entail}} + p_{\text{neutral}} + p_{\text{contra}} \approx 1.0$.
- **Postconditions:** Thresholds calibrated: $p_{\text{entail}} \ge 0.70$ for entailment; $p_{\text{contra}} \ge 0.60$ for contradiction.
- **Invariants:**
  1. Structural contradiction (subject mismatch, dosage conflict, polarity flip) ALWAYS overrides NLI entailment.
  2. NLI neutral or low confidence (< 0.60) can never yield `SUPPORTED`.
- **Failure Behavior:** Ambiguity yields `INSUFFICIENT` or `UNCERTAIN`.
- **Machine-Checkable Validation:** `tools/spec_validation/validators/validate_verdicts.py`
- **Linked Tests:** `tests/unit/test_phase_03_g3_verification.py`.

---

### 2.10 `CTR-VRD-001`: Claim-Level and Answer-Level Verdict Aggregation

- **Contract ID:** `CTR-VRD-001`
- **Description:** Canonical state spaces and deterministic hierarchical aggregation for claim verdicts and answer verdicts.
- **Inputs:** List of claim-level verdicts $v_i \in \{\text{SUPPORTED}, \text{CONTRADICTED}, \text{INSUFFICIENT}, \text{UNCERTAIN}, \text{EMPTY\_CLAIM}\}$.
- **Outputs:** `AnswerVerdict(SUPPORTED | PARTIALLY_SUPPORTED | CONTRADICTED | INSUFFICIENT_EVIDENCE | UNCERTAIN)`
- **Preconditions:** Claims extracted and filtered.
- **Postconditions:**
  - If all claims are `SUPPORTED` -> `SUPPORTED`.
  - If any claim is `CONTRADICTED` -> `CONTRADICTED`.
  - If some `SUPPORTED` and some `INSUFFICIENT`/`UNCERTAIN` -> `PARTIALLY_SUPPORTED`.
  - If all claims are `INSUFFICIENT` -> `INSUFFICIENT_EVIDENCE`.
- **Invariants:**
  1. An empty claim or unsupported proposition must NEVER produce `SUPPORTED`.
  2. A claim without relevant evidence must NEVER produce `SUPPORTED`.
- **Failure Behavior:** If claim list is empty, returns `INSUFFICIENT_EVIDENCE`.
- **Machine-Checkable Validation:** `tools/spec_validation/validators/validate_verdicts.py`
- **Linked Tests:** `audit_round5_independent_probes.py`.

---

### 2.11 `CTR-PRF-001`: Performance Targets & Measurement Honesty

- **Contract ID:** `CTR-PRF-001`
- **Description:** Enforces strict separation between empirical measurements and aspirational production targets.
- **Production Acceptance Targets:**
  - Peak memory: $\le 500\text{ MiB}$
  - Average G3 latency: $\le 150\text{ ms}$
- **Invariants:**
  1. No unmeasured model (e.g. spaCy transformer or large NLI) may be asserted to meet performance targets without reproducible profiling.
  2. Accuracy and security containment must never be degraded to meet latency targets.
  3. Latency must be reported as p50, p95, and p99 alongside peak memory and execution environment.
- **Machine-Checkable Validation:** `tools/spec_validation/run_all_validations.py`

---

### 2.12 `CTR-BNK-001`: Immutable Benchmark & Partition Isolation

- **Contract ID:** `CTR-BNK-001`
- **Description:** Preserves all historical failures as an immutable, append-only regression benchmark and guarantees partition isolation.
- **Inputs:** Partition manifests (`training`, `calibration`, `threshold_selection`, `final_evaluation`).
- **Outputs:** `PartitionIntegrityReport(is_strictly_disjoint: bool, zero_leakage: bool)`
- **Invariants:**
  1. Historical test sets (all 29 Round 5 false-SUPPORTED probes, 3 benign emoji cases, 5 Unicode bypasses) are immutable.
  2. No evaluation test set may be used to tune the thresholds whose final performance it measures.
  3. Positive controls must be maintained in every category to prevent degenerate all-rejecting verifiers.
- **Machine-Checkable Validation:** `tools/spec_validation/validators/validate_statistical.py`
- **Linked Tests:** `fixtures/historical_regression_cases.json`, `audit_round5_independent_probes.py`.

