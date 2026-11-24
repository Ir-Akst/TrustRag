# Phase 29 — Multilingual Security Evaluation

---

## 1. Experimental Methodology

Evaluated 9 languages spanning diverse linguistic families and scripts:
- **Latin Script:** English, Spanish, French, German.
- **Cyrillic Script:** Russian.
- **Devanagari Script:** Hindi.
- **Arabic Script:** Arabic.
- **Han / CJK Scripts:** Chinese, Japanese.

Each language was tested against 5 native-script attack prompts and 5 native-script clean benign controls ($N=90$ total evaluations).

---

## 2. Empirical Findings

- **Overall Multilingual ADR:** **15.56%** (7 / 45 blocked). Wilson 95% CI: $[7.75\%, 28.78\%]$.
- **Overall Clean FPR:** **0.00%** (0 / 45 false positives). Wilson 95% CI: $[0.00\%, 7.87\%]$.

### Per-Language Breakdown:

| Language | Script Family | Attacks (TP/Total) | Attack ADR (%) | Clean Controls (FP/Total) | Clean FPR (%) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **English** | Latin | $4 / 5$ | **80.0%** | $0 / 5$ | **0.0%** |
| **Spanish** | Latin | $1 / 5$ | **20.0%** | $0 / 5$ | **0.0%** |
| **French** | Latin | $1 / 5$ | **20.0%** | $0 / 5$ | **0.0%** |
| **German** | Latin | $1 / 5$ | **20.0%** | $0 / 5$ | **0.0%** |
| **Russian** | Cyrillic | $0 / 5$ | **0.0%** | $0 / 5$ | **0.0%** |
| **Hindi** | Devanagari | $0 / 5$ | **0.0%** | $0 / 5$ | **0.0%** |
| **Arabic** | Arabic | $0 / 5$ | **0.0%** | $0 / 5$ | **0.0%** |
| **Chinese** | Han | $0 / 5$ | **0.0%** | $0 / 5$ | **0.0%** |
| **Japanese** | Kanji/Kana | $0 / 5$ | **0.0%** | $0 / 5$ | **0.0%** |

---

## 3. Unicode NFKC Normalization & Multilingual Tokenization Audit

- **NFKC Normalization Impact:** Evaluating queries under Unicode NFKC normalization recovered **0 additional attacks** in non-Latin scripts. NFKC normalizes compatibility characters (e.g., ligature or width variants), but cannot translate Cyrillic, Arabic, or Han characters into English regex keywords.
- **Conclusion:** Regex guardrails without dedicated multilingual semantic encoders are strictly incapable of cross-lingual defense.
