# TrustRAG — Phase 03, Step 4: G3 Architecture-Level Safety Remediation Report (Round 4)

**Date:** 2026-11-10  
**Repository:** `C:\Users\aksha\OneDrive\Desktop\TrustRag`  
**Audit Baseline Addressed:** `reports/phase03_g3_round3_final_independent_audit.md`  
**Status:** `REMEDIATION COMPLETE — READY FOR INDEPENDENT AUDIT`

---

## 1. Executive Summary

Round 4 resolves all six findings (`HIGH-R3-01`, `HIGH-R3-02`, `MEDIUM-R3-01`, `LOW-R3-01`, `LOW-R3-02`, and `LOW-R3-03`) reported in the Round 3 independent audit through architecture-level improvements across atomic proposition verification, structured schedule assertions, public serialization redaction, fail-closed pipeline integrity, and Unicode format-character normalization.

Across all independent Round 3 adversarial probes (`43` Section 2 predicate probes, `30` Section 3 schedule probes, Section 4 containment/edge probes, Section 5 privacy/serialization probes, and CLI/LLM checks), reproduced false `SUPPORTED` verdicts dropped from **`8`** (`4` `HIGH-R3-01` + `4` `HIGH-R3-02`) to **`0`**. All **`291`** default unit tests pass (`2` deselected `@pytest.mark.integration`), `compileall` passes cleanly, and public CLI JSON / text outputs remain completely free of raw metadata, F4 threat snippets, and quarantined evidence.

---

## 2. Finding-by-Finding Architecture Remediation Details

### 2.1 `HIGH-R3-01` — Atomic Predicate & Conjunct Grounding (`src/trustrag/verification/output_verifier.py`)
1. **Eliminated Prefix Lexical Dilution Across Coordinated Clauses & Padded Subjects:**
   - Added `_expand_coordinated_predicates_with_bodies` returning `(full_claim, predicate_body)` pairs and passed `required_predicate_text` into `_verify_single_proposition`. Both the reconstructed atomic proposition **and** the local `predicate_body` (`pred_body_ok`) must independently meet `min_support_coverage` (`0.65`) against the same grounded evidence span, preventing long shared subject prefixes (e.g., `"Early emergency clinical responders quickly stabilized airways and fled debris."`) from masking ungrounded irregular past predicates (`"fled debris"`).
   - Added `_extract_conjunct_segments` (`conjuncts_ok`) so even unsplit coordinated structures cannot rely on one verified conjunct to carry an unverified second conjunct.
2. **Removed Closed Bare-Verb Bottleneck & Fixed Short Copula/Modal Predicates:**
   - Updated `_classify_finite_verb_token` with `allow_open_bare=True`, `_MODALS_OR_PLURAL_BARE_AUX`, `_NON_VERB_DERIV_SUFFIXES`, expanded `_NON_VERB_WORDS` (covering agentive nouns like `"responders"`/`"researchers"` and adjectives like `"toxic"`/`"fatal"`/`"banned"`/`"extreme"`), `_is_attributive_ed_modifier`, and `_leading_predicate_verb_kind`.
   - Relaxed short auxiliary/copula predicate splitting (`aux` predicates only require `len(seg_word_spans) >= 2` and `len(seg_content) >= 1`), fixing unsplit fabricated copula/modal tails (`"and is toxic"`, `"and was banned"`, `"and can spread"`, `"and will fail"`) and unseen plural/modal bare verbs (`"thwart"`, `"blunt"`, `"quench"`, `"curb"`, `"banish"`, `"quell"`).
   - Preserved comma-separated noun lists (`"fever, dry cough, and extreme fatigue"`), parenthetical expressions, titles, and numeric commas via `_inside_parentheses_or_number_mask` and comma-series consistency (`skipped_comma_item` tracking).

### 2.2 `HIGH-R3-02` — Structured Clause-Scoped Clinical Schedule Association (`src/trustrag/engine/text_utils.py`, `src/trustrag/verification/output_verifier.py`)
1. **Replaced Brittle Follower Allowlist with Syntactic Nominal Pre-Modifier Rejection (`text_utils.py`):**
   - Removed the closed `_FREQ_ADVERBIAL_FOLLOWERS` allowlist so arbitrary valid adverbial followers (`"using"`, `"per"`, `"following"`, `"via"`, `"throughout"`, `"during"`, `"before"`, etc.) are preserved consistently across both claim and evidence.
   - Replaced allowlist gating with syntactic nominal pre-modifier rejection (`_FREQ_NOMINAL_HEADS`, `_CLAUSE_CONNECTOR_WORDS`, lookahead-2 check in `_is_adverbial_schedule_adverb`), ignoring nominal noun phrases like `"maximum daily limit"`, `"daily monitoring plan"`, `"weekly report"`, `"daily summary"`, and `"monthly testing"` while retaining genuine predicate schedules (`"Testing is performed monthly"`).
2. **Structured `ScheduleAssertion` & Ambiguity/Subject Guards (`text_utils.py`, `output_verifier.py`):**
   - Added `@dataclass(frozen=True) class ScheduleAssertion` (fields: `rate_per_period`, `period`, `raw_phrase`, `subject_tokens`, `action_tokens`, `local_context_tokens`), `_split_clause_subject_predicate`, `_extract_schedule_components`, and `extract_schedule_assertions(text)` (re-used by `extract_frequency_expressions_with_context` and `extract_frequency_expressions`).
   - Updated `_evaluate_numbers_with_grounded_tokens` to score candidate multi-schedule evidence clauses using `2.0 * act_ov + 1.0 * subj_ov + 0.25 * ctx_ov + 0.5 * ent_ov`, refusing zero context overlap and refusing false `CONTRADICTS` when distinct-rate tied clauses cannot disambiguate the action (e.g., `"Blood glucose is checked daily and blood glucose is tested weekly."` vs `"Blood glucose is monitored daily."` -> `INSUFFICIENT_EVIDENCE`).
   - Added single-schedule disjoint subject protection (`c_sa.subject_tokens` vs `single_s_sa.subject_tokens`) so `"Renal labs are checked monthly per hospital protocol"` cannot falsely support `"Potassium is checked monthly."`.
   - Fixed `_verify_single_proposition` same-document contradiction suppression so a weaker wrong-clause `SUPPORTS` span in a document (`rank=0.5490`) never suppresses a strictly higher-ranked `CONTRADICTS` span in that same document (`rank=0.8279` / `0.6262`).

### 2.3 `MEDIUM-R3-01` & `LOW-R3-02` — Public `trust_report` Redaction, F4 Sanitization & Diagnostics Documentation
- **Public Metadata & F4 Snippet Redaction (`src/trustrag/pipeline/trustrag_pipeline.py`, `src/trustrag/detection/signals.py`):**
  - Updated `evaluate_instruction_content_signal` in `signals.py` so `SignalDetail.explanation` logs rule/category identifiers (`rule=<name>(category=<cat>)`, `rule=html_directive(category=HIDDEN_DIRECTIVE)`, `zero_width_or_format_chars=<n>`, `rule=repetitive_token_flood(category=DOS_FLOOD)`) without quoting attacker payload substrings or HTML comments.
  - Added `_sanitize_public_g2_assessment` in `trustrag_pipeline.py` to redact `G2DocumentAssessment.metadata` to `{"redacted_for_security": True}` (or `{}` when empty) for quarantined, filtered, or `removed_by_cap` documents inside `resp.trust_report.g2_assessments`.
  - Preserved full unredacted `retrieval_res.assessments` inside `_diagnostic_quarantine["raw_g2_assessments"]`.
- **In-Process Opt-In Diagnostics Clarification (`src/trustrag/engine/schemas.py`):**
  - Updated `PipelineResponse` docstring and `get_diagnostics(authorized=...)` docstring/commentary to explicitly state that `authorized=True` is a **trusted in-process caller explicit opt-in guard** preventing accidental exposure across normal serialization paths, rather than a multi-tenant authentication or RBAC security boundary.

### 2.4 `LOW-R3-01` & `LOW-R3-03` — Fail-Closed Unassessed-Doc Gate, Soft-Hyphen `\u00ad` & Agent-Noun Parsing
- **Fail-Closed Unassessed Retriever Document Gate (`src/trustrag/pipeline/trustrag_pipeline.py`):**
  - `TrustRAGPipeline.run` now detects any `trusted_documents` entry lacking a corresponding `G2DocumentAssessment` (`unassessed_doc_ids`), quarantines those documents before Generation, G3, and SRM, appends `"G2:UNASSESSED_DOCUMENT_QUARANTINE"` to `execution_trace`, sets `unsafe_output_quarantined=True`, and forces `overall_trust_decision = "FLAGGED"`.
- **Soft-Hyphen & Unicode Format Obfuscation Detection (`src/trustrag/engine/text_utils.py`):**
  - Expanded `ZERO_WIDTH_OR_CONTROL_RE` to include `\u00ad`, `\u034f`, `\u061c`, `\u180e`, `\u2061-\u2064`, and `\u2066-\u206f`, ensuring soft-hyphen obfuscated payloads trigger `DOC_OBFUSCATION`, are normalized cleanly before inspection, and are quarantined in `TrustRAGPipeline`.
- **Agent-Noun `-ers` Exclusions (`src/trustrag/verification/output_verifier.py`):**
  - Added common agentive `-ers` plural nouns (`responders`, `researchers`, `providers`, `prescribers`, `caregivers`, `practitioners`, `clinicians`, `officers`, etc.) to `_NON_VERB_WORDS` so matrix verb scanning skips pre-verbal nouns accurately.

---

## 3. Modified Files Inventory

- `src/trustrag/engine/text_utils.py` — Expanded `ZERO_WIDTH_OR_CONTROL_RE`; added `ScheduleAssertion`, `_split_clause_subject_predicate`, `_extract_schedule_components`, `extract_schedule_assertions`; replaced `_FREQ_ADVERBIAL_FOLLOWERS` allowlist with syntactic nominal pre-modifier filtering.
- `src/trustrag/verification/output_verifier.py` — Atomic predicate-body and per-conjunct grounding (`pred_body_ok`, `conjuncts_ok`); open-class bare/modal/copula VP decomposition with comma-series guard; agent noun exclusions; clause-scoped `ScheduleAssertion` disambiguation and single-schedule subject guard; same-doc rank-guarded contradiction preservation.
- `src/trustrag/detection/signals.py` — Sanitized `evaluate_instruction_content_signal` `SignalDetail.explanation` to emit rule/category identifiers without echoing raw threat/HTML payloads.
- `src/trustrag/engine/schemas.py` — Documented `get_diagnostics(authorized=True)` as an in-process opt-in guard (not authentication/RBAC) and added `raw_g2_assessments` diagnostic payload entry.
- `src/trustrag/pipeline/trustrag_pipeline.py` — Added `_sanitize_public_g2_assessment` public redaction, fail-closed unassessed-document quarantine (`G2:UNASSESSED_DOCUMENT_QUARANTINE`), and `raw_g2_assessments` diagnostic retention.
- `tests/unit/test_phase_03_g3_verification.py` — Added `38` new Round 4 tests (`41` parameterized pytest cases) covering atomic predicates/copulas, clinical schedules, public redaction, F4 sanitization, fail-closed unassessed-doc gating, Unicode obfuscation, agent nouns, and single-pass embedding spy verification (`93 -> 134` G3 tests).
- `docs/implementation_status.md` — Synced Phase 03 summary and verified suite test counts (`291 passed, 2 deselected`).
- `reports/phase03_g3_round4_remediation_report.md` — This Round 4 remediation report.
- `reports/phase03_g3_round4_test_report.md` — Complete Round 4 verification & adversarial probe execution report.

---

## 4. Known Conservative Behaviors & Residual Scope

1. **Conditional Multi-Clause Restrictive Scope (`2D_ctrl_conditional_medical`):** For `"Adults take aspirin unless bleeding occurs and avoid alcohol when dizzy."` verified against identical text, `_RESTRICTIVE_SCOPE_PATTERNS` captures `"unless bleeding occurs and avoid alcohol when dizzy"` through the end of the sentence, yielding fail-safe `INSUFFICIENT_EVIDENCE` (non-`SUPPORTED`, zero false positive).
2. **Negated Maximum-Limit Phrase Precedence (`3_nom_max_daily_limit`):** `"Never exceed the maximum daily limit when taking one tablet."` vs `"Take one tablet daily."` returns `CONTRADICTED` due to explicit negation (`"Never"`) mismatch rather than `INSUFFICIENT_EVIDENCE`.
3. **Offline / Environment Boundaries:** `ruff` and `mypy` remain unavailable in this Python environment, `2` `@pytest.mark.integration` network dataset tests are deselected by `pyproject.toml`, and external SRM/LLM HTTP backends were verified with deterministic stubs/mocks rather than live remote endpoints.

---

**Final Status:** `REMEDIATION COMPLETE — READY FOR INDEPENDENT AUDIT`

