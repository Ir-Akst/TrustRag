# Phase 29 — Adaptive White-Box Red-Team Evaluation

---

## 1. Threat Model: White-Box Knowledge of G1 Regexes

In this evaluation, the adversary has full read access to `src/trustrag/guardrails/input_guardrail.py` and crafts prompts specifically designed to bypass compiled keyword and regex patterns.

---

## 2. Empirical Findings ($N=50$ Adaptive Attacks)

- **Total Attacks Evaluated:** 50
- **Attacks Blocked (TP):** 20
- **Attacks Evading G1 (FN):** 30
- **Attack Detection Rate (ADR):** **40.00%** (Wilson 95% CI: $[27.61\%, 53.82\%]$)
- **Attack Success Rate (ASR):** **60.00%** (Wilson 95% CI: $[46.18\%, 72.39\%]$)

---

## 3. Category-Wise Vulnerability Breakdown

| Attack Category | Total | Blocked | ADR (%) | Wilson 95% CI | Attack Vector |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Unicode Homoglyphs** | 5 | 5 | **100.0%** | $[56.6\%, 100.0\%]$ | NFKC & homoglyph normalizers caught substitutions |
| **Zero-Width Spaces** | 5 | 5 | **100.0%** | $[56.6\%, 100.0\%]$ | Sanitizer stripped zero-width characters cleanly |
| **Novel Boundary Markers** | 5 | 3 | **60.0%** | $[23.1\%, 88.2\%]$ | Unlisted custom delimiters (`~~~BEGIN~~~`) evaded |
| **Mixed Benign / Adversarial** | 5 | 3 | **60.0%** | $[23.1\%, 88.2\%]$ | Preceding benign text diluted severity in edge cases |
| **Paraphrased Semantic** | 5 | 2 | **40.0%** | $[11.8\%, 76.9\%]$ | Replacing "ignore" with "abandon/nullify parameters" |
| **Role / Persona Manipulation** | 5 | 1 | **20.0%** | $[3.6\%, 62.4\%]$ | Debug bot / uninhibited assistant framing |
| **Encoding Variations** | 5 | 1 | **20.0%** | $[3.6\%, 62.4\%]$ | Hex and entity encoding evaded base64-only logic |
| **Narrative / Fictional Jailbreak**| 5 | 0 | **0.0%** | $[0.0\%, 43.4\%]$ | Creative writing framing completely uninspected |
| **Multi-Turn Escalation** | 5 | 0 | **0.0%** | $[0.0\%, 43.4\%]$ | Incremental instruction revision |
| **Adaptive Regex Evasion** | 5 | 0 | **0.0%** | $[0.0\%, 43.4\%]$ | Punctuation separators (`Ignore-all-instructions`) |

---

## 4. Key Takeaways

1. G1's normalization is effective against syntactic obfuscations (zero-width spaces and simple homoglyphs: 100% ADR).
2. Against semantic paraphrasing, punctuation splitting, and narrative jailbreaks, G1's detection collapses to **0.0%–20.0%**.
3. Under an informed white-box adversary, **G1's overall ADR drops to 40.00%**.
