# TrustRAG: Defense-in-Depth Security and Evidence-Grounded Verification for Retrieval-Augmented Generation

## Abstract
Retrieval-Augmented Generation (RAG) systems face two coupled failure modes in production: indirect prompt injection embedded in user queries or retrieved documents, and ungrounded or contradictory claims emitted during generation. We present **TrustRAG**, a defense-in-depth RAG architecture combining: (1) **G1**, an input guardrail integrating normalization, rule-based meta-pattern detection, semantic attack classification, multilingual/transliteration defense, and attribution-aware quote masking; (2) a **Document Firewall** enforcing strict generator-boundary quarantine; (3) **G2**, a multi-signal detection layer; and (4) **G3**, an evidence-grounded NLI verifier backed by a frozen DeBERTa-v3-small checkpoint (`141M` parameters) with short-QA contextualization, 2-sentence sliding windows, and fail-closed lifecycle controls. In Phase 44 evaluation (`seed=42`), TrustRAG achieves `98.33%` attack detection rate (59/60, 95% CI `[91.14%, 99.71%]`) and `0.0%` false-positive rate (0/100, 95% CI `[0.00%, 3.70%]`) on a fresh 160-prompt holdout, reduces benign FPR on SOC/CTI/quoted-attack prompts from `45.0%` to `5.0%` (`-40.0 pp`), maintains `0.0%` context and direct-generator leakage across 140 firewall cases, and recovers `78.0%` factual recall on HaluEval ($N=200$, up from `10.0%`) and `76.0%` on RAGTruth Summary ($N=50$, up from `16.0%`), while transparently characterizing the precision-leakage trade-off on long abstractive summaries.

---

## 1. Introduction
Enterprise RAG deployments ingest untrusted user queries and heterogeneous external corpora. Purely prompt-based defenses fail against paraphrased, multilingual, or transliterated injections, while naive keyword filters cause high false-positive rates on legitimate Security Operations Center (SOC) incident reports and Cyber Threat Intelligence (CTI) briefs. Simultaneously, post-hoc hallucination detectors frequently either abstain on short factual QA answers or miss cross-sentence contradictions. TrustRAG addresses both axes through modular, auditable gates (G1, Document Firewall, G2, G3) with strict fail-closed semantics.

## 2. Threat Model
We consider an adversary capable of: (a) submitting direct, indirect, narrative, or multilingual/transliterated prompt injections at the query boundary; (b) embedding malicious instructions inside otherwise benign analytical framing; (c) poisoning retrieved corpus documents to hijack downstream answer generation; and (d) attempting direct `AnswerGenerator` invocation bypassing retrieval filters. On the reliability axis, we consider non-adversarial hallucinations including entity substitutions, numerical conflicts, and subtle abstractive distortions.

## 3. System Architecture
TrustRAG routes every request through four sequential layers:
- **G1 (`InputGuardrail`):** Evaluates raw and normalized query variants before retrieval.
- **Document Firewall & Generator Boundary:** Sanitizes and quarantines untrusted retrieved chunks prior to `AnswerGenerator`.
- **G2 (`MultiSignalDetector`):** Aggregates retrieval-time anomaly and injection signals.
- **G3 (`EvidenceGroundedVerifier`):** Decomposes generated answers into atomic claims and verifies each claim against retrieved evidence spans using a frozen DeBERTa-v3-small NLI model, abstaining fail-closed on unsupported claims, contradictions, timeouts, or shutdowns.

## 4. Input Guardrail (G1) & Attribution-Aware Quote Masking
`InputGuardrail._evaluate_internal` inspects queries across `normalized_variants`, `_SUSPICIOUS_META_RULES`, `semantic_classifier.predict()`, and `multilingual_engine.evaluate_query()`. To eliminate false positives on SOC/CTI/educational prompts that quote attack strings for analysis without blanket whitelisting, Phase 44 introduces `_ATTRIBUTION_CONTEXT_PAT` and `_strip_attributed_quotes(text)`. Single- and double-quoted spans (`'...'`, `"..."`) are masked as `[QUOTED_EXAMPLE]` **only** when analytical/attribution framing is present. Unquoted text remains fully inspected, preserving detection of mixed benign-framing + embedded-attack payloads.

## 5. Document Firewall & Generator-Boundary Enforcement
The Document Firewall isolates instruction-like spans in retrieved passages before they reach the generator context window. Generator-boundary enforcement ensures `AnswerGenerator` cannot be invoked on unquarantined raw documents without triggering boundary rejection.

## 6. Multi-Signal Detection (G2)
G2 combines lexical, structural, and semantic anomaly signals across retrieved context chunks to flag poisoned passages before synthesis.

## 7. Evidence-Grounded Verification (G3) & Short-QA Remediation
`EvidenceGroundedVerifier` (`src/trustrag/verification/grounded_verifier.py`) addresses two failure modes diagnosed in Phase 43:
1. **Short-QA Exclusion:** Removed the `< 3` word drop in `extract_atomic_claims`, retaining 1–2 word entity/date/numeric answers while skipping only empty/trivial filler.
2. **Query Contextualization & Cross-Sentence Synthesis:** For 1–3 word claims with a query, evaluates `f"The answer to '{query.strip()}' is {claim}."`; adds adjacent 2-sentence sliding windows to `evidence_spans` and `full_evidence_text`; applies top-16 lexical-overlap span pre-filtering to bound CPU NLI latency; and enforces contradiction precedence (`best_con >= 0.55` or `best_con >= contradiction_threshold and best_con > best_ent + 0.05`).

## 8. Multilingual & Transliteration Defense
`multilingual_engine.evaluate_query()` detects non-English and transliterated imperative injections (e.g., Hinglish/romanized overrides) alongside Unicode confusable normalization.

## 9. Frozen NLI Model & Training Provenance
All neural NLI evaluations use the frozen DeBERTa-v3-small checkpoint (`/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`). All 8 checkpoint artifact files (`checkpoint_meta.json`, `config.json`, `model.safetensors`, `optimizer.pt`, `rng_state.pt`, `scheduler.pt`, `tokenizer.json`, `tokenizer_config.json`) are SHA-256 verified against `checksums.sha256` with zero retraining or weight modification across Phases 40–44.

## 10. Experimental Methodology & Datasets
All Phase 44 evaluations were executed deterministically (`seed=42`) via `reports/phase44/scripts/run_phase44_evaluation.py` against the final `src/` tree:
- `p44_g1_fresh` ($N=160$: 60 attacks across 4 categories, 100 benign controls across 4 categories).
- `p42_quoted_after` ($N=120$: 100 benign SOC/CTI/quoted/education, 20 malicious instructions).
- `halueval_200` ($N=200$: 100 factual, 100 hallucinated QA pairs).
- `ragtruth_summary_50` ($N=50$: 25 factual, 25 hallucinated long-form summaries).
- `controlled_120` ($N=120$: controlled supported, unsupported, and contradiction regimes).
- `firewall` ($N=140$: 90 malicious, 50 benign documents).
- `production_neural` ($N=15$ warm requests + 8-thread concurrency + timeout/shutdown fail-closed checks).
Confidence intervals are computed using Wilson 95% intervals.

## 11. G1 Security & Benign Utility Results
On `p44_g1_fresh` ($N=160$), G1 achieves `ADR = 98.33%` (59/60, 95% CI `[91.14%, 99.71%]`), `ASR = 1.67%`, `FPR = 0.0%` (0/100, 95% CI `[0.00%, 3.70%]`), `Precision = 100.0%`, and `F1 = 0.9916`. Per-category attack detection is `100.0%` (15/15) on direct, indirect/narrative, and multilingual/transliterated attacks, and `93.33%` (14/15) on mixed benign + embedded attacks; all four benign control categories achieve `0.0%` FPR (0/25 each). On the Phase 42 benign-quoted benchmark ($N=120$), overall benign FPR drops from `45.0%` (45/100) to `5.0%` (5/100, 95% CI `[2.15%, 11.18%]`), with `0/25` on `benign_incident_reports` (down from 80.0%) and `0/25` on `benign_threat_intel` (down from 60.0%), while retaining `100.0%` ADR (`20/20`) on malicious instructions.

## 12. Document Firewall & Bypass Results
Across $N=140$ documents (90 malicious, 50 benign), TrustRAG achieves `0.0%` context leakage (0/90, 95% CI `[0.00%, 4.09%]`), `0.0%` direct `AnswerGenerator` bypass leakage, and `0.0%` false quarantine on benign documents (0/50).

## 13. G3 Evidence Grounding Results
- **Controlled ($N=120$):** `100.0%` gate accuracy, `100.0%` supported acceptance, `100.0%` contradiction recall, `0.0%` unsupported leakage.
- **HaluEval ($N=200$):** Coverage rises from `17.0%` to `52.5%`, factual recall from `10.0%` (10/100) to `78.0%` (78/100, 95% CI `[68.93%, 85.00%]`), and factual precision from `29.41%` to `74.29%`, with hallucination leakage at `27.0%` (27/100 vs. `24.0%` baseline).
- **RAGTruth Summary ($N=50$):** Coverage rises from `12.0%` to `62.0%` and factual recall from `16.0%` (4/25) to `76.0%` (19/25, 95% CI `[56.57%, 88.50%]`), while factual precision shifts from `66.67%` to `61.29%` and hallucination leakage increases from `8.0%` (2/25) to `48.0%` (12/25, 95% CI `[30.03%, 66.50%]`).

## 14. Component Ablation & Baseline Comparison
Phase 42/43 ablations established that rule-only heuristics alone suffer high false positives on quoted attacks and miss paraphrased/transliterated attacks, while semantic + multilingual layers require attribution-aware quote masking to preserve SOC/CTI utility. Similarly, Phase 43's raw vs. sentence-wrapped HaluEval diagnosis proved that `< 3` word claim exclusion was the dominant bottleneck in QA recall, directly motivating Phase 44's query-contextualized verification.

## 15. Production Neural Execution, Caching & Lifecycle
Under Profile B genuine DeBERTa execution ($N=15$ warm requests), TrustRAG recorded `82` genuine `torch` forward passes, `209` cache hits, and `466` cache misses, with warm mean latency `1642.258 ms` (p50 `1622.672 ms`, p95 `1887.055 ms`, p99 `1994.663 ms`) and peak RSS `1543.22 MB`. Eight-thread concurrent execution succeeded, and both timeout and shutdown lifecycle hooks failed closed (`abstained=True`).

## 16. Statistical Analysis & Confidence Intervals
All primary rates are reported with exact binomial numerators/denominators and Wilson 95% confidence intervals in `reports/phase44/STATISTICAL_RESULTS.json`. Unit regression verification across `tests/unit/` yielded `819 passed, 2 skipped, 2 pre-existing failures` (`test_suspicious_inputs_flagged_and_original_preserved` and `test_temperature_calibrator_preserves_zero_clean_fpr`), and `10 passed` on the focused Phase 40/40.1/44 regression suite.

## 17. Limitations & Failure Modes
1. **Long-Form Summary Leakage:** On `RAGTruth Summary` ($N=50$), raising recall to `76.0%` increased hallucination leakage to `48.0%` (12/25); a 141M-parameter NLI model struggles to reject subtle abstractive distortions without high abstention.
2. **Residual Quoted-Attack FPR (`5.0%`) & Mixed-Attack Miss (`1/15`):** Unframed or edge-case quoted attacks still account for 5/25 false positives on the Phase 42 set, and 1/15 embedded attacks bypassed G1 in the fresh holdout.
3. **CPU Inference Latency:** `~1.64 s` mean warm latency per request on CPU may require GPU acceleration or batching for strict sub-second SLAs.

## 18. Ethical & Dual-Use Considerations
TrustRAG is a defensive guardrail and verification system. Evaluation corpora containing synthetic attack prompts are confined to `reports/phase44/` for reproducible auditing and do not target live external systems.

## 19. Reproducibility & Artifact Integrity
All scripts, raw predictions, logs, statistical outputs, and SHA-256 manifests are archived under `reports/phase44/` on branch `phase-44-final-remediation-publication-freeze`, anchored to `trustrag-v1.0.0-rc1` (`531bff32745ede1bd1b38609cc6daf653d3eff24`).

## 20. Conclusion
TrustRAG Phase 44 resolves the critical G1 benign-utility bottleneck (`45.0%` -> `5.0%` FPR) and G3 short-QA recall collapse (`10.0%` -> `78.0%` on HaluEval) while preserving `98.33%` fresh attack detection and `0.0%` firewall/generator-boundary leakage. With explicit scoping of long-summary hallucination leakage (`48.0%` on RAGTruth Summary), TrustRAG is **PUBLICATION READY WITH CLAIM LIMITATIONS**.

