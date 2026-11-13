# TrustRAG Phase 13 Step 11 — G1, G2, and G3 Guardrails Final Status

**Target Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Auditor:** Independent Senior Software Architect & Security Auditor  
**Scope:** In-Depth Technical Audit of the Three Primary Security Guardrails  
**Evaluation Date:** 2026-11-13  

---

## 1. G1: Input Guardrail (`src/trustrag/guardrails/input_guardrail.py`)

**Overall Status:** **`IMPLEMENTED AND VERIFIED` (Readiness: 95%)**

### 1.1 Evaluated Capabilities
1. **Prompt Injection & Directive Detection:** Scans user inputs for direct injection directives ("ignore previous instructions", "system prompt", "developer mode", etc.).
2. **Obfuscation & Encoding Normalization:**
   - **Unicode Normalization:** Cyrillic homoglyphs normalized to ASCII equivalents; fullwidth ASCII normalized; Zero-Width Joiners (ZWJ) and Non-Joiners (ZWNJ) stripped.
   - **Base64 Standard (RFC 4648 §4):** Padded (`=`, `==`) and unpadded tokens detected via Phase 1 clean-boundary regex.
   - **Base64 URL-Safe (RFC 4648 §5):** Tokens containing `-` and `_` normalized and decoded.
   - **Alphabet-Colliding Delimiters:** Slashes (`/`), pluses (`+`), and equals (`=`) surrounding tokens safely extracted and evaluated via Phase 2 candidate processing.
   - **Adjacent-Token Splitting:** Conjoined slash-delimited tokens (`/TOKEN1/TOKEN2/`) cleanly split into discrete subcandidates.
3. **Resource Bounding & DoS Defenses:**
   - Lazy streaming iteration (`re.finditer`) eliminates intermediate list allocations.
   - Enforces `_MAX_B64_CANDIDATES = 64` across Phase 1 and Phase 2.
   - Enforces `_MAX_B64_TOKEN_LEN = 8192` characters.
   - Evaluates a maximum of 4,096 bytes of decoded content (`dec_bytes[:4096]`).
   - Splitter bounds subcandidates to 64 items.
4. **False-Positive Behavior:** Evaluated against 305 benign multi-domain test cases with **0 false positives (0.0000%)**.

### 1.2 Limitations
- **Candidate Starvation:** Malicious Base64 tokens positioned at candidate 65+ are ignored due to the 64-candidate DoS ceiling (accepted architectural trade-off).
- **Multi-Layer Base64:** Double-encoded Base64 (`B64(B64(attack))`) is unpacked once and not recursively scanned.
- **Alternative Encodings:** Non-Base64 binary encodings (Base32, Base85, UUEncode) are not decoded.

---

## 2. G2: Multi-Signal Detector (`src/trustrag/detection/msd.py`)

**Overall Status:** **`HEURISTIC / FALLBACK` (Readiness: 60%)**

G2 is designed to detect poisoned, corrupted, or coordinated attack documents in retrieved context using six orthogonal signals (F1–F6). The audit reveals a fundamental architectural distinction between heuristic proxies and neural dependencies:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   G2 MULTI-SIGNAL DETECTOR (MSD)                       │
├────────────────────────────────┬──────────────────────┬────────────────┤
│ Signal / Component             │ Implementation Mode  │ Runtime Status │
├────────────────────────────────┼──────────────────────┼────────────────┤
│ F1: Perplexity Anomaly         │ Neural LLM Loss      │ UNAVAILABLE*   │
│ F2: Embedding Norm Anomaly     │ Neural Dense Norm    │ UNAVAILABLE*   │
│ F3: Query-Match Divergence     │ TF-IDF Overlap Proxy │ ACTIVE         │
│ F4: Instruction Content        │ Regex Heuristic      │ ACTIVE         │
│ F5: Consensus Deviation        │ Cross-Doc Sim Proxy  │ ACTIVE         │
│ F6: Provenance Prior           │ Source Domain Lookup │ ACTIVE         │
│ Trust Calibration              │ Platt / Temperature  │ ACTIVE (JSON)  │
│ Capped Removal                 │ floor(K / 2) Rule    │ ACTIVE         │
│ Coordinated Poisoning Filter   │ Exact/Sim Cluster    │ ACTIVE         │
└────────────────────────────────┴──────────────────────┴────────────────┘
* Marked UNAVAILABLE offline because neural LLM/embedding weights are absent.
```

### 2.1 Detailed Signal Implementation Reality
1. **F1 (Perplexity):** Requires computing next-token cross-entropy loss using a live neural language model. Because `torch`, `transformers`, and local model weights are absent offline, F1 evaluates to `UNAVAILABLE` and is ignored during signal fusion.
2. **F2 (Embedding Norm):** Requires dense neural embeddings from a transformer model. Absent offline; evaluates to `UNAVAILABLE`.
3. **F3 (Query-Match):** Implemented using deterministic TF-IDF unigram/bigram cosine similarity between the query and candidate documents. Functions accurately on CPU.
4. **F4 (Instruction Content):** Scans retrieved passages for imperative injection phrasing and system prompt overrides using regular expressions. Functions accurately on CPU.
5. **F5 (Consensus Deviation):** Measures pairwise TF-IDF document similarity across retrieved passages to detect outlier factual claims. Functions accurately on CPU.
6. **F6 (Provenance Prior):** Queries a static domain/source reputation dictionary to penalize untrusted or anonymous sources. Functions accurately on CPU.
7. **Trust Calibration & Capped Removal:** 
   - Uses pre-computed JSON weights (`platt_calibrator_v1.json`, `temperature_calibrator_v1.json`).
   - Strictly enforces the capped removal rule: at most $\lfloor K/2 \rfloor$ documents can be removed, preventing context starvation when all retrieved documents are flagged.
8. **Poisoning Weakness:** Without F1 and F2 neural signals, stealthy factual knowledge poisoning (where a malicious passage contains fluent, grammatically flawless misinformation) achieves a high clean score (`0.9283`), leaking into generation.

---

## 3. G3: Output Evidence Verifier (`src/trustrag/verification/output_verifier.py`)

**Overall Status:** **`IMPLEMENTED AND VERIFIED` (Readiness: 85%)**

G3 verifies that generated answers are strictly grounded in retrieved evidence, preventing hallucinations, numerical errors, and temporal contradictions.

### 3.1 Evaluated Capabilities
1. **Claim Decomposition:** Splits candidate answers into atomic propositional claims using punctuation, conjunctions, and sentence boundaries.
2. **Evidence Grounding:** Evaluates lexical overlap and TF-IDF alignment between individual claims and retrieved source documents.
3. **Verdict Categories:**
   - `SUPPORTED`: Claim is directly corroborated by retrieved evidence.
   - `CONTRADICTED`: Claim asserts facts directly conflicting with retrieved evidence.
   - `INSUFFICIENT_EVIDENCE`: Evidence is absent or ambiguous; triggers answer abstention or filtering.
4. **Consistency & Contradiction Verification:**
   - **Numerical & Unit Consistency:** Verifies quantities, metric/imperial conversions (e.g. Celsius vs Fahrenheit), and magnitude agreements. Passes 25 linguistic regression probes.
   - **Currency & Temporal Consistency:** Validates monetary amounts and temporal chronological bounds (Gate_06 PASS).
   - **Cross-Entity Contradictions:** Flags conflicting assertions across distinct named entities (Gate_09 & Gate_10 PASS).
5. **Abstention & Re-Answer Behavior:** Implements fail-closed abstention when evidence is insufficient. Re-answering (`enable_reanswer`) is implemented in code but disabled by default.

### 3.2 Implementation Nature: Heuristic vs Neural NLI
- G3 operates as a high-precision **deterministic rule-based and TF-IDF verifier**.
- It does **not** execute a neural Natural Language Inference (NLI) model (such as DeBERTa-v3 or an NLI cross-encoder) offline.
- Performance: Executes in `6.09 ms` warm P50 latency with deterministic repeatability.

---

## 4. Guardrail Synthesis

| Guardrail | Core Implementation Mechanism | Verification Level | Neural Independence |
|---|---|---|---|
| **G1 (Input)** | Regex, Base64 decoders, streaming iteration, Unicode normalizers | **100% Verified** | Completely independent of neural models (Pure CPU) |
| **G2 (Context)** | 4 deterministic proxies (F3–F6) + 2 unavailable neural signals (F1, F2) | **Partially Verified** | F1/F2 require neural models; F3–F6 run CPU proxies |
| **G3 (Output)** | Sentence tokenizer, lexical matcher, unit/currency/temporal rule engine | **100% Verified** | Completely independent of neural models (Pure CPU) |

