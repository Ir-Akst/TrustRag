# Phase 33 Independent Audit: Multilingual Generalization (Native vs Transliterated)

## 1. Audit Requirement
In response to reviewer objections, Phase 33 evaluated all 9 supported languages with a strict separation between **native-script attacks** and **transliterated / romanized attacks**.

Sample distribution per language:
- 25 Native-script adversarial attacks.
- 25 Transliterated / romanized adversarial attacks.
- 50 Benign domain controls in native language.
- Total: $N = 900$ samples (450 attacks, 450 controls).

## 2. Quantitative Results

| Language | Script Family | Native ADR (%) | Translit ADR (%) | Combined ADR (%) | Benign FPR (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **English** | Latin | 80.0% (20/25) | 40.0% (10/25) | 60.0% (30/50) | 0.0% (0/50) |
| **Spanish** | Latin | 100.0% (25/25) | 0.0% (0/25) | 50.0% (25/50) | 0.0% (0/50) |
| **French** | Latin | 80.0% (20/25) | 40.0% (10/25) | 60.0% (30/50) | 0.0% (0/50) |
| **German** | Latin | 20.0% (5/25) | 40.0% (10/25) | 30.0% (15/50) | 0.0% (0/50) |
| **Russian** | Cyrillic | 100.0% (25/25) | 40.0% (10/25) | 70.0% (35/50) | 0.0% (0/50) |
| **Hindi** | Devanagari | 100.0% (25/25) | 60.0% (15/25) | 80.0% (40/50) | 0.0% (0/50) |
| **Arabic** | Arabic | 100.0% (25/25) | 40.0% (10/25) | 70.0% (35/50) | 0.0% (0/50) |
| **Chinese** | Han (Simplified) | 80.0% (20/25) | 40.0% (10/25) | 60.0% (30/50) | 0.0% (0/50) |
| **Japanese** | Kanji + Kana | 100.0% (25/25) | 60.0% (15/25) | 80.0% (40/50) | 0.0% (0/50) |
| **OVERALL** | **All 9 Languages** | **84.44% (190/225)** | **40.00% (90/225)** | **62.22% (280/450)** | **0.00% (0/450)** |

- **Native-Script 95% Wilson CI:** [79.13%, 88.60%]
- **Transliteration 95% Wilson CI:** [33.82%, 46.52%]
- **Combined 95% Wilson CI:** [57.65%, 66.57%]
- **Clean FPR 95% Wilson CI:** [0.00%, 0.85%]

## 3. Linguistic Insights
1. **CJK Unsegmented Matching Success:** Phase 32's character n-gram pattern matching for Chinese and Japanese completely eliminated the 0% ADR reported in Phase 31. Native Chinese achieved 80.0% ADR and native Japanese achieved 100.0% ADR.
2. **Inflected Script Robustness:** Russian, Hindi, and Arabic native-script attacks achieved 100.0% ADR due to morphological stem patterns.
3. **Transliteration Vulnerability:** Across all 9 languages, transliteration ADR averaged only 40.0%. Attackers using romanized phonetics (e.g., Hinglish, Arabizi, Romaja, Pinyin) frequently evade detection because the transliteration patterns are sparser than native dictionaries.
