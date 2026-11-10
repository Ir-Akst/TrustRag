# TrustRAG Architecture & Configuration Specification (Phases 00–03)

> **Scope:** Phases 00 through 03 (Foundation, Dataset Engineering, Benchmark Construction, and Integrated Defense Engine)  
> **Updated:** 2026-11-10

---

## 1. End-to-End Defense Pipeline Architecture

TrustRAG connects input guardrails, trust-aware retrieval, multi-signal document detection, evidence-grounded answer generation, claim-level verification, and Small Reasoning Model (SRM) review into one deterministic, auditable pipeline:

```text
User Query
  │
  ▼
[G1: InputGuardrail] (src/trustrag/guardrails/input_guardrail.py)
  ├─ BLOCK ──▶ Safe refusal response with audit hash & reason codes (skips retrieval)
  ├─ FLAG  ──▶ Annotates risk & preserves raw input; continues with downstream scrutiny
  └─ ALLOW ──▶ Passes safe cleaned query forward
  │
  ▼
[Retrieval Candidate Fetching] (src/trustrag/retrieval/retriever.py)
  │  TF-IDF unigram/bigram cosine + lexical coverage oversampling (top_k * candidate_multiplier)
  ▼
[G2: MultiSignalDetector (MSD)] (src/trustrag/detection/msd.py & signals.py)
  │  Evaluates 6 core TrustRAG signals (plus optional FilterRAG Freq-Density heuristic):
  │   F1. perplexity          (optional backend z-score; unavailable if model absent)
  │   F2. embedding_norm      (actual vector L2 norm z-score; requires configured clean ref by default)
  │   F3. query_match         (cosine relevance normalized; raw similarity preserved)
  │   F4. instruction_content (heuristic: prompt override, safety bypass, AI directives vs benign imperatives)
  │   F5. consensus_deviation (heuristic: semantic & factual peer deviation/conflicts preserved for G3)
  │   F6. provenance          (configurable priors & metadata traceability; UNKNOWN when missing)
  │  Scoring: trust_score(d) = sigmoid(w_eff · f(d) + b) with non-amplifying missing-signal coverage attenuation
  │  ├─ POISONED  ──▶ Removed up to floor(K / 2) cap where K = min(top_k, candidate_count); excess down-ranked with audit report
  │  ├─ UNCERTAIN ──▶ Retained down-ranked with conflict/insufficient-signal metadata
  │  └─ CLEAN     ──▶ Ranked cleanly into Trusted Evidence Context
  ▼
[AnswerGenerator] (src/trustrag/generation/generator.py)
  │  Extractive synthesis (offline deterministic default) or optional LLM hook;
  │  abstains cleanly when zero trusted evidence passes G2.
  ▼
[G3: OutputEvidenceVerifier] (src/trustrag/verification/output_verifier.py)
  │  Extracts atomic factual claims (filtering greetings, questions & opinions),
  │  precomputes single-pass TF-IDF/embedding span alignment, and enforces polarity,
  │  unit/dimension-matched numeric & dosage verification, proper entities, and lexical coverage
  │  (never relies on semantic similarity alone).
  │  - Claim Verdicts: SUPPORTED | CONTRADICTED | INSUFFICIENT | UNCERTAIN
  │  - Answer Verdicts: SUPPORTED | PARTIALLY_SUPPORTED | CONTRADICTED | INSUFFICIENT_EVIDENCE | UNCERTAIN
  │  - Backwards-compatible VerificationStatus & EvidenceReference traces (supporting & contradicting)
  ▼
[SRMClient (HalluGuard-inspired)] (src/trustrag/srm/client.py & backends.py)
  │  Backends: disabled (direct deterministic fallback) | local_ollama | openai_compatible
  │  Handles timeouts and unavailable servers gracefully via DeterministicFallbackBackend.
  ▼
PipelineResponse (Final Answer + Evidence Documents + Complete TrustReport & Execution Trace)
```

---

## 2. Package & Interface Layout

| Package / Module | Responsibility | Key Public Classes |
|---|---|---|
| `src/trustrag/config/` | Hierarchical YAML + env var configuration | `Settings`, `GuardrailsConfig`, `RetrievalConfig`, `MSDConfig`, `GenerationConfig`, `VerificationConfig`, `SRMConfig` |
| `src/trustrag/engine/` | Unified Phase 03 Pydantic schemas & shared lexical/polarity helpers | `EvidenceDocument`, `G1Assessment`, `G2DocumentAssessment`, `G3ClaimVerdict`, `G3AnswerVerdict`, `G3VerificationReport`, `SRMRequest`, `SRMResponse`, `TrustReport`, `PipelineResponse` |
| `src/trustrag/guardrails/` | G1 user query validation, obfuscation audit, & injection defense | `InputGuardrail` |
| `src/trustrag/detection/` | G2 Multi-Signal Detector & modular signal evaluators | `MultiSignalDetector` |
| `src/trustrag/retrieval/` | TF-IDF + lexical hybrid retrieval integrated with G2 filtering/ranking | `TrustAwareRetriever` |
| `src/trustrag/generation/` | Evidence-grounded extractive synthesis with abstention & LLM hook | `AnswerGenerator` |
| `src/trustrag/verification/` | G3 atomic claim extractor & strict factual entailment verifier | `OutputEvidenceVerifier` |
| `src/trustrag/srm/` | HalluGuard-inspired SRM client, HTTP backends, & deterministic fallback | `SRMClient`, `LocalOllamaBackend`, `OpenAICompatibleAPIBackend`, `DeterministicFallbackBackend` |
| `src/trustrag/pipeline/` | Main defense pipeline orchestrator & CLI runner | `TrustRAGPipeline`, CLI (`python -m trustrag.pipeline.cli`) |

---

## 3. Configuration Hierarchy & Overrides

Configuration loads in precedence order:
1. Explicit kwargs passed to `Settings(...)` / `load_config(...)`
2. Environment variables (`TRUSTRAG_<SECTION>_<FIELD>`, e.g., `TRUSTRAG_GUARDRAILS_BLOCK_THRESHOLD=0.65`, `TRUSTRAG_MSD_TRUST_THRESHOLD=0.70`, `TRUSTRAG_SRM_BACKEND=local_ollama`)
3. `configs/base.yaml` and `configs/datasets.yaml`
4. Pydantic model defaults

### Key Phase 03 Configuration Parameters (`configs/base.yaml`)

- **`guardrails` (`GuardrailsConfig`):**
  - `enabled` (`true`), `max_input_length` (`4096`), `flag_threshold` (`0.35`), `block_threshold` (`0.70`), `block_on_empty` (`true`), `strip_zero_width_for_analysis` (`true`).
- **`retrieval` (`RetrievalConfig`):**
  - `top_k` (`5`), `candidate_multiplier` (`3` — expands scoring/re-ranking candidate pool to `top_k * candidate_multiplier` without inflating the removal cap), `min_relevance_score` (`0.01`), `filtering_mode` (`"remove_with_cap"` | `"downrank_only"` | `"disabled"`), `enforce_removal_cap` (`true`), `removal_cap_ratio` (`0.5` -> `floor(K/2)` where `K = min(top_k, candidate_count)`), `trust_weight` (`0.45`).
- **`msd` (`MSDConfig`):**
  - `enabled` (`true`), `trust_threshold` (`0.60`), `poison_threshold` (`0.38`), `instruction_poison_threshold` (`0.55`), `instruction_flag_threshold` (`0.30`), `bias` (`0.0`).
  - Signal weights: `weight_perplexity` (`0.8`), `weight_embedding_norm` (`0.8`), `weight_query_match` (`1.2`), `weight_instruction_content` (`2.0`), `weight_consensus_deviation` (`1.0`), `weight_provenance` (`0.8`).
  - Missing-signal policy: `missing_signal_policy` (`"coverage_attenuated"` | `"zero_log_odds"` | `"strict_uncertain_on_missing"`), `min_available_signals` (`2`), `min_available_weight_ratio` (`0.25`).
  - Optional backends & priors: `perplexity_backend` (`"disabled"` | `"callable"`), `embedding_backend` (`"tfidf_raw"` | `"callable"` | `"disabled"`), `embedding_norm_reference_policy` (`"require_configured"` | `"allow_empirical_fallback"`), `provenance_priors` (`{}`), `enable_freq_density` (`false`).
- **`generation` (`GenerationConfig`):**
  - `mode` (`"extractive"` | `"llm_with_fallback"`), `max_context_docs` (`3`), `max_sentences_per_doc` (`2`), `abstain_on_empty_context` (`true`).
- **`verification` (`VerificationConfig`):**
  - `enabled` (`true`), `min_support_coverage` (`0.65`), `min_relevance_for_check` (`0.10`), `strict_numeric_matching` (`true`), `strict_negation_check` (`true`).
- **`srm` (`SRMConfig`):**
  - `enabled` (`true`), `backend` (`"disabled"` | `"local_ollama"` | `"openai_compatible"`), `model_name` (`"halluguard-srm-fallback"`), `endpoint_url` (`None`), `timeout_seconds` (`5.0`), `temperature` (`0.0`), `fallback_on_error` (`true`).

---

## 4. Critical Design Invariants

1. **Original Input Preservation:** G1 always stores the raw, unaltered `original_input` alongside `audit_hash` (SHA-256). Cleaning/de-obfuscation only creates an explicit `normalized_input` with recorded reason codes.
2. **Honest Missing Signals & Non-Invented Provenance:** G2 marks unavailable perplexity (`F1`), missing embeddings or unconfigured norm baselines (`F2`, under default `require_configured`), single-document consensus (`F5`), or missing provenance (`F6`, marked `UNKNOWN`) as `available=False, value=None`, never amplifies missing signal weights (defaults to `coverage_attenuated`), and emits `UNCERTAIN` if insufficient signals exist. Every signal explicitly records `is_heuristic: bool` and `basis: str`. Removal cap budget uses `K = min(top_k, candidate_count)`.
3. **Zero Benchmark Label Leakage:** `EvidenceDocument.from_record()` strips `clean_poison_label`, `expected_security_outcome`, and `poisoning_method` before any record enters retrieval or G2.
4. **No Semantic-Similarity-Only Support & Alignment vs. Truth Distinction:** G3 requires matching polarity, unit/dimension-verified numbers, verified named entities, and claim-side lexical coverage before assigning `SUPPORTED` (`SUPPORTS`), and emits `UNCERTAIN` when independent sources conflict (`supporting_evidence_refs` + `contradicting_evidence_refs`). Crucially, **G3 verifies evidence alignment against retrieved passages — not guaranteed external real-world truth** if an entire corpus is erroneous or incomplete.
5. **No Trained SRM Claims Without Checkpoints:** Phase 03 ships the SRM interface, HTTP backends, timeout handling, and deterministic fallback without downloading large checkpoints; `execution_status` explicitly logs `DISABLED`, `FALLBACK`, `TIMEOUT`, `UNAVAILABLE`, or `SUCCESS`.

