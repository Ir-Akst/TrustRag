# Phase 32 Workstream J: Remaining Research Gaps & Open Challenges

## 1. Transparent Evaluation of Remaining Limitations
Despite the major advances achieved in Phase 32, a hostile scientific review demands explicit disclosure of remaining boundaries:

1. **German Morphological Coverage (DE ADR = 20.0%):**
   - In the multilingual evaluation, German achieved an ADR of 20.0% (10/50 detected). Highly agglutinative compound nouns (e.g., `Sicherheitsrichtlinienumgehung`, `Konfigurationsdatenoffenbarung`) create compound token variations not captured by standard Germanic stem roots.
   - *Mitigation Plan:* Incorporate a compound-splitter tokenizer for German morphology in Phase 33.

2. **DeBERTa NLI CPU Latency (66.5 ms / pair):**
   - Evaluating complex generated answers with 10+ atomic claims against multiple retrieved documents requires sequential CPU forward passes, introducing 500–800 ms of latency.
   - *Mitigation Plan:* Quantize the DeBERTa model using INT8/ONNX runtime or batch claim verification passes across available CPU threads.

3. **Multimodal and Image-Based Prompt Injections:**
   - The current architecture operates exclusively on textual RAG inputs and retrieved passages. Vision-language models (VLMs) processing retrieved PDF scans or diagrams remain susceptible to typographic prompt injections.

4. **Highly Transliterated Code-Switching with Slang:**
   - Informal chat dialects mixing Latin script with regional slang (e.g., Romanized regional dialects) without recognizable anchor keywords can evade token-based matching if semantic intent is heavily obfuscated.
