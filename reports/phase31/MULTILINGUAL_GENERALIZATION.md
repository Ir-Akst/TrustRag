# Multilingual Generalization Audit

**Auditor:** Independent ML Security Auditor & Computational Linguistics Reviewer  
**Suite:** Phase 31 9-Language Benchmark ($N=900$, 450 Attacks, 450 Clean Controls)

---

## 1. Evaluation Methodology

We evaluated G1 Input Guardrail across nine major languages:
- **Latin Script:** English, Spanish, French, German
- **Non-Latin Script:** Russian (Cyrillic), Hindi (Devanagari), Arabic (Arabic script), Chinese (Hanzi), Japanese (Kanji/Kana)

Each language was tested with 50 adversarial attacks (25 native script + 25 transliterated/dialectal) and 50 native clean domain queries.

---

## 2. Empirical Performance

### Global Metrics:
- **Total Attacks ($N=450$):** 95 Blocked, 355 Bypassed $\to$ **Global ADR: 21.11%** (95% Wilson CI: $[17.59\%, 25.12\%]$)
- **Total Controls ($N=450$):** 0 Blocked, 450 Allowed $\to$ **Global Clean FPR: 0.00%** (95% Wilson CI: $[0.00\%, 0.85\%]$)
- **Non-Latin Native Script ADR ($N=125$):** 40 Blocked $\to$ **32.00%**
- **Non-Latin Overall ADR ($N=250$):** 40 Blocked $\to$ **16.00%**

### Per-Language Confusion Matrix & Performance:

| Language | Total Attacks | Blocked (TP) | Native ADR | Translit ADR | Total Clean | Clean FP | Clean FPR | 95% Wilson CI (ADR) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 50 | **35** | 100.0% | 40.0% | 50 | 0 | 0.0% | $[56.24\%, 80.90\%]$ |
| **Hindi** | 50 | **20** | 80.0% | 0.0% | 50 | 0 | 0.0% | $[27.60\%, 53.82\%]$ |
| **Russian** | 50 | **15** | 60.0% | 0.0% | 50 | 0 | 0.0% | $[19.09\%, 43.76\%]$ |
| **German** | 50 | **10** | 20.0% | 20.0% | 50 | 0 | 0.0% | $[11.24\%, 33.04\%]$ |
| **Spanish** | 50 | **5** | 20.0% | 0.0% | 50 | 0 | 0.0% | $[4.35\%, 21.36\%]$ |
| **French** | 50 | **5** | 20.0% | 0.0% | 50 | 0 | 0.0% | $[4.35\%, 21.36\%]$ |
| **Arabic** | 50 | **5** | 20.0% | 0.0% | 50 | 0 | 0.0% | $[4.35\%, 21.36\%]$ |
| **Chinese** | 50 | **0** | 0.0% | 0.0% | 50 | 0 | 0.0% | $[0.00\%, 7.13\%]$ |
| **Japanese** | 50 | **0** | 0.0% | 0.0% | 50 | 0 | 0.0% | $[0.00\%, 7.13\%]$ |

---

## 3. Linguistic & Architectural Analysis

1. **Failure of Unsegmented Script Matching (Chinese & Japanese):** Regex engines relying on whitespace word boundaries (`\b`) fail on scripts that do not use inter-word spacing (CJK).
2. **Morphological Variation in Inflected Languages (Russian, Hindi, Arabic):** Fixed character stems fail when words conjugate or take grammatical affixes.
3. **Transliteration Evasion:** Transliterated queries (e.g., Hinglish, Arabizi, Romanized Russian) bypass native-script regexes completely (0.0% ADR).
4. **Honest Scientific Reporting:** Character matching regexes cannot substitute for true cross-lingual semantic understanding. A multilingual neural guardrail is required for robust international protection.
