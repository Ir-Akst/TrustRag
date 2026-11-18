# TrustRAG Phase 11.2 — Stage A: Preflight & Integration Audit

**Date:** November 18, 2026  
**Auditor:** Principal ML Evaluation Engineer & Independent Security Auditor  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**Git HEAD:** `aba5cc9d`  
**Evaluation Scope:** G1 (Input Guardrail), G2 (Multi-Signal Detector), G3 (Output Evidence Verifier), Pipeline Routing, and Neural NLI Integration

---

## 1. Executive Summary & Verification Environment

This audit establishes the preflight baseline and architectural verification for the combined Step 07–08 research campaign. All evaluations were conducted under strict read-only constraints on frozen models, training corpora, and historical audit reports.

### Environment & Runtimes
- **Hardware Architecture:** AMD EPYC 7B13 64-Core Processor, 224 GB RAM, x86_64 Linux.
- **Pipeline Virtual Environment:** `/home/aditya/rags/.venv` (Python 3.14.3, PyArrow 26.0.1, Pydantic-Settings 2.16.2, Scikit-Learn 1.9.1, NumPy 2.5.4).
- **Neural NLI Virtual Environment:** `/home/aditya/rags/.venv-train` (Python 3.10.12, PyTorch 2.14.1+cpu, Transformers 5.20.2, Accelerate 1.15.0).
- **Frozen NLI Checkpoint:** `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` (FP32 DeBERTa-v3-small, 141.9M parameters, Step 8,112, 3 full epochs).

---

## 2. G1: Input Screening & Normalization Audit

**Implementation:** `src/trustrag/guardrails/input_guardrail.py`  
**Core Utilities:** `src/trustrag/engine/text_utils.py`

### 2.1 Architecture and Preprocessing Pipeline
1. **Preservation of Raw Input:** `InputGuardrail.evaluate(query)` retains `original_input` strictly unmodified for auditability and cryptographic traceability (`audit_hash = SHA256(original_input)`).
2. **Confusable Character Folding:**
   - Detects fullwidth ASCII confusables via `count_fullwidth_ascii_confusables`.
   - Normalizes mixed-script Cyrillic/Greek/Latin homoglyphs via NFKC and character mapping (`fold_mixed_script_confusables`).
   - Strips zero-width spaces, directional control markers (`\u200b`, `\u200e`, `\u202c`), and non-printable escape sequences (`detect_obfuscation`).
3. **Payload Extraction:**
   - Extracts base64-encoded substrings ($\ge 16$ characters) and decodes them recursively for nested threat pattern matching.
4. **Threat Pattern Screening:**
   - Screens queries against compiled regex patterns across 4 canonical threat categories: `PROMPT_INJECTION`, `ROLE_HIJACK`, `MALICIOUS_COMMAND`, and `DOS_TRIGGER`.
   - Evaluates meta-probing heuristics: `hypothetical_policy_probe`, `debug_or_admin_mode_probe`, `instruction_hierarchy_override`, and `hidden_context_directive`.

### 2.2 Decision Logic & Fail-Open / Fail-Closed Characteristics
- **Decision Schema:** `G1Decision.ALLOW`, `G1Decision.FLAG`, `G1Decision.BLOCK`.
- **Thresholds:** `risk_score >= block_threshold (0.70)` $\rightarrow$ `BLOCK`; `risk_score >= flag_threshold (0.35)` $\rightarrow$ `FLAG`; otherwise $\rightarrow$ `ALLOW`.
- **Fail-Closed Boundary:** Explicit prompt injection patterns (e.g., `developer mode override`, `system prompt dump`, `rm -rf`) immediately trigger `BLOCK` with high risk scores ($0.85 - 1.0$), halting the pipeline before retrieval.
- **Fail-Open Boundary:** Phrasing variants that omit specific imperative keywords (e.g., `"Ignore your safety rules"` vs `"Ignore all safety rules"`, as uncovered in the reality audit) or benign-framed questions targeting malicious topics (e.g., `"Is AES-256 vulnerable to brute-force decryption?"`) pass through as `ALLOW` with `risk_score = 0.0`. G1 does not perform semantic intent analysis; it is strictly syntactic/lexical.

---

## 3. G2: Multi-Signal Evidence Trust Assessment (MSD)

**Implementation:** `src/trustrag/detection/msd.py`, `src/trustrag/detection/signals.py`  
**Retriever Integration:** `src/trustrag/retrieval/retriever.py`

### 3.1 Six-Signal Specification & Runtime Status

| Signal ID | Signal Name | Method / Implementation | Current Runtime Status | Failure Mode if Missing |
| :--- | :--- | :--- | :--- | :--- |
| **$S_1$ / $F_1$** | `perplexity` | Neural language model log-loss | `UNAVAILABLE_OFFLINE` | Defaults to missing feature ($f_1 = 0$); coverage attenuated |
| **$S_2$ / $F_2$** | `embedding_norm` | Dense vector L2 norm anomaly | `UNAVAILABLE_OFFLINE` | Defaults to missing feature ($f_2 = 0$); coverage attenuated |
| **$S_3$ / $F_3$** | `query_match` | TF-IDF / Lexical Cosine Similarity | `ACTIVE_LOCAL` | Falls back to token overlap |
| **$S_4$ / $F_4$** | `instruction_content` | Regex imperative injection scanner | `ACTIVE_LOCAL` | Mandatory active barrier against prompt injection |
| **$S_5$ / $F_5$** | `consensus_deviation` | Cross-document TF-IDF distance | `ACTIVE_LOCAL` | Bypassed when poisoned documents outvote clean documents ($3v1$) |
| **$S_6$ / $F_6$** | `provenance` | Source domain metadata priors | `ACTIVE_LOCAL` | Defaults to `UNKNOWN` ($0.50$) when provenance missing |

### 3.2 Mathematical Aggregation
Normalized trust scores are calculated via logistic sigmoid with coverage attenuation:
$$\text{trust\_score}(d) = \sigma\left( w_{\text{eff}} \cdot \mathbf{f}(d) + b \right)$$
where each available signal $s_i \in [0, 1]$ is centered as $f_i = 2s_i - 1 \in [-1, 1]$. Under the `coverage_attenuated` policy:
$$w_{\text{eff}} = \mathbf{w}_{\text{active}} \cdot \left( \frac{\sum_{i \in \text{available}} w_i}{\sum_{i=1}^6 w_i} \right)$$
This ensures that absent signals shrink the trust score toward the neutral prior ($0.50$) rather than falsely inflating confidence.

### 3.3 Removal Cap & Pre-Generation Quarantine
- **Removal Cap Policy:** Removal is strictly bounded by $\lfloor K \times \text{removal\_cap\_ratio} \rfloor$ where `removal_cap_ratio = 0.50`. For $K=3$, at most $\lfloor 1.5 \rfloor = 1$ document can be removed.
- **Pre-Generation Evidence Gate:**
  In `TrustRAGPipeline.run`:
  ```python
  quarantined_doc_ids = poisoned_doc_ids | uncertain_security_doc_ids | unassessed_doc_ids
  admissible_docs = [d for d in trusted_docs if d.doc_id not in quarantined_doc_ids]
  ```
  This is a **fail-closed pre-generation gate**: any document classified as `POISONED` or `UNCERTAIN` (with non-zero instruction risk) is quarantined before reaching the generator, preventing attacker-controlled context from entering generation.
- **Vulnerability:** When pure factual poison has zero instruction triggers, $S_4$ evaluates to $0.0$. Because $S_1$ and $S_2$ are `UNAVAILABLE_OFFLINE`, the document receives a benign trust score ($\sim 0.65 - 0.92$), evades quarantine, and enters the admissible context.

---

## 4. G3: Output Claim-Evidence Verification

**Implementation:** `src/trustrag/verification/output_verifier.py`

### 4.1 Grounding & Verification Logic
1. **Atomic Claim Extraction:** Parses generated answers into discrete sentences, strips bracket citations (`[doc_001]`), and filters meta-refusals, questions, and conversational pleasantries.
2. **Polarity & Antonym Detection:** Identifies strict negation cues (`not`, `never`, `cannot`) and matches opposite antonym sets (`safe` vs `unsafe`, `effective` vs `ineffective`, `confirmed` vs `refuted`).
3. **Numeric and Dimension Bounds:** Extracts scalar values, scientific units, and medical dosages, enforcing exact numeric alignment between candidate claims and evidence passages.
4. **Canonical Verdict Mapping:**
   - Step 4 claim verdicts: `SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT`, `UNCERTAIN`.
   - Answer verdicts: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, `UNCERTAIN`.

### 4.2 Controlled Re-Answer Loop ($\hat{E}$)
When an answer is not fully verified (`status != VERIFIED`) or indicates query inconsistency, G3 attempts controlled re-answering:
1. Filters admissible documents to high-trust subset $\hat{E}$ (`trust_score >= min_reanswer_trust_score (0.60)` with no conflicts).
2. If $\hat{E}$ is empty, the pipeline safely abstains (`REANSWER_NO_HIGH_TRUST_SUBSET`).
3. If $\hat{E}$ is non-empty, re-runs generator up to `max_reanswer_attempts (1)` within `reanswer_timeout_seconds (3.0s)`.
4. If re-answering remains unverified or times out, the pipeline abstains safely (`REANSWER_UNVERIFIED_ABSTAIN`).

### 4.3 Overall Pipeline Decision Precedence
In `TrustRAGPipeline.run`, final trust decisions are resolved in strict priority order:
1. `G3 == CONTRADICTED` $\rightarrow$ `CONTRADICTED`
2. `Quarantined Evidence` or `Answer Unicode Flagged` $\rightarrow$ `FLAGGED`
3. `Generator Abstained` $\rightarrow$ `ABSTAINED`
4. `SRM in {"UNTRUSTWORTHY", "REFUSE"}` $\rightarrow$ `CONTRADICTED`
5. `G1 == FLAG` or `G2 Conflict Detected` $\rightarrow$ `FLAGGED`
6. `G3 in {UNVERIFIED, PARTIALLY_SUPPORTED, UNCERTAIN}` $\rightarrow$ `UNVERIFIED`
7. `G3 == VERIFIED` and `SRM == TRUSTWORTHY` $\rightarrow$ `TRUSTED`

---

## 5. Architectural Gap: Neural NLI Integration Audit

> [!IMPORTANT]
> **Independent Audit Finding — Standalone vs Integrated Architecture:**
> The production `OutputEvidenceVerifier` class in `src/trustrag/verification/output_verifier.py` relies exclusively on **heuristic lexical and rule-based methods** (TF-IDF cosine similarity, polarity negation checks, antonym tables, numeric regex bounds).
> 
> The fine-tuned 141.9M-parameter DeBERTa-v3-small NLI model (`models/trained/deberta-v3-small-nli-phase11_1-full3epoch`), trained in Phase 11.1 and validated in Steps 04–06, **is NOT imported, wired, or called within `output_verifier.py` or `TrustRAGPipeline`**.

### Implications of the Architectural Gap:
1. **Semantic Grounding Blindness:** The production G3 verifier cannot detect subtle semantic paraphrasing, deep logical entailment, or nuanced contradictions that do not contain explicit antonyms or negation words.
2. **Evaluation Dual-Track:** In this campaign, end-to-end clean utility and security attacks are evaluated both under the **in-tree production pipeline** (heuristic G3) and under the **calibrated neural NLI model harness** at operating thresholds $\theta \in \{0.16, 0.20, 0.24, 0.50\}$.
3. **Production Readiness Blocker:** Full production deployment of TrustRAG G3 cannot be certified until a neural NLI wrapper is integrated directly into the `verify()` method of `OutputEvidenceVerifier`.

---

## 6. Preflight Conclusion & Authorization to Proceed

All pipeline subsystems (G1, G2, G3, Retrieval, Generation, and SRM fallback) have been verified and execute deterministically on CPU. Preflight requirements are satisfied. Stages B, C, D, and E proceed using the verified dual-track methodology.

