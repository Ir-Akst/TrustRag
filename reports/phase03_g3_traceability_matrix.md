# TrustRAG Phase 03 G3 — Historical Finding & Requirement Traceability Matrix

**Date:** 2026-11-11  
**Scope:** Complete bidirectional mapping from historical audit findings (Rounds 1–5 and V7/V8 audits) to canonical contracts, schema rules, test fixtures, executed validations, and acceptance criteria.

---

## 1. Traceability Schema & Structure

Every requirement and audit defect is tracked through a 7-stage verification chain:
$$\text{Requirement ID} \longrightarrow \text{Architecture Contract} \longrightarrow \text{Schema Rule} \longrightarrow \text{Test Fixture} \longrightarrow \text{Executed Validation} \longrightarrow \text{Result} \longrightarrow \text{Acceptance Criterion}$$

---

## 2. Complete Historical Defect Traceability Matrix

| Requirement / Defect ID | Historical Origin & Defect Description | Architecture Contract | Schema / Logic Rule | Test Fixture | Executed Validation | Result | Acceptance Criterion |
|---|---|---|---|---|---|---|---|
| **REQ-R2-H01** | *NEW-HIGH-01:* Word-written dosage quantities ("fifty mg" vs "50 mg") | `CTR-QNT-001` | Number word normalization in quantity extraction | `fixtures/valid_claim_graphs.json` | `validate_schemas.py` | PASS | Dosage quantities match regardless of representation |
| **REQ-R2-H02** | *NEW-HIGH-02:* Antonyms, relative-clause inversions, omitted conditions | `CTR-CLM-001`, `CTR-VRD-001` | Strict polarity check; condition edge enforcement | `fixtures/valid_evidence_graphs.json` | `validate_verdicts.py` | PASS | Polarity inversion yields CONTRADICTED |
| **REQ-R2-M01** | *NEW-MEDIUM-01:* Entity slots, proper nouns, and acronyms | `CTR-CLM-001` | Entity node typing; exact entity grounding | `fixtures/valid_claim_graphs.json` | `validate_schemas.py` | PASS | Unmatched proper entities cannot receive SUPPORTED |
| **REQ-R2-M02** | *NEW-MEDIUM-02:* Comma-separated coordinated predicates | `CTR-CRD-001` | Comma conjunct segmentation and independent grounding | `fixtures/coordination_cases.json` | `validate_coordination.py` | PASS | Every comma-separated predicate must be supported |
| **REQ-R2-M03** | *NEW-MEDIUM-03:* G2 UNCERTAIN obfuscation/instruction risk trust leak | `CTR-PIP-001` | G2 containment threshold; non-amplifying missing signal policy | `fixtures/unicode_test_cases.json` | `validate_pipeline.py` | PASS | UNCERTAIN obfuscated doc never reaches Gen/G3/SRM |
| **REQ-R2-M04** | *NEW-MEDIUM-04:* Cross-period frequency mismatch (e.g. daily vs monthly) | `CTR-TMP-001`, `CTR-QNT-001` | Temporal interval and frequency attribute matching | `fixtures/temporal_cases.json` | `validate_temporal.py` | PASS | Frequency mismatch yields CONTRADICTED |
| **REQ-R2-L01** | *NEW-LOW-01:* Unsafe answer/evidence exposure when POISONED survives | `CTR-PIP-001` | Pre-generation containment filter; public serialization redaction | `fixtures/historical_regression_cases.json` | `validate_pipeline.py` | PASS | Quarantined evidence redacted from public output |
| **REQ-R3-H01** | *AUDIT-HIGH-01:* Closed verb list bypassed for coordinated predicates | `CTR-CRD-001` | Generalized finite-verb detection for coordinate clauses | `fixtures/coordination_cases.json` | `validate_coordination.py` | PASS | Unseen action verbs properly segmented |
| **REQ-R3-H02** | *AUDIT-HIGH-02:* Frequency mismatch bypassed for non-medication verbs | `CTR-TMP-001` | Generalized schedule predicate-object association | `fixtures/temporal_cases.json` | `validate_temporal.py` | PASS | Generalized verbs bound to temporal frequency |
| **REQ-R3-M01** | *AUDIT-MEDIUM-01:* Diagnostic quarantine fields leak in JSON | `CTR-PIP-001` | Public serialization sanitization (`model_dump`, logs, CLI) | `fixtures/historical_regression_cases.json` | `validate_pipeline.py` | PASS | Zero diagnostic leakage in unauthenticated calls |
| **REQ-R4-H01** | *NEW-R4-HIGH-01:* Coordination bypassed by `or`, `as well as`, `while + V-ing` | `CTR-CRD-001` | Deterministic truth tables for `OR`, `CONTRAST`, and non-finite clauses | `fixtures/coordination_cases.json` | `validate_coordination.py` | PASS | Disjunction with ungrounded clause yields INSUFFICIENT |
| **REQ-R4-H02** | *NEW-R4-HIGH-02:* Trailing irregular-past verbs after `-ed` matrix verb | `CTR-CLM-001` | Irregular past verb head detection in comma conjuncts | `fixtures/historical_regression_cases.json` | `validate_schemas.py` | PASS | Irregular past tails independently grounded |
| **REQ-R4-H03** | *NEW-R4-HIGH-03:* Passive schedule assertion subject binding | `CTR-CLM-001` | Explicit unknown agent representation; patient binding | `fixtures/valid_claim_graphs.json` | `validate_schemas.py` | PASS | Passive subject bound to correct lab entity |
| **REQ-R4-M01** | *NEW-R4-MEDIUM-01:* ASCII-embedded Unicode tags and variation selectors | `CTR-UNI-001` | Canonical Unicode policy; deep codepoint inspection | `fixtures/unicode_test_cases.json` | `validate_unicode.py` | PASS | Tags and VS characters quarantined at Stage 3 |
| **REQ-R5-H01** | *HIGH-01 (Round 5):* 5 coordinator failures (`nor`, `yet`, finite `while`) | `CTR-CRD-001` | Truth tables expanded for negative & contrastive coordinators | `fixtures/coordination_cases.json` | `validate_coordination.py` | PASS | Clauses joined by `nor`/`yet`/`while` independently verified |
| **REQ-R5-H02** | *HIGH-02 (Round 5):* 17 matrix irregular-past verbs (`withdrew`, `froze`, etc.) | `CTR-CLM-001` | Comprehensive irregular past verb lexicon in head scanner | `fixtures/historical_regression_cases.json` | `validate_schemas.py` | PASS | Zero false-SUPPORTED on matrix irregular past verbs |
| **REQ-R5-H03** | *HIGH-03 (Round 5):* 5 schedule subject/action association failures | `CTR-TMP-001`, `CTR-CLM-001` | Disjunctive boundary splitting; PP-subject tracking | `fixtures/historical_regression_cases.json` | `validate_temporal.py` | PASS | Schedule frequency strictly bound to clinical subject |
| **REQ-R5-S3A** | *Section 3A (Round 5):* 2 comparative claim failures (`faster than...`) | `CTR-CLM-001`, `CTR-VRD-001` | Comparative clause extraction and grounding requirement | `fixtures/historical_regression_cases.json` | `validate_verdicts.py` | PASS | Comparative assertions require explicit comparative evidence |
| **REQ-R5-M01** | *MEDIUM-01 (Round 5):* 3 benign emoji false quarantines (`U+FE0F`) | `CTR-UNI-001` | Context-aware emoji presentation selector evaluation | `fixtures/unicode_test_cases.json` | `validate_unicode.py` | PASS | Legitimate clinical emoji documents marked CLEAN |
| **REQ-R5-S3D** | *Section 3D (Round 5):* 5 Unicode/homoglyph/normalization bypasses | `CTR-UNI-001` | Scan for `U+E0100`, `U+3164`, `U+FFF9`, Cyrillic homoglyphs | `fixtures/unicode_test_cases.json` | `validate_unicode.py` | PASS | Stealth injection vectors quarantined at Stage 3 |
| **REQ-SPEC-01** | *V7/V8 Audit:* Contradictory pipeline stage definitions | `CTR-PIP-001` | Canonical 10-stage execution pipeline specification | `schemas/pipeline_contract.schema.json` | `validate_contradictions.py` | PASS | All documents, schemas, and runners use identical ordering |
| **REQ-SPEC-02** | *V7/V8 Audit:* Incompatible graph cardinalities & dangling edges | `CTR-CLM-001`, `CTR-EVD-001` | Closed schema with explicit ID reference validation | `schemas/claim_graph.schema.json` | `validate_schemas.py` | PASS | Dangling edges rejected 100% |
| **REQ-SPEC-03** | *V7/V8 Audit:* Unmeasured performance & latency claims | `CTR-PRF-001` | Explicit separation of production targets and measured latency | `reports/phase03_g3_final_canonical_specification.md` | `run_all_validations.py` | PASS | Targets disclosed as unverified production goals |

---

## 3. Verification Completeness

- Total Historical Defects & Requirements Tracked: **23**
- Total Tracked Items Machine-Validated: **23 (100.0%)**
- Total Unmapped Historical Findings: **0**
- Newly Introduced Defect Regressions: **0**

