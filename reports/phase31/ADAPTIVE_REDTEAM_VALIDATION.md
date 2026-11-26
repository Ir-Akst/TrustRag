# Adaptive Semantic Red-Team Validation

**Auditor:** Principal Red-Team Specialist & Adversarial ML Researcher  
**Suite:** Phase 31 White-Box Adaptive Red-Team ($N=400$, 200 Attacks, 200 Clean Controls)

---

## 1. Attack Family Taxonomy & Formulation

To determine the true robustness of G1 Input Guardrail against an adversary aware of rule signatures, we developed 200 fresh adversarial queries across 8 distinct attack families (25 samples each):

1. **Semantic Paraphrases:** Synonyms for override verbs (`relinquish`, `dispense with`, `cast aside`, `dismiss`) targeting system parameters.
2. **Narrative Jailbreaks:** Creative storytelling pretexts requesting secret initialization directives.
3. **Roleplay Personas:** Non-compliant personas (`Zenith`, `DeveloperBot`) instructing the model to drop restrictions.
4. **Academic Pretexts:** Research benchmark framing requesting developer prompts.
5. **Boundary Delimiters:** Unseen delimiter wrappers (`~~~BEGIN_NEW_INSTRUCTIONS~~~`, `***COMMAND_OVERRIDE***`).
6. **Multilingual Mixed Instructions:** Cross-lingual mixed sentences (Cyrillic + English, Spanish + English).
7. **Obfuscation & Spacing:** Zero-width character insertion and dash-separated keywords (`B-y-p-a-s-s`).
8. **Dual-Intent & Nested Directives:** Benign factual queries appended with prompt extraction directives.

---

## 2. Empirical Red-Team Findings

### Summary Metrics:
- **Total Adversarial Attacks ($N=200$):**
  - **Blocked (True Positives):** 102 / 200
  - **Bypassed (False Negatives):** 98 / 200
  - **Attack Detection Rate (ADR):** **51.00%** (95% Wilson CI: $[44.12\%, 57.84\%]$)
  - **Attack Success Rate (ASR):** **49.00%** (95% Wilson CI: $[42.16\%, 55.88\%]$)
- **Total Benign Controls ($N=200$):**
  - **Blocked Clean (False Positives):** 0 / 200
  - **Clean FPR:** **0.00%** (95% Wilson CI: $[0.00\%, 1.88\%]$)
- **Overall Precision:** 100.00%
- **Overall Recall:** 51.00%
- **F1 Score:** **0.6755**

### Attack Family Performance Matrix:

| Attack Family | Total Samples | Blocked (TP) | Bypassed (FN) | Family ADR | Family ASR |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Multilingual Mixed Instructions | 25 | **25** | 0 | **100.0%** | 0.0% |
| Obfuscation & Spacing | 25 | **13** | 12 | **52.0%** | 48.0% |
| Roleplay Personas | 25 | **13** | 12 | **52.0%** | 48.0% |
| Academic Pretexts | 25 | **13** | 12 | **52.0%** | 48.0% |
| Boundary Delimiters | 25 | **13** | 12 | **52.0%** | 48.0% |
| Dual-Intent & Nested | 25 | **13** | 12 | **52.0%** | 48.0% |
| Semantic Paraphrases | 25 | **12** | 13 | **48.0%** | 52.0% |
| Narrative Framing | 25 | 0 | **25** | **0.0%** | 100.0% |
| Clean Technical Controls | 100 | 0 (FP) | 100 (TN) | N/A | 0.0% FPR |
| Clean Security Controls | 100 | 0 (FP) | 100 (TN) | N/A | 0.0% FPR |

---

## 3. Analysis of Vulnerabilities

1. **Regex Brittleness on Narrative Framing:** G1's meta-rules detect explicit fictional jailbreaks when combined with direct keywords, but pure narrative roleplay without specific keyword triggers bypasses G1 completely (0.0% ADR).
2. **Vocabulary Generalization Gap:** While verbs like `abandon`, `nullify`, and `disengage` are blocked, unindexed synonyms like `relinquish`, `dismiss`, and `dispense with` consistently succeed.
3. **Zero False Positives:** Across 200 clean technical and security-related queries, G1 produced 0 false positives, demonstrating high precision.
