# Phase 29 — Remaining Research Gaps & Open Challenges

This report documents the unresolved research problems that remain beyond the scope of Phase 29:

1. **Indirect Prompt Injection in Retrieved Context**:
   - Because G2 MSD operates on geometric distance rather than instruction semantics, $44.44\%$ of indirect prompt injections reach the generator. A dedicated passage-level instruction filter is required.
2. **Adaptive Regex Evasion**:
   - Under an informed white-box adversary who alters punctuation or synonyms, G1's ADR drops to $40.00\%$. Static regex rules require augmentation with lightweight sub-word or token-embedding classifiers.
3. **Non-Latin Multilingual Invariance**:
   - G1 has 0.0% coverage on Cyrillic, Han, Devanagari, and Arabic. True multilingual robustness requires cross-lingual sentence encoders (e.g. mDeBERTa or XLM-RoBERTa).
4. **Live Generative SLM Baseline for FilterRAG**:
   - FilterRAG was evaluated in extractive proxy mode due to the absence of a live causal generative SLM in the offline environment.
