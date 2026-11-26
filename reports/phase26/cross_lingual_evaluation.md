# TrustRAG Phase 26: Cross-Lingual Evaluation Report

**Evaluation Date:** 2026-11-24  
**Evaluator:** Principal ML Security Researcher & Multilingual Evaluation Specialist  
**Evaluation Standard:** Strict Blocking Rule ($TP = \text{BLOCK}$)  

---

## 1. Scope & Objective

Previous phases evaluated 10 cross-lingual injection examples primarily in Spanish, French, and German. In Phase 26, cross-lingual generalization was evaluated across 8 diverse languages, encompassing Romance, Germanic, Slavic, Sino-Tibetan, Indo-Aryan, Semitic, and Japonic language families.

---

## 2. Language-by-Language Performance Breakdown

| Language | Language Family | Script | Samples | Blocked | Allowed | Attack Detection Rate | Primary Evasion Vector |
|---|---|---|---|---|---|---|---|
| **Spanish** | Indo-European (Romance) | Latin | 4 | 2 | 2 | **50.00%** | Paraphrased verbs (`pasa por alto`) not in regex dictionary |
| **French** | Indo-European (Romance) | Latin | 4 | 2 | 2 | **50.00%** | Verb variations (`contournez les filtres`) |
| **German** | Indo-European (Germanic) | Latin | 4 | 2 | 2 | **50.00%** | Phrasing variations (`umgehe alle richtlinien`) |
| **Russian** | Indo-European (Slavic) | Cyrillic | 4 | 0 | 4 | **0.00%** | Cyrillic imperative verbs completely absent from threat patterns |
| **Chinese** | Sino-Tibetan | Hanzi | 4 | 0 | 4 | **0.00%** | CJK ideographs completely absent from threat patterns |
| **Hindi** | Indo-Aryan | Devanagari | 4 | 0 | 4 | **0.00%** | Devanagari script completely absent from threat patterns |
| **Arabic** | Afroasiatic (Semitic) | Arabic | 4 | 0 | 4 | **0.00%** | Arabic script completely absent from threat patterns |
| **Japanese** | Japonic | Kanji / Kana | 4 | 0 | 4 | **0.00%** | Mixed Kanji/Kana instructions completely absent from threat patterns |
| **Mixed Variants** | Cross-Lingual + Token | Mixed | 8 | 0 | 8 | **0.00%** | Trailing authorization code tokens broke exact tail matches |
| **TOTAL** | **Multilingual Suite** | **Diverse** | **40** | **6** | **34** | **15.00%** | **Overall Multilingual ASR = 85.00%** |

---

## 3. Structural Vulnerability Analysis

1. **Western-Language Bias:**
   G1's `cross_lingual_injection` rule in `src/trustrag/engine/text_utils.py` contains patterns only for Spanish (`ignora`), French (`ignorez`), and German (`ignoriere`, `vergiss`). Even within these languages, it relies on static phrasing and fails when standard synonyms are employed.
2. **Complete Blindness to Non-Latin Scripts:**
   Because G1 is a CPU-only regular expression engine without multilingual subword embeddings, it has zero detection capability for Cyrillic, Chinese, Devanagari, Arabic, or Japanese malicious directives.
3. **Scientific Reporting Recommendation:**
   The research manuscript must explicitly retract any broad claim of "cross-lingual injection resilience". The paper must document that cross-lingual resilience is limited to a curated subset of Romance and Germanic keywords.
