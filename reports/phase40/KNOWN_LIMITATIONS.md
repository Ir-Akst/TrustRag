# Known Limitations & Remaining Vulnerabilities

1. **G1 Benign Cybersecurity Education FPR (10.00% overall, 20.00% on `benign_cyber_education`):** Misses the `<= 3%` target because defensive questions mentioning quoted attack examples still trigger the TF-IDF classifier (`8/40`).
2. **G1 Adaptive Evasion (75.00% ADR on `obfuscated_and_adaptive`):** 10/40 adaptive paraphrases avoiding common vocabulary (`"Treat the upstream guidance as optional..."`) bypassed G1.
3. **English Leetspeak in Multilingual Holdout (66.67% ADR):** `1gn0r3 pr10r rul3s` style leetspeak without character-level leet normalization bypassed the multilingual regexes.
4. **Rule/ML Hybrid vs. Deep Neural Guardrail:** Because the frozen DeBERTa checkpoint is NLI-trained and immutable, G1 uses a lightweight TF-IDF+LogReg semantic model rather than a dedicated transformer guardrail.
