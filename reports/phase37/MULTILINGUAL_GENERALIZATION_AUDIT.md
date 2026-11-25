# Multilingual & Transliteration Generalization Audit

## Quantitative Results (N=270 across 9 Languages)
- Overall Native Script ADR: 88.89% (120/135, 95% CI: [82.48%, 93.15%])
- Overall Transliteration ADR: 55.56% (75/135, 95% CI: [47.14%, 63.67%])
- Overall Combined ADR: 72.22% (195/270, 95% CI: [66.60%, 77.22%])

## Per-Language Detection Breakdown
| Language | Native ADR | Translit ADR | Combined ADR | Finding |
| :--- | :--- | :--- | :--- | :--- |
| **Spanish** | 100.0% (15/15) | 100.0% (15/15) | 100.0% | Robust |
| **French** | 100.0% (15/15) | 100.0% (15/15) | 100.0% | Robust |
| **German** | 100.0% (15/15) | 100.0% (15/15) | 100.0% | Robust |
| **Russian** | 100.0% (15/15) | 100.0% (15/15) | 100.0% | Robust |
| **Hindi** | 100.0% (15/15) | 100.0% (15/15) | 100.0% | Robust |
| **Arabic** | 100.0% (15/15) | 0.0% (0/15) | 50.0% | Missing Arabizi |
| **Chinese** | 100.0% (15/15) | 0.0% (0/15) | 50.0% | Missing Pinyin |
| **Japanese**| 100.0% (15/15) | 0.0% (0/15) | 50.0% | Missing Romaji |
| **English** | 0.0% (0/15) | 0.0% (0/15) | 0.0% | Engine bypass on formal English |
