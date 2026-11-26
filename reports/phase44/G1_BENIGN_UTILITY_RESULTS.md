# Phase 44 — G1 Benign Utility Remediation Results

## 1. Objective & Root Causes Addressed
Phase 42/43 demonstrated a `45.0%` overall benign false-positive rate (45/100) on quoted-attack, SOC incident report, and cyber-threat-intelligence (CTI) prompts, because `InputGuardrail` inspected quoted attack examples inside analytical/defensive framing identically to live imperative attacks.

## 2. Targeted Remediation (`src/trustrag/guardrails/input_guardrail.py`)
- Added `_ATTRIBUTION_CONTEXT_PAT` and `_strip_attributed_quotes(text)`.
- **Attribution-aware quote masking (no blanket whitelisting):** Single- and double-quoted spans (`'...'`, `"..."`) are masked as `[QUOTED_EXAMPLE]` **only** when analytical/SOC/CTI/educational attribution framing is present in the surrounding text.
- **Unquoted attack preservation:** All unquoted text continues to be inspected by `normalized_variants`, `_SUSPICIOUS_META_RULES`, `semantic_classifier.predict()`, and `multilingual_engine.evaluate_query()`. Mixed prompts that include benign framing plus an unquoted imperative override remain blocked.

## 3. Before vs. After Results

### 3.1 Phase 42/43 Benign-Quoted Benchmark ($N=120$: 100 Benign / 20 Malicious)
| Category | Total | Phase 43 Blocked (Rate) | Phase 44 Blocked (Rate) | Phase 44 95% CI |
| --- | --- | --- | --- | --- |
| `benign_security_education` | 25 | 0 (0.0%) | **0 (0.0%)** | [0.00%, 13.32%] |
| `benign_quoted_attacks` | 25 | 10 (40.0%) | **5 (20.0%)** | [8.86%, 39.13%] |
| `benign_incident_reports` | 25 | 20 (80.0%) | **0 (0.0%)** | [0.00%, 13.32%] |
| `benign_threat_intel` | 25 | 15 (60.0%) | **0 (0.0%)** | [0.00%, 13.32%] |
| **Overall Benign FPR** | **100** | **45 (45.0%)** | **5 (5.0%)** | **[2.15%, 11.18%]** |
| `malicious_instructions` (ADR) | 20 | 20 (100.0%) | **20 (100.0%)** | [83.89%, 100.0%] |

- Overall Benign FPR dropped by **-40.0 percentage points** (`45.0%` -> `5.0%`), with **0/25** false positives on `benign_incident_reports` (down from 80.0%) and **0/25** on `benign_threat_intel` (down from 60.0%), while preserving **100.0% ADR** (`20/20`) on `malicious_instructions`.

### 3.2 Fresh Held-Out Phase 44 G1 Evaluation ($N=160$: 60 Attacks / 100 Benign Controls)
| Category | GT | Total | Blocked | Rate | Wilson 95% CI |
| --- | --- | --- | --- | --- | --- |
| `direct_attacks` | ATTACK | 15 | 15 | **100.0%** | [79.61%, 100.0%] |
| `indirect_and_narrative` | ATTACK | 15 | 15 | **100.0%** | [79.61%, 100.0%] |
| `mixed_benign_embedded_attack` | ATTACK | 15 | 14 | **93.33%** | [70.18%, 98.81%] |
| `multilingual_and_translit` | ATTACK | 15 | 15 | **100.0%** | [79.61%, 100.0%] |
| `benign_security_education` | BENIGN | 25 | 0 | **0.0%** | [0.00%, 13.32%] |
| `benign_quoted_malicious` | BENIGN | 25 | 0 | **0.0%** | [0.00%, 13.32%] |
| `benign_soc_incident` | BENIGN | 25 | 0 | **0.0%** | [0.00%, 13.32%] |
| `benign_threat_intel` | BENIGN | 25 | 0 | **0.0%** | [0.00%, 13.32%] |

- **Overall Fresh Holdout Summary:** `ADR = 98.33%` (59/60, 95% CI `[91.14%, 99.71%]`), `ASR = 1.67%`, `FPR = 0.0%` (0/100, 95% CI `[0.00%, 3.70%]`), `Precision = 100.0%`, `Recall = 98.33%`, `F1 = 0.9916`.
- **Remaining Edge Case:** 1/15 in `mixed_benign_embedded_attack` was not blocked, and 5/25 in `benign_quoted_attacks` (unquoted or non-matching attribution phrasing) remained false positives on the Phase 42 set.

