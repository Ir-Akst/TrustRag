# TrustRAG Security Guarantees & Invariants

TrustRAG enforces non-negotiable security invariants across all defense stages and serving layers:

1. **Authoritative Input & Paraphrase Safety (G1):**
   - `InputGuardrail` preserves unaltered `original_input` alongside a SHA-256 `audit_hash` before any normalization or paraphrasing.
   - Zero-width characters (`U+200B`, bidirectional overrides, control sequences) and homoglyph/fullwidth obfuscation are explicitly flagged rather than silently stripped.
   - Paraphrasing (`validate_paraphrase`) is non-authoritative and rejects any rewrite altering numbers/units, negation, named entities, temporal markers, conditional clauses, or introducing injection triggers. Blocking decisions cannot be bypassed by paraphrasing.

2. **Honest Signals, Label Isolation & Removal Cap (G2 MSD):**
   - `EvidenceDocument.from_record()` strips ground-truth benchmark labels (`clean_poison_label`, `expected_security_outcome`, `poisoning_method`) prior to indexing or scoring.
   - Unavailable signals (`F1` perplexity without a model, `F2` embedding norm without a configured baseline, `F5` single-doc consensus, `F6` missing provenance) remain `available=False, value=None` / `UNKNOWN` and never amplify surviving signal weights (`coverage_attenuated`).
   - Retrieval quarantine removes `POISONED` candidates strictly up to `floor(K / 2)` where `K = min(top_k, candidate_count)`. Excess poisoned documents are down-ranked and audited without causing denial of service.

3. **Non-Circular Adaptive Governance & Fail-Safe Rollback:**
   - Calibration (`TrustCalibrator`) rejects test-split leakage, verifies SHA-256 parameter integrity on load and inference, and falls back to uncalibrated raw scores on corruption or non-finite inputs.
   - `ContextAwareThresholdSelector` and `AdaptationPolicyEngine` can tighten defense thresholds under verified risk or attack drift, never weaken below static security baselines, reject proposals sourced from retrieved documents or repetition feedback, and roll back cleanly on timeout or error.

4. **Strict Claim Grounding & Fail-Safe Abstention (G3 & SRM):**
   - `OutputEvidenceVerifier` never awards `SUPPORTED` on semantic similarity alone: it checks polarity, dosage/unit conversion (including C/F and m/ft/kg/lb), active-voice role swaps, temporal validity, intra-document contradictions, and query-answer consistency.
   - Controlled re-answering runs strictly on the high-trust document subset and abstains safely if no high-trust subset satisfies G3.
   - SRM model judgments require verified evidence substring citations; backend failures or timeouts fail explicitly via `SRMExecutionStatus` and `DeterministicFallbackBackend`.

5. **API Hardening & Tamper-Evident Auditing:**
   - Production startup (`TRUSTRAG_ENV=production`) requires `TRUSTRAG_API_TOKEN` Bearer auth and enforces token checks on mutating endpoints.
   - Security middleware applies CORS origin allowlists, sliding-window rate limiting (`429 RATE_LIMITED`), strict JSON/Pydantic validation (`400`/`422`), CSP/security headers, path-traversal protection (`404`), and immutable security invariant enforcement in `RuntimeConfigManager`.
   - `AuditLogStore` maintains an append-only SHA-256 hash chain with automatic secret redaction.

