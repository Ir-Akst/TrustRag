# Phase 33 Independent Audit: Remaining Research Gaps & Open Challenges

## 1. Disclosed Technical Boundaries
The Phase 33 audit establishes the following open research challenges:

1. **Semantic Generalization Beyond Fixed Dictionaries:**
   - The current `SemanticAttackClassifier` relies on static regex keyword groups. While effective against targeted keywords, it drops to 8.0% ADR on unseen synonyms (`"unshackle"`, `"jettison"`, `"overrule"`).
   - *Phase 34 Priority:* Dense embedding similarity checks or dynamic semantic word-vector clustering.

2. **Transliteration & Code-Switching Detection:**
   - While native non-Latin ADR is 95.0%, transliterated/code-switched queries average only 40.0% ADR. Attackers using mixed-script and phonetic romanization can evade detection.
   - *Phase 34 Priority:* Phonetic transliteration normalization (e.g. Double Metaphone or Soundex adapted for Indic and Arabic dialects).

3. **Retrieved-Document Evasion of Surgical Firewall:**
   - When injected instructions avoid explicit meta-tags and adopt novel instructional pretexts, 25.0% leak to the generator.
   - *Phase 34 Priority:* Sentence-level perplexity / instruction-tuning likelihood scoring to detect instructions in factual prose.

4. **DeBERTa NLI CPU Latency & Neutral Bias on Real-World Paraphrasing:**
   - Sequence classification requires 64.1 ms per pair on CPU, causing 400–600 ms latency for complex multi-claim answers. Furthermore, high-variation paraphrases are often judged neutral rather than entailed.
   - *Phase 34 Priority:* Model quantization (INT8/ONNX) and fine-tuning on domain-specific lexical variation.
