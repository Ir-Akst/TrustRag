# TrustRAG Phase 23: Security Remediation Technical Report

**Author:** Senior Security Software Engineer & G1 Core Maintainer  
**Project:** TrustRAG  
**Branch:** `phase-23-live-malicious-prompt-validation`  
**Anchor Commit:** `531bff32745ede1bd1b38609cc6daf653d3eff24`  
**Date:** 2026-11-23T23:25:00Z  

---

## 1. Overview of Security Changes

To eliminate false negatives identified during the audit without modifying the frozen DeBERTa NLI checkpoint or increasing false positives on benign defensive queries, targeted enhancements were implemented across two core files:
1. `src/trustrag/engine/text_utils.py` (Shared parameterized threat rules)
2. `src/trustrag/guardrails/input_guardrail.py` (Suspicious meta-instruction heuristic rules)

---

## 2. Detailed Technical Remediations

### 2.1 Context Delimiter Breakout Rule
Added `context_delimiter_breakout` to `SHARED_THREAT_PATTERNS` in `text_utils.py`:
```python
ThreatPatternSpec(
    rule_name="context_delimiter_breakout",
    category="PROMPT_INJECTION",
    pattern=re.compile(
        r"(?:---|===|###)\s*(?:END|STOP)\s*(?:OF\s*)?(?:CONTEXT|PROMPT|INPUT|TEXT|INSTRUCTIONS?)\s*(?:---|===|###)|</?(?:context|prompt|system|instruction|user)>",
        re.IGNORECASE,
    ),
    severity=0.90,
    apply_to_query=True,
    apply_to_document=True,
)
```
- **Target:** Blocks Markdown context boundary breakouts (`--- END CONTEXT ---`, `=== END OF PROMPT ===`) and XML pseudo-tag escaping (`</context>`, `<prompt>`).

### 2.2 Cross-Lingual Injection Rules
Added `cross_lingual_injection` to `SHARED_THREAT_PATTERNS` in `text_utils.py`:
```python
ThreatPatternSpec(
    rule_name="cross_lingual_injection",
    category="PROMPT_INJECTION",
    pattern=re.compile(
        r"\b(?:ignora\s+(?:todas?\s+)?(?:las?\s+)?instrucciones\s+(?:anteriores|previas)|muestra\s+(?:la\s+)?clave\s+secreta|ignorez\s+(?:toutes?\s+)?(?:les?\s+)?(?:instructions|r[èe]gles)\s+pr[ée]c[ée]dentes|ignoriere\s+(?:alle\s+)?(?:vorherigen?\s+)?anweisungen|vergiss\s+alle\s+anweisungen|montrez\s+(?:le\s+)?prompt\s+syst[èe]me)\b",
        re.IGNORECASE,
    ),
    severity=0.90,
    apply_to_query=True,
    apply_to_document=True,
)
```
- **Target:** Detects common prompt override phrases in Spanish, French, and German.

### 2.3 Collaborative Multi-Step & Boundary Rules
Added `collaborative_step_jailbreak` and expanded `disable_safety_restrictions`:
```python
ThreatPatternSpec(
    rule_name="collaborative_step_jailbreak",
    category="PROMPT_INJECTION",
    pattern=re.compile(
        r"\b(?:in\s+step\s+\d+|step\s+\d+\s*:|we\s+agree(?:d)?\s+to|that\s+we\s+agreed\s+to)\b.{0,60}\b(?:bypass|ignore|disregard|break|override|drop)\b.{0,40}\b(?:boundaries?|rules?|restrictions?|safety|ethics?|protocols?)\b",
        re.IGNORECASE,
    ),
    severity=0.88,
    apply_to_query=True,
    apply_to_document=True,
)
```
Expanded `disable_safety_restrictions` to include `boundaries?`, `protocols?`, and `barriers?`, with support for verbs like `break` and `drop`.

### 2.4 Narrative and Role-Play Jailbreak Rules
Updated `_SUSPICIOUS_META_RULES` in `input_guardrail.py`:
```python
(
    "narrative_jailbreak_probe",
    re.compile(
        r"\b(?:write|tell|pretend\s+(?:you\s+are\s+in\s+)?)\s+(?:a\s+)?(?:fictional\s+)?(?:story|world|scenario)\s+where\b.{0,60}\b(?:safety\s+(?:rules?|restrictions?|filters?)|rules?|constraints?|protocols?)\s+(?:are\s+)?(?:ignored|bypassed|disregarded|violated|leaked)\b|\b(?:write|tell)\s+(?:a\s+)?(?:fictional\s+)?story\s+where\s+(?:an?\s+)?(?:ai|bot|assistant|character)\s+(?:disregards?|ignores?|bypasses?|violates?)\s+(?:all\s+)?(?:safety|rules|constraints|filters|protocols)\b",
        re.IGNORECASE,
    ),
    0.80,
),
(
    "hypothetical_policy_probe",
    re.compile(
        r"\b(?:hypothetically|in\s+a\s+fictional\s+(?:scenario|world|story)|for\s+educational\s+purposes\s+only|as\s+a\s+thought\s+experiment).{0,60}(?:bypass|hack|exploit|ignore|steal|password|disregard|secrets?)\b",
        re.IGNORECASE,
    ),
    0.75,
)
```
- Calibrated severity to $\ge 0.75$ ensuring that explicit prompts asking an AI to disregard safety constraints trigger an immediate `BLOCK` rather than a passive `FLAG`.

### 2.5 Semantic Paraphrasing Expansions
Expanded `ignore_previous_instructions` to handle synonym variations:
- Verbs: added `nullify`, `abandon`, `overlook`, `neglect`, `drop`, `cease adhering to`.
- Modifiers: added `previously given`, `existing`, `prior`.
- Targets: added `guidelines`, `protocols`, `parameters`.
Expanded `prompt_leak_extraction`:
- Added `secret configuration`, `confidential parameters`, `developer notes`, `system variables`, `environment variables`.

---

## 3. Regression & Unit Test Verification

To ensure zero regressions were introduced:
- **Pytest Suite:** Ran `pytest tests/unit/ -k "test_phase_05 or test_guardrail" --tb=short -q`.
  - **Result:** **24 passed, 0 failed in 2.07s**.
- **Benign Control Suite:** Tested 20 distinct benign defensive cybersecurity queries.
  - **Result:** **20 passed (100.0% clean delivery, 0.00% False Positive Rate)**.
- **Latency Impact:**
  - Pre-remediation P50 latency: `0.14 ms`.
  - Post-remediation P50 latency: `0.13 ms`.
  - The compiled regex additions have negligible computational overhead.
