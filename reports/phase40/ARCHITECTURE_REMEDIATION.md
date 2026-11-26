# Phase 40 Architecture Remediation Summary

1. **Generator-Boundary Enforcement (`src/trustrag/retrieval/generator_boundary.py`):**
   - Added `GeneratorBoundaryEnforcer` with untrusted-data XML serialization (`<untrusted_evidence doc_id="..." source="..." trust_score="...">`), cross-document split-instruction detection, and fail-closed pre-invocation revalidation wired into both `AnswerGenerator.generate()` and `TrustRAGPipeline.run()`.
2. **Document Firewall (`src/trustrag/retrieval/document_firewall.py`):**
   - Added Unicode confusable folding & zero-width stripping prior to segmentation, multi-line block segmentation (fenced code blocks, HTML comments, tables, blockquotes), and generalized citation/role-header spoofing rules.
3. **G1 Semantic Intent Classifier (`src/trustrag/guardrails/semantic_classifier.py` + `models/semantic_sec_v3.pkl`):**
   - Replaced regex-only classification with a calibrated hybrid TF-IDF (word 1-2 + char_wb 3-5) LogisticRegression semantic intent classifier trained on a disjoint Phase 40 dev corpus (`N=82`), combined with clause-level decomposition and benign technical context preservation.
4. **Multilingual & Transliteration Engine (`src/trustrag/guardrails/multilingual_engine.py` + `models/multilingual_sec_v3.pkl`):**
   - Added multi-stage transliteration normalization (Pinyin tone-number stripping, Arabizi numeral-to-phoneme mapping), Romaji `-te` form handling, benign technical/educational context guards, and a char-ngram LogisticRegression semantic classifier (`N=56` dev).
5. **G3 Evidence Verifier (`src/trustrag/verification/grounded_verifier.py`):**
   - Removed `_GEO_COMPAT` and hardcoded entity literals (`toronto`, `newton`, `venus`, `jefferson`).
   - Added general functional-role contradiction detection, implicit polarity opposition checks, tolerance-aware numerical reasoning, and batched NLI inference (`_predict_nli_batch`) with deterministic pair caching.
