# TrustRAG — Phase 03, Step 4: G3 Output Evidence Verification Implementation Report

> **Repository:** `C:\Users\aksha\OneDrive\Desktop\TrustRag`  
> **Phase / Step:** Phase 03 — Step 4: G3 Output Evidence Verification  
> **Date:** 2026-11-10  
> **Python Runtime:** Windows 11, Python 3.12.4 (`C:\Users\aksha\AppData\Local\Programs\Python\Python312\python.exe`)  
> **Verdict:** `ACCEPTED`

---

## 1. Repository Inspection & Design Alignment Summary

Before implementing Step 4 enhancements, existing Phase 00–03 modules and test suites were directly inspected and verified:
- Verified that remediated G2 code was present and active (`coverage_attenuated` missing-signal scaling in `src/trustrag/detection/msd.py`, `require_configured` default baseline policy for `F2` in `src/trustrag/detection/signals.py`, `removal_cap_k = min(requested_top_k, candidate_count)` in `src/trustrag/retrieval/retriever.py`, and `32` passing tests in `tests/unit/test_phase_03_g2_msd.py`).
- Inspected `src/trustrag/generation/generator.py`, `src/trustrag/verification/output_verifier.py`, `src/trustrag/engine/schemas.py`, `src/trustrag/engine/text_utils.py`, `src/trustrag/srm/backends.py`, `src/trustrag/pipeline/trustrag_pipeline.py`, and `src/trustrag/pipeline/cli.py`.
- Identified exact upgrade points cleanly preserving backward compatibility with existing Phase 03 defense tests (`TestG3OutputEvidenceVerification`, `TestSRMIntegration`, `TestEndToEndDefensePipeline`) and G1/G2 components.

---

## 2. Files Created & Modified

| File | Action | Purpose & Changes |
|---|---|---|
| `src/trustrag/engine/text_utils.py` | Modified | Extended `NUMBER_UNIT_RE` with medical dosage/count units (`mcg`, `ug`, `iu`, `tablets`, `capsules`, `doses`, `weeks`, `months`) for claim & span parsing. |
| `src/trustrag/engine/schemas.py` & `src/trustrag/engine/__init__.py` | Modified | Added canonical `G3ClaimVerdict` (`SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT`, `UNCERTAIN`) and `G3AnswerVerdict` (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, `UNCERTAIN`); added `UNCERTAIN` to `EvidenceOutcome` and `VerificationStatus`; added `source_dataset` & `span_outcome` on `EvidenceReference`; added `supporting_evidence_refs`, `contradicting_evidence_refs`, and auto-mapped `verdict` on `ClaimVerificationItem`; added `verdict`, `insufficient_count`, `uncertain_count`, and `uncertain_claims` on `G3VerificationReport`. |
| `src/trustrag/verification/output_verifier.py` | Modified | Upgraded `OutputEvidenceVerifier`: compound factual clause extraction filtering greetings/questions/opinions, single-pass shared `_EvidenceSpanIndex` (batched TF-IDF + optional `embedding_callable` hook), sub-clause span indexing avoiding false self-contradiction on compound evidence, physical-dimension-aware numeric/dosage conflict checking, explicit `supporting_evidence_refs`/`contradicting_evidence_refs`, 4-outcome claim verification, and deterministic 5-outcome answer aggregation. |
| `src/trustrag/srm/backends.py` | Modified | Extended `DeterministicFallbackBackend` to account for `EvidenceOutcome.UNCERTAIN` alongside `NOT_ENOUGH_EVIDENCE` when synthesizing SRM fallback verdicts (`CAUTION`). |
| `src/trustrag/pipeline/trustrag_pipeline.py` & `src/trustrag/pipeline/cli.py` | Modified | Integrated G3 `UNCERTAIN` status and canonical `verdict` cleanly into pipeline execution traces, `SRMRequest`, overall decision (`UNVERIFIED` / `CAUTION`), and CLI output without mutating evidence or breaking existing keys. |
| `tests/unit/test_phase_03_g3_verification.py` | Created | 17 dedicated unit and E2E tests covering claim extraction, all 12 mandatory Step 4 scenarios, batched embedding call efficiency, malformed inputs, and threshold configurability. |
| `docs/architecture.md` & `docs/implementation_status.md` | Modified | Documented G3 architecture, configuration, verdict aggregation rules, alignment-vs-truth distinction, and updated test counts (`174 passed, 2 deselected`). |
| `reports/phase03_g3_implementation_report.md` & `reports/phase03_g3_test_report.md` | Created | Step 4 G3 implementation and test reports. |

---

## 3. G3 Architecture & Pipeline Data Flow

```text
User Query
  │
  ▼
[G1: InputGuardrail] (unchanged)
  │ ALLOW / FLAG
  ▼
[G2: MultiSignalDetector + TrustAwareRetriever] (remediated, unchanged)
  │ trusted_documents (metadata, provenance, source_id, source_dataset preserved)
  ▼
[AnswerGenerator]
  │ generated candidate answer (or abstained / answer_override)
  ▼
[G3: OutputEvidenceVerifier] (src/trustrag/verification/output_verifier.py)
  ├─ Step A: extract_claims(answer_text)
  │     Splits sentences/semicolons/punctuated compound factual clauses;
  │     filters questions, greetings, conversational boilerplate, and subjective opinions.
  ├─ Step B: _build_evidence_index(trusted_documents)  [SINGLE PASS]
  │     Splits spans + independent sub-clauses; fits TfidfVectorizer ONCE;
  │     optionally batches embedding_callable ONCE for spans and claims.
  ├─ Step C: verify_claim(...) per claim
  │     Checks polarity & semantic antonyms, unit/dimension-aware numeric/dosage bounds,
  │     non-initial proper entities, and claim-side lexical coverage (>= min_support_coverage).
  │     Emits SUPPORTED | CONTRADICTED | INSUFFICIENT | UNCERTAIN
  │     with separate supporting_evidence_refs & contradicting_evidence_refs.
  └─ Step D: Answer-Level Verdict Aggregation
        CONTRADICTED -> CONTRADICTED
        UNCERTAIN    -> UNCERTAIN
        ALL SUPPORTED -> SUPPORTED
        MIXED SUP/INS -> PARTIALLY_SUPPORTED
        NONE / ZERO CLAIMS -> INSUFFICIENT_EVIDENCE
  ▼
[SRMClient + TrustRAGPipeline Final Response]
```

---

## 4. Claim-Verification & Aggregation Rules

### Per-Claim Verdict Logic
For each claim $c$ evaluated against indexed spans in `trusted_documents`:
1. **`SUPPORTED` (`EvidenceOutcome.SUPPORTS`):** At least one span matches topic relevance (`>= min_relevance_for_check`), satisfies polarity consistency (`_evaluate_polarity`), satisfies exact/dimension-compatible numeric & dosage checks (`_evaluate_numbers`), contains all non-initial proper entities (`_extract_proper_entities`), achieves claim lexical coverage `>= min_support_coverage`, **and** no external document directly contradicts $c$.
2. **`CONTRADICTED` (`EvidenceOutcome.CONTRADICTS`):** No external span supports $c$, and at least one span sharing topic overlap exhibits explicit negation flip, semantic antonym conflict, same-unit numeric discrepancy (e.g., `5000mg` vs `4000mg`), or same-dimension unit scale conflict (e.g., `500mcg` vs `500mg`).
3. **`UNCERTAIN` (`EvidenceOutcome.UNCERTAIN`):** At least one document directly supports $c$ while at least one *different* document directly contradicts $c$ (`supporting_evidence_refs` and `contradicting_evidence_refs` both non-empty). Confidence is capped in `[0.50, 0.75]`.
4. **`INSUFFICIENT` (`EvidenceOutcome.NOT_ENOUGH_EVIDENCE`):** Neither direct support nor direct contradiction criteria hold (empty documents, no relevant spans, missing named entities, unverified numeric values/units, or similarity-only overlap below coverage threshold). Missing evidence is never mapped to `SUPPORTED`.

### Deterministic Answer-Level Precedence (`G3VerificationReport.verdict`)
1. `abstained` or `disabled` or `0` extracted factual claims $\rightarrow$ `INSUFFICIENT_EVIDENCE` (`ABSTAINED` / `UNVERIFIED`).
2. `contradicted_count > 0` $\rightarrow$ **`CONTRADICTED`** (`VerificationStatus.CONTRADICTED`).
3. `uncertain_count > 0` $\rightarrow$ **`UNCERTAIN`** (`VerificationStatus.UNCERTAIN`).
4. `supported_count == total_claims` ($> 0$) $\rightarrow$ **`SUPPORTED`** (`VerificationStatus.VERIFIED`). A single unsupported claim prevents `SUPPORTED`.
5. `supported_count > 0` (alongside `>= 1` `INSUFFICIENT`) $\rightarrow$ **`PARTIALLY_SUPPORTED`** (`VerificationStatus.PARTIALLY_SUPPORTED`).
6. Otherwise $\rightarrow$ **`INSUFFICIENT_EVIDENCE`** (`VerificationStatus.UNVERIFIED`).

---

## 5. Configuration Reference (`VerificationConfig` & `configs/base.yaml`)

| Parameter | Default | Description |
|---|---:|---|
| `enabled` | `true` | Enables or bypasses claim verification cleanly (`disabled` yields `INSUFFICIENT_EVIDENCE`). |
| `min_support_coverage` | `0.65` | Minimum claim-side content-word coverage required (alongside polarity, entities, numbers) for `SUPPORTED`. |
| `min_relevance_for_check` | `0.10` | Minimum span similarity before evaluating entailment/contradiction against a span. |
| `strict_numeric_matching` | `true` | Enforces unit/dimension-aware numeric and dosage alignment (`_evaluate_numbers`). |
| `strict_negation_check` | `true` | Enforces strict negation and antonym polarity checks (`_evaluate_polarity`). |
| `embedding_callable` *(runtime arg)* | `None` | Optional dense embedding batch function passed to `OutputEvidenceVerifier`; invoked at most twice per `verify()` call (spans + claims). |

---

## 6. Known Limitations & Semantic Verification vs. Factual Truth

1. **Retrieved-Evidence Alignment vs. Guaranteed Factual Truth:** G3 verifies whether claims in a generated answer are grounded in retrieved documents. If all retrieved passages agree on an inaccurate claim without contradiction in the retrieved set, G3 aligns against the supplied evidence (`SUPPORTED` relative to retrieved text), which is **not** a guarantee of external world truth. External factual truth additionally depends on trusted corpus provenance (G2) and downstream reasoning (SRM).
2. **Anaphoric Pronouns & Cross-Sentence Coreference:** `OutputEvidenceVerifier.extract_claims` intentionally avoids splitting clauses whose subject is a bare anaphoric pronoun (`"it"`, `"they"`, `"this"`) and checks sentence/sub-clause spans individually rather than resolving multi-sentence pronoun coreference chains via an external parser.
3. **Rule-Based Polarity & Lexical Coverage:** Without an external neural NLI cross-encoder installed offline, implicit paraphrases with minimal lexical overlap or subtle pragmatic implications outside `_ANTONYM_PAIRS` and `min_support_coverage` conservatively resolve to `INSUFFICIENT` (`NOT_ENOUGH_EVIDENCE`) rather than falsely claiming support.
4. **Optional Tooling Absence:** As in earlier Phase 03 steps, `ruff` and `mypy` are not installed in this global Python 3.12 runtime (`Exit 1: No module named ...`).

---

**Final Verdict:** `ACCEPTED`

