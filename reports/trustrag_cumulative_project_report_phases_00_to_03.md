# TrustRAG — Cumulative Technical Report (Phases 00 through 03)

**Repository:** `C:\Users\aksha\OneDrive\Desktop\TrustRag`  
**Date:** 2026-11-11  
**Current Project Milestone:** Phases 00–03 Complete | Ready for Phase 04 (Evaluation & Experimental Benchmarking — Not Started)  
**Latest Verified Test Suite:** `python -m pytest -q` -> **`303 passed, 2 deselected`** (`0` failures)

---

## 1. Executive Project Summary

TrustRAG is an offline-capable, reproducible Retrieval-Augmented Generation (RAG) security and factuality verification engine designed to defend against corpus poisoning, hidden prompt injection, Unicode obfuscation, and unsupported or hallucinated model outputs.

Across **Phases 00 through 03**, the project built:
1. **Phase 00 (Core Foundation):** Typed YAML + environment configuration, structured JSON logging with secret filtering, deterministic seeding, hardware detection, and exception taxonomy.
2. **Phase 01 (Dataset Engineering):** 13 standardized dataset adapters, safe NFKC cleaning, SHA-256 deduplication, leakage-resistant grouped train/val/test splitting, workflow isolation, and portable manifests/dataset cards.
3. **Phase 02 (Acquisition & Security Benchmarks):** Standardized taxonomy (`SUPPORTED`/`CONTRADICTED`/`NOT_ENOUGH_EVIDENCE`, `CLEAN`/`POISONED`/`UNCERTAIN`, 7 attack families), deterministic paired synthetic security generator (up to 1,000 clean/poisoned pairs), disk safety resource manager, and 4 partitioned benchmarks under `data/benchmarks/`.
4. **Phase 03 (Core Defense Pipeline — G1, Retrieval+G2, Generation, Stage 7, G3, SRM):** End-to-end 10-stage architecture connecting Input Guardrail (`G1`), Trust-Aware Retrieval + Multi-Signal Detection (`G2`), Pre-Generation Fail-Closed Containment, Grounded Extractive Generation, Answer Unicode Inspection (`Stage 7`), Claim-Level Output Evidence Verification (`G3`, hardened across audit Rounds 1–6), Small Reasoning Model integration (`SRM`) with deterministic fallback, canonical specification contracts (`CTR-PIP-001` through `CTR-BNK-001`), and an automated 10-module specification + runtime conformance validator (`tools/spec_validation/`).

---

## 2. Phase-by-Phase Deliverables & Architecture

### Phase 00 — Core Foundation
* **Modules:** `src/trustrag/config/settings.py`, `src/trustrag/exceptions/__init__.py`, `src/trustrag/utils/logging.py`, `src/trustrag/utils/repro.py`, `configs/base.yaml`, `pyproject.toml`.
* **Key Capabilities:**
  * Precedence-based config loading (`explicit kwargs` -> `TRUSTRAG_<SECTION>_<FIELD>` env vars -> YAML -> Pydantic defaults).
  * Secret-redacting structured JSON logger (`get_logger()`).
  * Reproducible deterministic seed initialization (`set_random_seed`, `seed=42`).
  * Strongly typed exception hierarchy rooted in `TrustRAGError`.
* **Tests:** `9/9` unit tests in `tests/unit/test_foundation.py`.

---

### Phase 01 — Dataset Engineering (`trustrag.data`)
* **Modules (`src/trustrag/data/`):**
  * Core schemas & registry: `base.py`, `schemas.py` (`DocumentRecord`, `QueryRecord`, `ClaimVerificationRecord`, `SecurityRecord`, `compute_content_hash`), `registry.py`, `config/dataset_config.py`, `configs/datasets.yaml`.
  * Integrity & isolation: `preprocessing/cleaning.py`, `preprocessing/deduplication.py`, `validation.py`, `splitting.py` (`LeakageResistantSplitter`), `isolation.py` (`DatasetUsageValidator`).
  * Serialization & CLI: `storage.py` (atomic JSONL/Parquet + SHA-256), `manifest.py`, `acquisition/hf.py`, `acquisition/local.py`, `cli.py` (`python -m trustrag.data.cli` / `trustrag-data`).
  * **13 Dataset Loaders (`src/trustrag/data/loaders/`):** `natural_questions.py`, `hotpotqa.py`, `ms_marco.py`, `squad.py`, `boolq.py`, `halueval.py`, `ragtruth.py`, `llm_aggrefact.py` (eval-only gated), `wice.py`, `expertqa.py`, `rsb.py` (local import), `custom_security.py`, `fineweb.py` (deferred training corpus).
* **Documentation:** `docs/dataset_engineering.md`, `docs/dataset_license_register.md`, `docs/dataset_field_mapping.md`.
* **Tests:** `68` Phase 01 data tests (`tests/unit/data/`), `2` network integration tests in `tests/integration/test_data_acquisition.py`.

---

### Phase 02 — Dataset Acquisition & Security Benchmark Construction
* **Key Components Added:**
  * `src/trustrag/data/taxonomy.py`: Canonical claim labels (`SUPPORTED`, `CONTRADICTED`, `NOT_ENOUGH_EVIDENCE`), document security labels (`CLEAN`, `POISONED`, `UNCERTAIN`), and 7 attack families (`KNOWLEDGE_POISONING`, `PROMPT_INJECTION`, `DENIAL_OF_SERVICE`, `TRIGGER_DOS`, `CONFLICTING_EVIDENCE`, `MALICIOUS_INSTRUCTION`, `BENIGN_INSTRUCTION_LIKE`).
  * `src/trustrag/data/benchmarks/security_generator.py`: Deterministic paired clean/poisoned generator producing up to 1,000 pairs (2,000 records) linked by shared `source_id` to guarantee 0 cross-split leakage.
  * `src/trustrag/data/resource.py`, `src/trustrag/data/acquisition/manager.py`, `src/trustrag/data/quality.py`: Pre-allocation disk check (50 MB safety headroom), tiered acquisition tracking (P0/P1/P2), and dataset quality/leakage auditing.
* **Constructed Benchmarks (`data/benchmarks/`):**
  1. `clean_rag/` (train: 70, val: 15, test: 15)
  2. `knowledge_poisoning/` (train: 104, val: 22, test: 24)
  3. `hallucination/` (train: 7, val: 1, test: 3)
  4. `adversarial_robustness/` (train: 174, val: 36, test: 40)
  Each directory includes `manifest.json`, `README.md`, `quality_report.json`, and `split_report.json` verifying 0 overlap and 0 group leakage.
* **Tests:** `24` Phase 02 tests -> cumulative **`101/101`** unit tests at end of Phase 02.
* **Reports:** `reports/phase_01_report.md`, `reports/phase_01_correction_report.md`, `reports/phase_02_report.md`, `reports/phase_02_correction_report.md`, `reports/phase_02_environment_recovery.md`.

---

### Phase 03 — Integrated Defense Engine (G1, G2, Generation, Stage 7, G3, SRM)

#### Architecture Pipeline Flow (`src/trustrag/`)
```text
User Query
  ├──▶ [Stage 1: G1 InputGuardrail] (guardrails/input_guardrail.py)
  │       BLOCK (refusal + audit_hash) | FLAG (preserve original_input) | ALLOW
  ▼
[Stage 2: TrustAwareRetriever] (retrieval/retriever.py)
  │   TF-IDF unigram/bigram cosine + lexical coverage (top_k * candidate_multiplier)
  ▼
[Stages 3–4: Retrieved Unicode Scan & G2 MultiSignalDetector] (detection/msd.py, signals.py)
  │   F1 perplexity | F2 embedding_norm (require_configured) | F3 query_match
  │   F4 instruction_content | F5 consensus_deviation | F6 provenance
  │   Non-amplifying coverage_attenuated sigmoid scoring; floor(min(top_k, count)/2) removal cap
  ▼
[Stage 5: Pre-Generation Containment Gate] (pipeline/trustrag_pipeline.py)
  │   Fail-closed quarantine for G2 POISONED, security UNCERTAIN, & unassessed docs
  │   (Zero quarantined docs reach Generation, G3, SRM, logs, CLI, or public serialization)
  ▼
[Stage 6: AnswerGenerator] (generation/generator.py)
  │   Extractive grounded synthesis (CPU offline default) or optional LLM hook; abstains on empty context
  ▼
[Stage 7: Generated-Answer Unicode Inspection] (pipeline/trustrag_pipeline.py)
  │   Inspects generated text for hidden tags/invisible delimiters/confusables/fullwidth Latin;
  │   withholds flagged outputs (ANSWER_UNICODE:FLAGGED) prior to display
  ▼
[Stage 8: G3 OutputEvidenceVerifier] (verification/output_verifier.py)
  │   Atomic claim decomposition & strict multi-condition alignment (never cosine similarity alone)
  ▼
[Stage 9: SRMClient] (srm/client.py, backends.py)
  │   Configurable disabled / local_ollama / openai_compatible with DeterministicFallbackBackend
  ▼
[Stage 10: PipelineResponse & Private Diagnostics] (engine/schemas.py, pipeline/cli.py)
      Public redaction + explicit opt-in get_diagnostics(authorized=True)
```

#### Key Phase 03 Hardening & Remediation Progression
1. **G2 MSD Audit & Final Remediation (`phase03_g2_final_remediation_report.md` — `ACCEPTED`):**
   * Replaced missing-signal weight amplification with non-amplifying `coverage_attenuated` / `zero_log_odds` scoring.
   * Locked `F2` (`embedding_norm`) default to `require_configured` (`UNAVAILABLE` when reference stats absent, avoiding artificial clustering collisions).
   * Bounded retrieval removal budget strictly to `floor(min(top_k, candidate_count) / 2)` independent of `candidate_multiplier`.
   * Expanded `tests/unit/test_phase_03_g2_msd.py` to 32 tests.
2. **G3 Output Verification Hardening (Audit Rounds 1 through 6 — `src/trustrag/verification/output_verifier.py` & `text_utils.py`):**
   * **Numeric, Dosage & Unit Verification:** Word-written & digit dosages (`"fifty mg"` vs `"50 mg"`), dimensional normalization (`g`/`mg`/`mcg`), and strict entity binding.
   * **Polarity, Antonyms & Restrictive Scope:** Strict clause negation flips, antonym pairs, omitted condition/population qualifiers (`unless`, `only if`, `under supervision`, `with renal impairment`), copula/organization entity slots, and pronoun ambiguity detection.
   * **Compound & Coordinated Predicate Grounding:** Recursive decomposition across `and`, `but`, `or`, `nor`, `yet`, `while` (both participial `+ V-ing` and finite with pronoun resolution), `as well as`, causal/comparative tails (`because`, `faster than...`), and comma-separated predicates (both regular `-ed` and unseen matrix/trailing irregular-past verbs like `withdrew`, `froze`, `overcame`, `swept`, `arose`, `bled`), while sparing noun lists, academic titles, city/country pairs, numeric commas, and parentheticals.
   * **Schedule Association (`ScheduleAssertion`):** Clause-scoped subject/object-to-frequency binding handling active, passive, `or`-coordinated, plural, prepositional-phrase subjects, nominal modifiers (`maximum daily limit`), and equal-rate cross-clause leakage.
   * **Context-Aware Unicode & Containment Defense:** Exempts legitimate BMP emoji presentation selectors (`U+FE0F`) and authentic Arabic/Persian/Indic complex-script `U+200C`/`U+200D` joiners & emoji ZWJ sequences (`CLEAN`), while quarantining soft hyphens (`U+00AD`), ZWSP (`U+200B`), Unicode Tags (`U+E0001–E007F`), VS Supplement (`U+E0100–E01EF`), Hangul Fillers (`U+3164`), Interlinear Annotations (`U+FFF9–FFFB`), Latin/ASCII Cyrillic & Greek mixed-script confusables, and standalone Fullwidth ASCII compatibility attacks (`U+FF21–FF5A`).
   * **Final Polish Applied:** Resolved Round 3 edge cases `2D_ctrl_conditional_medical` (compound restrictive scope check preserving multi-clause positive controls without weakening omitted-qualifier rejection) and `3_nom_max_daily_limit` (`_is_unmatched_negated_outer_clause` preventing outer warning clauses from triggering false `CONTRADICTED` on nominal modifiers), plus Stage 7 (`ANSWER_UNICODE`) runtime inspection in `TrustRAGPipeline`.

#### Canonical Specification & Executable Validator (`tools/spec_validation/` & `reports/phase03_g3_*`)
* **6 Specification & Decision Reports Created:**
  * `reports/phase03_g3_final_canonical_specification.md`
  * `reports/phase03_g3_contract_registry.md` (12 frozen contracts: `CTR-PIP-001` Pipeline, `CTR-UNI-001` Unicode, `CTR-CLM-001` Claim Graph, `CTR-EVD-001` Evidence Graph, `CTR-CRD-001` Coordination, `CTR-TMP-001` Temporal, `CTR-QNT-001` Quantities, `CTR-PRV-001` Provenance, `CTR-NLI-001` NLI, `CTR-VRD-001` Verdicts, `CTR-PRF-001` Performance, `CTR-BNK-001` Benchmarks)
  * `reports/phase03_g3_specification_validation_report.md`
  * `reports/phase03_g3_traceability_matrix.md` (23 historical requirements/findings mapped)
  * `reports/phase03_g3_adversarial_validation_report.md` (Pass B red-team review)
  * `reports/phase03_g3_final_go_no_go.md` (`SPECIFICATION_READY_FOR_INDEPENDENT_AUDIT`)
* **Executable Validation Suite (`tools/spec_validation/`):**
  * 4 Closed JSON Schemas (`claim_graph`, `evidence_graph`, `pipeline_contract`, `provenance`)
  * 9 Test Fixture files (`valid/invalid` graphs, `unicode_test_cases`, `coordination_cases`, `temporal_cases`, `provenance_cases`, `historical_regression_cases`)
  * 10 Python Validators (`Validators A–I` checking specification/math/schemas + `Validator J: validate_runtime_conformance.py` exercising live `src/trustrag/` code & profiling latency/memory) managed by `run_all_validations.py`.

---

## 3. Cumulative Test, Audit & Performance Verification

### Executed Test & Probe Matrix
| Verification Suite | Outcome / Exit | Exact Verified Counts |
|---|---|---|
| **`python -m pytest -q`** | **Exit `0` (PASS)** | **`303 passed, 2 deselected`** (`17.68s`): `9` Foundation + `92` Phase 01/02 Data + `202` Phase 03 (`test_phase_03_defense.py`, `test_phase_03_g2_msd.py`, `test_phase_03_g3_verification.py`); `2` HF network integration tests deselected per `pyproject.toml` `-m 'not integration'` |
| **`python tools/spec_validation/run_all_validations.py`** | **Exit `0` (PASS)** | **10/10 validators PASS**, **13/13 acceptance gates PASS** (`576/576` verdict combos, `64` coordination pairs + `4` probes, `10/10` graph schemas, `9/9` Unicode policy & runtime checks, `15/15` historical G3 fixture checks, Stage 7 `True`, RFC 8785 determinism, Clopper–Pearson 95% bounds) |
| **`audit_round3_independent.py`** | **Exit `0` (PASS)** | Section 2: **`43/43`** exact (`false_supported=0`); Section 3: **`30/30`** exact (`false_supported=0`); Sections 4–5 clean |
| **`audit_round4_independent_probes.py`** | **Exit `0` (PASS)** | `3A`/`3B` `false_sup=[]`, `fn=[]`; `3C`/`3D`/`3E`/`4` containment & zero leakage clean |
| **`audit_round5_independent_probes.py`** | **Exit `0` (PASS)** | **`96/96`** G3 probes (`0` false-`SUPPORTED`, `0` false-`CONTRADICTED`); `10/10` stealth Unicode attacks quarantined; `8/8` benign emoji/multilingual docs `CLEAN`; `0` JSON/log/CLI leaks |
| **`audit_cli_llm.py`** | **Exit `0` (PASS)** | `CLI_RC=0 0`, `CLI_JSON_LEAK=False`, `REVEAL_JSON_LEAK=False`, `LLM_CALLED=0` |
| **`python -m compileall -q src tests`** | **Exit `0` (PASS)** | Zero syntax errors |

### Measured Runtime Performance (Deterministic Offline Engine)
Measured directly on `OutputEvidenceVerifier` via `Validator J` (`Windows-11`, `Python 3.12.4`, 5 warmup + 100 timed runs):
* **Cold import & initialization:** `23090.59 ms`
* **Warm verification latency:** `mean = 18.823 ms`, **`p50 = 18.165 ms`**, **`p95 = 23.384 ms`**, **`p99 = 26.024 ms`** (well below `150 ms` target)
* **Peak traced Python heap (`tracemalloc`):** **`92.377 MiB`** (well below `500 MiB` target)

---

## 4. Open Scope Boundaries & Phase 04 Readiness

1. **Ready to Start Phase 04:** All Phase 00–03 engineering, defense containment, G2/G3 safety fixes, unit tests (`303 passed`), and independent probe checks are complete with **Phase 04 (`Evaluation & Experimental Benchmarking`) untouched**.
2. **Offline vs. External Model Note:** Phase 03 benchmarks and tests execute in deterministic CPU-offline mode (no spaCy or NLI checkpoint installed/loaded, `srm.backend=disabled` by default). External LLM or Ollama SRM latency/accuracy should be measured separately during Phase 04 evaluation if enabled.
3. **Spec-Only Advanced Contracts:** Calendar ISO interval arithmetic (`CTR-TMP-001`) and cryptographic RFC 8785 key lifecycle enforcement (`CTR-PRV-001`) are formalized and checked in `tools/spec_validation/` rather than loaded on Phase 03 offline benchmarks.
4. **Historical Artifacts Disclosure:** `reports/phase03_g3_redesign_architecture_proposal_v8.md` referenced by the stabilization directive was absent on disk (baseline reconstructed from `docs/architecture.md`, `src/trustrag/`, and Round 1–5 reports); historical Round 1–5 audit reports remain preserved untouched in `reports/`.

