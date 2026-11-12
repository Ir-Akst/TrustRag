# Phase 07 — Step 09: Phase 08 Research-Alignment Architecture Specification

**Specification Date:** 2026-11-12  
**Branch:** `phase-7` (`cc1961e`)  
**Objective:** Define the concrete, gated engineering and experimental roadmap required to close Gaps `GAP-01` through `GAP-10` and bridge TrustRAG from a deterministic software prototype to empirically verified research alignment with Papers A, B, and C.

---

## 1. Phase 08 System Architecture Overview

Phase 08 upgrades the deterministic offline skeleton while preserving all safety, fail-closed fallbacks, public redaction guarantees, and deterministic reproducibility tests:

```
User Query q
   │
   ▼
[Stage 1: G1 Input Guardrail v2]
   ├─ Canonicalize (NFKC / obfuscation / trigger rules)
   ├─ Optional Trusted LLM Paraphraser -> q'   (Paper B §6.1)
   └─ Intent Classification -> (factual | yes/no | multi-hop | opinion | flagged)
        │  Routing Policy: BLOCK severe payloads OR dual-probe (q, q') + flag raised_g3_bar
        ▼
[Stage 2: Dense + Lexical Retrieval Pool (top-s = k * m)]
   ├─ Dual query expansion (raw q + paraphrase q' when available)
   └─ Computes real L2 norm vectors & dense cosine scores
        │
        ▼
[Stage 3: G2 Multi-Signal Detector v2 + Calibration]
   ├─ F1: Local Causal LM Perplexity z-score (calibrated on clean corpus)
   ├─ F2: Dense Embedding L2-Norm z-score (clean reference corpus stats)
   ├─ F3: Dense + BM25/TF-IDF Query Match
   ├─ F4: Instruction-Content & Obfuscation Risk
   ├─ F5: Cross-Passage + (q vs q') Retrieval Consensus Deviation
   ├─ F6: Explicit Provenance Prior (UNKNOWN omitted cleanly)
   ├─ [Research Track Only]: FilterRAG SLM Freq-Density + ML-FilterRAG A/B harness
   ├─ Calibrator v2 (strict train/val-only fit, zero test leakage, ECE <= 0.08 target)
   └─ Cluster Trust Ranking + floor(K/2) Removal Cap + Weight Down-Ranking
        │
        ▼
[Stage 4: High-Trust Subset Ê Selection & Bounded Re-Answer Loop] (Paper B §6.3)
   ├─ Partition top-k into High-Trust Ê vs Uncertain/Contested (zero POISONED in generator context)
   ├─ Candidate Answer Generation (LLM/SLM backend with extractive fallback)
   └─ If G3 fails & untouched clean subset Ê_strict exists -> bounded 1-step Re-Answer on Ê_strict
        │
        ▼
[Stage 5: G3 Verification & HalluGuard SRM v2]
   ├─ Fix heuristic guards (passive/active swap, upper-bound negation, supports/unsupported conflict)
   ├─ Real NLI / Cross-Encoder claim verifier + G2 doc trust_score evidence weighting
   ├─ G3 Query Consistency Check (detect off-topic hijacks & spurious DoS refusals)  [Paper B §6.3]
   └─ HalluGuard SRM Client v2 (local GGUF/Ollama/vLLM/PEFT runner, think/non-think mode, span citation guard)
        │
        ▼
Final Decision: TRUSTED (release) | RE-ANSWERED_TRUSTED | FLAGGED | ABSTAINED | CONTRADICTED
```

---

## 2. Detailed Component Specifications

### 2.1 SRM & HalluGuard Alignment (`src/trustrag/srm/`)
- **`SRMConfig` Extensions:**
  - `backend: Literal["disabled", "local_ollama", "openai_compatible", "hf_local_peft"]`
  - `inference_mode: Literal["think", "non_think"] = "non_think"`
  - `enforce_citation_grounding: bool = True`
  - `distinguish_hallucination_taxonomy: bool = True`
- **`_parse_srm_json` & `SRMResponse` Contract:**
  - Parse `<think>(.*?)</think>` reasoning traces without breaking JSON decoding.
  - Extend `SRMClaimJudgment` with optional `hallucination_type: Literal["grounded", "intrinsic", "extrinsic", "unverified"] | None` and `cited_spans: list[str]`.
  - Verify every string in `cited_spans` exists (after NFKC/whitespace normalization) inside `request.evidence_passages`; otherwise append `SRM_UNGROUNDED_CITATION` audit flag.
- **No Circular Prompting Mode:** Add `blind_to_g3_heuristics: bool` in evaluation mode so SRM balanced accuracy on `RAGTruth` and `LLM-AggreFact` measures genuine SRM skill rather than echoing G3 rule decisions.

### 2.2 Neural Signals & Latency Fix in `G2` + `AdaptiveDefenseController` (`GAP-03`, `GAP-07`, `GAP-09`)
- **Single-Pass Controller Retrieval (`GAP-07`):** Modify `AdaptiveDefenseController.evaluate_query` so candidate retrieval + similarity matrix runs **once**, passing cached candidate scores directly to both `ContextAwareThresholdSelector` and calibrated `MultiSignalDetector` — eliminating the measured `+35.33 ms` (`p = 0.0002`, `d = 1.0701`) double-retrieval penalty.
- **Dense Embeddings (`F2`, `F3`, `F5`):** Wire optional local `sentence-transformers` encoder (`all-MiniLM-L6-v2` / `bge-small-en-v1.5`) behind `MSDConfig.embedding_backend="sentence_transformer"`, storing clean training-corpus embedding norm `(mean, std)` and disabling unnormalized TF-IDF `F2` (`ROC-AUC = 0.4704` regression).
- **Perplexity Signal (`F1`):** Wire small local causal LM (`Qwen2.5-0.5B` or `GPT-2`) behind `MSDConfig.perplexity_backend="hf_causal_lm"` calibrated on clean training corpus.
- **Platt Calibration v2:** Fit weights `(w_1..w_6, b)` AND post-hoc calibration ONLY on clean-vs-attack training splits grouped cleanly by `target_query`, validating that held-out `Brier` and `FPR` strictly improve over raw scores before promoting any artifact.

### 2.3 G1–G3 Pipeline Completeness (`GAP-04`, `GAP-05`, `GAP-06`)
1. **G1 Dual-Probe (`q` & `q'`) + Strict-G3 Mode:** Add `paraphrase_callable` hook to `InputGuardrail` and `pipeline.run`. When enabled, retrieve with both `q` and `q'`, pass Jaccard divergence into `evaluate_consensus_deviation_signals` (`F5`), and support Paper B §6.1 `escalation_on_flag` mode.
2. **G3 Heuristic Guard Patches (Immediate Deterministic Safety):**
   - Add syntactic subject/verb/object positional check (`passive/active role preservation`) to eliminate false `SUPPORTED` on swapped roles (`Step 06 Probe #3`).
   - Whitelist upper/lower-bound comparative constructions (`"not exceed"`, `"no more than"`, `"at most"`) before polarity flip rejection (`Step 06 Probe #1`).
   - Expand `_check_intra_doc_conflict` in `generalization.py` to recognize morphological antonyms (`supports`/`unsupported`, `valid`/`invalid`, `allowed`/`prohibited`) (`Step 06 Probe #11`).
   - Normalize compact scale literals (`14M` <-> `14000000`) inside numeric matching (`Step 06 Probe #5`).
3. **G3 Query Consistency Check:** Update signature to `OutputEvidenceVerifier.verify(answer_text, trusted_documents, *, query: str | None = None, doc_trust_scores: dict[str, float] | None = None, abstained: bool = False)`:
   - Detect off-topic injection hijacks (high claim overlap with prompt hijack vs near-zero relevance to `query`) and spurious refusals when high-trust documents satisfy `query`.
4. **High-Trust `Ê` Re-Answer Loop:** Replace all-or-nothing Pipeline `L190` withholding with: if any clean high-trust subset `Ê = {d in top_k : trust_score >= trust_threshold and d not poisoned/conflicted}` exists and initial draft touches mixed/untrusted docs or fails G3, regenerate once constrained strictly to `Ê`, re-verify via G3+SRM, and release if `TRUSTED`.

### 2.4 FilterRAG / ML-FilterRAG Research Harness (`GAP-08`)
- Keep FilterRAG isolated behind explicit experiment config (`enable_freq_density` + live SLM `answer_callable`).
- Only permit ML-FilterRAG feature comparisons once genuine intermediate SLM responses $a_j = \text{SLM}(q, d_j)$ and causal-LM perplexity values are computed, benchmarking cleanly against `MSD` and `MSD + Freq-Density` on PoisonedRAG & RSB.

---

## 3. Data & Benchmark Remediation Plan (`GAP-01`)

| Action | Description | Acceptance Criterion |
| --- | --- | --- |
| **1. Rebuild Disjoint Security Splits** | Split `custom_security/raw_train.jsonl` + newly generated diverse attack queries **strictly grouped by `target_query`** (`train` queries disjoint from `val` and `test`); remove duplicate records; move `BENIGN_INSTRUCTION_LIKE` controls into a separate `benign_control` flag (`is_attack=0`). | `0%` cross-split query overlap; `0%` exact/near duplicates; `benchmarks/` synced cleanly without `benchmarks_backup` mismatch. |
| **2. Acquire Offline External Benchmarks** | Download & verify hashes into `data/raw/` for `Natural Questions`, `HotpotQA`, `HaluEval-QA (10k)`, `RAGTruth (full test)`, `LLM-AggreFact` (where license permits), and `RSB (13 attacks)`. | Valid `manifest.json` + LF/CRLF SHA-256 checks + non-trivial retrieval distractor pool (`>= 5,000` passages). |
| **3. Non-Leaky Calibration & Utility Splits** | Re-fit `platt_calibrator_v2.json` strictly on newly isolated `train`; evaluate BoolQ test strictly on isolated `test` inside full distractor pool. | `0` shared queries/passages between calibration `train` and reported `test`. |

---

## 4. Phase 08 Promotion / Acceptance Gates

A Phase 08 release may only claim research alignment if **ALL** of the following pass on independent held-out test partitions:
1. **Zero Data Leakage:** `0` shared queries or passages between `train`, `val`, `test`, and calibration artifacts.
2. **Security vs Baseline:** Statistically significant ASR reduction over unprotected RAG AND offline Phase 07 (`ASR <= 0.10` targeted across factual + instruction attacks) without `FPR > 0.05` on benign procedural controls.
3. **Clean Utility Retention:** Clean `Recall@5` drop `<= 0.02` vs unprotected RAG (fixing the `-0.067` BoolQ drop) and mean adaptive overhead `<= 10 ms`.
4. **Verifier & SRM Reliability:** `0/13` heuristic critical probe failures + empirical balanced accuracy reported transparently on full `RAGTruth` and `LLM-AggreFact` using a real local 4B SRM checkpoint.

