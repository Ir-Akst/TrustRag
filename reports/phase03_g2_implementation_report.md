# TrustRAG — Phase 03, Step 3: G2 Multi-Signal Detector (MSD) Implementation Report

> **Repository:** `C:\Users\aksha\OneDrive\Desktop\TrustRag`  
> **Phase / Step:** Phase 03 — Step 3: G2 Multi-Signal Detector (MSD) & Trust-Aware Retrieval  
> **Date:** 2026-11-10  
> **Verdict:** `ACCEPTED`

---

## 1. Implementation Summary

G2 Multi-Signal Detector (MSD) and trust-aware retrieval have been implemented inside the existing TrustRAG architecture in alignment with the TrustRAG, HalluGuard, and FilterRAG specifications. Every retrieved document is evaluated across **six core signals (`F1`–`F6`)** plus an optional **FilterRAG `freq_density` supplementary heuristic**, scored using the sigmoid formulation $\text{trust\_score}(d) = \sigma(w \cdot f(d) + b)$ with documented missing-signal weight renormalization, classified strictly using Phase 02's `DocumentSecurityLabel` taxonomy (`CLEAN`, `POISONED`, `UNCERTAIN`), and integrated into TF-IDF retrieval enforcing the TrustRAG $\lfloor K / 2 \rfloor$ removal cap with deterministic `original_rank` tie-breaking.

Existing Phase 00 foundation, Phase 01–02 dataset workflows, and Phase 03 G1 Input Guardrail functionality remain completely intact and passing.

---

## 2. Files Created

| File | Purpose |
|---|---|
| `tests/unit/test_phase_03_g2_msd.py` | 19 focused synthetic-fixture unit & retrieval integration tests (Test Groups A, B, and C covering F1–F6, sigmoid math, missing/insufficient signals, `freq_density`, `floor(K/2)` cap, tie-breaking, and JSON schema serialization). |
| `reports/phase03_g2_implementation_report.md` | This G2 MSD & Trust-Aware Retrieval implementation report. |

---

## 3. Files Modified

| File | Summary of G2 Changes |
|---|---|
| `src/trustrag/exceptions/__init__.py` | Updated `ConfigurationError` inheritance to `(TrustRAGError, ValueError)` so invalid config assertions raise `ConfigurationError` while preserving standard `ValueError` compatibility. |
| `src/trustrag/config/engine_config.py` | Added 6-signal weights, sigmoid `bias`, `poison_threshold`, `instruction_poison_threshold`, `instruction_flag_threshold`, missing-signal policy (`missing_signal_policy`, `min_available_signals`, `min_available_weight_ratio`), `perplexity_*` & `embedding_*` reference controls, `provenance_priors`, `enable_freq_density`, `filtering_mode`, `enforce_removal_cap`, and `removal_cap_ratio` (`<= 0.5`), raising `ConfigurationError` via `_ValidatedConfigModel`. |
| `configs/base.yaml` | Synchronized default `retrieval` and `msd` settings with `RetrievalConfig` and `MSDConfig`. |
| `src/trustrag/config/settings.py` | Wrapped `Settings.__init__` Pydantic validation errors into `ConfigurationError`. |
| `src/trustrag/engine/text_utils.py` | Added RAG-specific F4 document rules (`disable_safety_restrictions`, `direct_ai_instruction`, `answer_manipulation_directive`) to `SHARED_THREAT_PATTERNS` (`apply_to_query=False, apply_to_document=True` for doc-only directives so G1 behavior stays unchanged). |
| `src/trustrag/engine/schemas.py` & `__init__.py` | Introduced Step 8 [`SignalDetail`](file:///C:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/engine/schemas.py) (`available`, `value`, `raw_value`, `z_score`, `configured_weight`, `effective_weight`, `status`, `explanation`), [`G2DocumentAssessment`](file:///C:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/engine/schemas.py) (`document_id`, `decision: DocumentSecurityLabel`, `signals: Dict[str, SignalDetail]`, `supplementary_heuristics`, `original_retrieval_score`, `adjusted_retrieval_score`, `original_rank`, `adjusted_rank`, `removed_by_cap`), and removal-cap fields on [`RetrievalResult`](file:///C:/Users/aksha/OneDrive/Desktop/TrustRag/src/trustrag/engine/schemas.py). |
| `src/trustrag/detection/signals.py` & `__init__.py` | Implemented `evaluate_perplexity_signal` (`F1`), `evaluate_embedding_norm_signal` (`F2`), `evaluate_query_match_signal` (`F3`), `evaluate_instruction_content_signal` (`F4`), `evaluate_consensus_deviation_signals` (`F5`), `evaluate_provenance_signal` (`F6`), and optional `evaluate_freq_density_heuristic`. |
| `src/trustrag/detection/msd.py` | Implemented `MultiSignalDetector` with sigmoid `trust_score(d) = sigmoid(w · f(d) + b)`, weight renormalization over valid signals, `UNCERTAIN` on insufficient signals, and `CLEAN`/`POISONED`/`UNCERTAIN` classification guards. |
| `src/trustrag/retrieval/retriever.py` | Upgraded `TrustAwareRetriever` to compute raw unnormalized TF-IDF document vectors alongside L2 retrieval vectors, execute `MultiSignalDetector`, enforce `floor(K * removal_cap_ratio)` (`floor(K / 2)`), retain excess suspicious docs down-ranked with audit reports, and tie-break deterministically by `original_rank`. |
| `tests/unit/test_phase_03_defense.py` | Updated the 4 earlier Phase 03 assertions referencing old `TRUST`/`DOWNRANK`/`FILTER` enums and list-based signals to match `DocumentSecurityLabel` (`CLEAN`/`UNCERTAIN`/`POISONED`) and dictionary-based `signals`. |
| `docs/architecture.md` & `docs/implementation_status.md` | Documented F1–F6, sigmoid scoring, missing-signal policy, `floor(K/2)` removal cap, and updated test counts (`144 passed, 2 deselected`). |

*(No G1 logic in `src/trustrag/guardrails/input_guardrail.py` was modified; G1 tests remained untouched and passing.)*

---

## 4. Architecture Changes

```text
User Query
  └─▶ [G1 InputGuardrail] (unchanged)
        └─▶ [TrustAwareRetriever Candidate Fetch (TF-IDF + Lexical)]
              ├─ Preserves original_retrieval_score & original_rank
              ├─ Extracts real TF-IDF unnormalized vectors (or configured embeddings)
              └─▶ [G2 MultiSignalDetector]
                    ├─ F1: perplexity (optional model / callable; unavailable if missing)
                    ├─ F2: embedding_norm (real L2 norm vs ref/batch; unavailable if missing)
                    ├─ F3: query_match (cosine similarity + token coverage; raw score kept)
                    ├─ F4: instruction_content (injection/override/safety-bypass detection)
                    ├─ F5: consensus_deviation (semantic & factual peer conflict; >=2 docs)
                    ├─ F6: provenance (configurable priors & traceability; UNKNOWN if absent)
                    ├─ [Optional] freq_density (FilterRAG heuristic; outside core sigmoid)
                    ├─ Trust Score: sigmoid(sum(w'_i * (2*s_i - 1)) + b)
                    └─ Decision: CLEAN | POISONED | UNCERTAIN
                          └─▶ [Trust-Aware Ranking & floor(K/2) Removal Cap]
                                ├─ Remove up to floor(K/2) worst POISONED docs
                                ├─ Down-rank excess POISONED & all UNCERTAIN docs
                                ├─ Preserve original metadata, provenance & reports
                                └─ Tie-break strictly on original_rank
```

---

## 5. Six-Signal Explanations (Plus Optional FilterRAG Heuristic)

| ID | Key | `is_heuristic` | Measurement Basis & Missing-Backend Behavior |
|:---:|---|:---:|---|
| **F1** | `perplexity` | `False` | Evaluates model perplexity from `perplexity_callable` or passed raw perplexity against `(perplexity_reference_mean, perplexity_reference_std)` via $z = (p - \mu)/\sigma$, mapped monotonically to $\exp(-0.5 (|z| / z_{\text{thresh}})^2)$. When `perplexity_backend="disabled"` or unavailable, returns `available=False, value=None, status="UNAVAILABLE"`. Never fabricates perplexity. |
| **F2** | `embedding_norm` | `False` | Computes actual L2 norm $\|e\|_2$ from existing TF-IDF raw vectors (`norm=None`) or configured callable/precomputed embeddings. Normalizes via $z$-score against explicit configured reference stats OR candidate batch empirical peers (`len >= 3`). Marks `available=False, value=None` when disabled, missing, zero, or `< 3` peers without configured baseline. |
| **F3** | `query_match` | `False` | Measures statistical cosine similarity from TF-IDF/embedding representations + query token coverage. Preserves `raw_value` (raw similarity) and maps into `[0, 1]`. Unavailable if query or document is empty or similarity is `None`. |
| **F4** | `instruction_content` | `True` | Heuristic scanner for RAG-targeting instructions (`ignore previous`, `SYSTEM OVERRIDE`, `reveal prompts`, `disable safety restrictions`, `Note to language model`, `when answering this query`, shell exfiltration `&& curl`, hidden HTML directives, zero-width obfuscation, token flooding). Distinguishes and preserves benign procedural imperatives (recipes, standard Linux commands). |
| **F5** | `consensus_deviation` | `True` | Evaluates cross-document consistency across candidate pool using semantic cosine matrix + polarity/antonym/unit-matched numeric comparisons. Unavailable (`available=False`) when candidate pool has `< 2` non-empty documents. Preserves `conflict_detected` and `conflicting_doc_ids` for G3 rather than automatically labeling conflict `POISONED`. |
| **F6** | `provenance` | `False` | Evaluates `provenance_priors` configured by source/provenance key, explicit `verified` / `source_trust` attributes, or non-generic metadata traceability. Missing or generic `"local"` / `"unknown"` provenance without priors returns `status="UNKNOWN", available=False, value=None` and is never treated as poisoning proof. |
| *Supp.* | `freq_density` | `True` | *(Optional FilterRAG)* Measures density of shared query + intermediate answer content tokens in passage (`hits / doc_content_tokens`). Kept in `supplementary_heuristics`, disabled by default (`enable_freq_density=False`), omitted from `w · f(d) + b`, and never standalone proof of poisoning. |

---

## 6. Trust-Score Calculation

For each document $d$, normalized available signal values $s_i \in [0, 1]$ (where $1.0$ = maximally trustworthy / clean) are converted into centered features $f_i(d) = 2 s_i - 1 \in [-1, +1]$ and aggregated via:

$$\text{trust\_score}(d) = \sigma\left(\sum_{i \in A} w'_i \cdot (2 s_i - 1) + b\right)$$

- All weights $w_i \ge 0$ are configurable in `MSDConfig`, guaranteeing monotonic signal direction (higher signal value strictly raises trust).
- Default weights: `perplexity=0.8`, `embedding_norm=0.8`, `query_match=1.2`, `instruction_content=2.0`, `consensus_deviation=1.0`, `provenance=0.8`, `bias=0.0`.
- Result is strictly clamped/bounded in $(0, 1)$.

---

## 7. Missing-Signal Policy

- Unavailable signals (`available=False, value=None`) are **never fabricated or filled with synthetic neutral placeholders inside individual signal objects**.
- Under `missing_signal_policy="renormalize_available"` (default), available weights are scaled cleanly to preserve total configured logit energy:
  $$w'_i = w_i \cdot \frac{\sum_{j=1}^6 w_j}{\sum_{k \in A} w_k}$$
- **Insufficient Signals Guard:** If the candidate document is empty, available signals count $< \text{min\_available\_signals}$ (default `2`), available configured weight ratio $< \text{min\_available\_weight\_ratio}$ (default `0.25`), or `missing_signal_policy="strict_uncertain_on_missing"` with $< 6$ valid signals, G2 sets **`decision = UNCERTAIN`** (`G2_INSUFFICIENT_SIGNALS`).

---

## 8. Threshold Configuration

Default decision policy (`MSDConfig`):
1. Empty text or insufficient valid signals $\rightarrow$ `UNCERTAIN`.
2. Adversarial RAG instruction risk `instruction_risk_score >= 0.55` (`instruction_poison_threshold`) $\rightarrow$ `POISONED`.
3. `trust_score < 0.38` (`poison_threshold`): classified `UNCERTAIN` if a factual conflict triggered without instruction/perplexity/norm poisoning indicators; otherwise `POISONED`.
4. `conflict_detected` OR `instruction_risk_score >= 0.30` (`instruction_flag_threshold`) OR `trust_score < 0.60` (`trust_threshold`) $\rightarrow$ `UNCERTAIN`.
5. Otherwise $\rightarrow$ `CLEAN`.

All thresholds and weights validate at initialization and raise `ConfigurationError` on invalid combinations.

---

## 9. Retrieval Integration & 10. Removal-Cap Behavior

- `TrustAwareRetriever` retrieves oversampled candidates (`top_k * candidate_multiplier`), passes exact raw cosine similarities and unnormalized TF-IDF vectors to `MultiSignalDetector`, and supports configurable `filtering_mode`: `"remove_with_cap"`, `"downrank_only"`, or `"disabled"`.
- Under `"remove_with_cap"` (with `enforce_removal_cap=True`, `removal_cap_ratio=0.5`), out of $K$ retrieved candidates at most $\lfloor K / 2 \rfloor$ highest-risk `POISONED` documents are removed into `removed_documents` (`filtered_documents`).
- When `POISONED` candidates exceed $\lfloor K / 2 \rfloor$ (or when $K = 1$, where $\lfloor 1 / 2 \rfloor = 0$), `removal_cap_applied=True` is set and excess `POISONED` documents remain in the surviving pool **strictly down-ranked** (`tier_factor = 0.20`) with their full detection report attached.
- Ties on `adjusted_retrieval_score` break deterministically by `original_rank`. `original_retrieval_score`, `doc.metadata`, `source_id`, and `provenance` remain preserved intact.

---

## 11. Test Commands & Exact Results

| Check | Exact Command | Exit Code | Observed Result |
|---|---|---:|---|
| **G2 Unit & Integration Suite** | `$env:PYTHONPATH="src"; pytest -v tests/unit/test_phase_03_g2_msd.py` | `0` | **19 passed**, 0 failed, 0 skipped (`7.25s`) |
| **G1 Guardrail Regression Suite** | `$env:PYTHONPATH="src"; pytest -v tests/unit/test_phase_03_defense.py -k "TestG1InputGuardrail"` | `0` | **4 passed**, 0 failed, 20 deselected (`7.59s`) |
| **Complete Project Test Suite** | `$env:PYTHONPATH="src"; pytest -v` | `0` | **144 passed**, 0 failed, **2 deselected** (`tests/integration/test_data_acquisition.py` requiring live network via default `addopts = "-m 'not integration'"`) (`11.98s`) |
| **Syntax & Import Verification** | `python -m compileall -q src tests; python -c "import trustrag; from trustrag.guardrails import InputGuardrail; from trustrag.detection import MultiSignalDetector; from trustrag.retrieval import TrustAwareRetriever; print('IMPORTS_OK')"` | `0` | `IMPORTS_OK` (all modules compile & import cleanly) |
| **Configured Ruff Lint Check** | `python -m ruff check src tests` | `1` | Not installed in active environment (`No module named ruff`) |
| **Configured Mypy Type Check** | `python -m mypy src` | `1` | Not installed in active environment (`No module named mypy`) |
| **End-to-End G1 + Retrieval + G2 Smoke Test** | Python runner over `data/benchmarks/adversarial_robustness/train.jsonl` & `data/benchmarks/knowledge_poisoning/test.jsonl` | `0` | 1) On `adversarial_robustness/train.jsonl` (`K=4, CAP=2`): `G1=ALLOW`, 2 prompt-injected `POISONED` docs removed, 2 `CLEAN` docs promoted (`trust=0.9881`). 2) On `knowledge_poisoning/test.jsonl` (`K=2, CAP=1`): `G1=ALLOW`, conflicting dosage pair retained as `UNCERTAIN` (`removed=[]`) preserving conflict reports for G3. |

---

## 12. Known Limitations

1. **Retrieval Representation Scope:** Without PyTorch/SentenceTransformers/FAISS installed in the active environment, default retrieval and `F2` / `F3` / `F5` operate on TF-IDF vector spaces (`scikit-learn`). Dense neural embeddings can be connected directly through `embedding_callable`.
2. **Optional Linters Not Installed:** `ruff` and `mypy` from `requirements-dev.txt` are not present in the active Python environment.
3. **Rule-Based G2 `F4` Instruction Patterns:** Novel adversarial paraphrases completely outside structural override, safety-bypass, AI-directive, answer-manipulation, or obfuscation patterns rely on F1/F2/F5 signals when available.

---

## 13. Optional Backend Availability

- **Perplexity Model (`F1`):** Disabled by default (`perplexity_backend="disabled"`). Tested hermetically via callable backend injection in `test_missing_and_configured_perplexity_model`; no live causal LM weights are downloaded or bundled.
- **Embedding Model (`F2`/`F3`):** Uses real `scikit-learn` TF-IDF vectors by default (`embedding_backend="tfidf_raw"`); supports external `embedding_callable`; marks `F2` `UNAVAILABLE` cleanly when disabled or insufficient peers (`< 3`). No live SentenceTransformer API or downloaded checkpoint was invoked.
- **FilterRAG `freq_density`:** Disabled by default (`enable_freq_density=False`); exercised offline via lightweight `answer_callable` fixture.

---

**Final Verdict:** `ACCEPTED`

