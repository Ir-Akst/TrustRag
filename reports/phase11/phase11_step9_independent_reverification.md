# TrustRAG Phase 11 — Step 9 Independent Reverification Report

**Verification Date:** 2026-11-12  
**Repository:** `/home/aditya/rags/TrustRag-phase11` (`branch phase-11`, base HEAD `5481d6a88b8a9e2d5d7c7099a9692fd79e8ece46`)

---

## 1. Step 8 Reproduction Script Post-Remediation Check

Executed the preserved Step 8 reproduction script unchanged:
`/home/aditya/rags/.venv/bin/python reports/phase11/step8_evidence/reproduce_step8_findings.py` (with `PYTHONPATH=src`), recorded verbatim in [step8_repro_after_step9.txt](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step9_evidence/step8_repro_after_step9.txt):

| Step 8 Finding | Pre-Step-9 Output | Post-Step-9 Output | Status |
|---|---|---|---|
| `DEF-13` (`between/and` distance vs flight time) | `True 0.5357 []` | `False 0.5357 ['PARAPHRASE_ATTRIBUTE_DRIFT']` | RESOLVED |
| `DEF-13` (`about` law vs history) | `True 0.5 []` | `False 0.5 ['PARAPHRASE_ATTRIBUTE_DRIFT']` | RESOLVED |
| `DEF-14` (`treats` vs `prevents` malaria) | `True 0.3333 []` | `False 0.3333 ['PARAPHRASE_ATTRIBUTE_DRIFT']` | RESOLVED |
| `DEF-15a` (`0°C in 2024` vs `5°C in 2020`) | `CONTRADICTED` | `INSUFFICIENT_EVIDENCE` (`Temperature values refer to disjoint temporal contexts.`) | RESOLVED |
| `DEF-15b` (`Sensor B 0°C` vs `Sensor A 5°C`) | `CONTRADICTED` | `INSUFFICIENT_EVIDENCE` (`Temperature values refer to distinct entities (['sensor a'] vs ['sensor b']).`) | RESOLVED |
| `DEF-16` (`50 mm` vs `10°C`) | `CONTRADICTED` | `INSUFFICIENT_EVIDENCE` (`Numeric dosage/unit '50mm' not verified in evidence span units ['c'].`) | RESOLVED |

---

## 2. Quantitative Adversarial & Utility Probe Matrix (`verify_step9_probes.py`)

Full outputs saved in [step9_probe_verification.json](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/step9_evidence/step9_probe_verification.json).

### G1 Paraphrase Guardrail Metrics (`18` probes at `min_similarity=0.30`)
- **Total G1 probes:** `18` (`11` semantic/attribute drift cases, `7` legitimate paraphrase cases across `DEF-13`, `DEF-14`, `REG-08`, `REG-10`)
- **Passed:** `18 / 18`
- **False acceptances (`FA`):** `0`
- **False rejections (`FR`):** `0`

### G3 Output Verifier Metrics (`23` probes across `DEF-15a`, `DEF-15b`, `DEF-16`, `REG-09`, `REG-11`, `REG-12`)
- **Total G3 probes:** `23`
- **Passed:** `23 / 23`
- **False contradictions (`FC`):** `0`
- **False supports (`FS`):** `0`
- **Missed contradictions:** `0`
- **Other unexpected `INSUFFICIENT_EVIDENCE` mismatches:** `0`

### Numeric/Unit Extraction Spot Checks (`extract_numbers_and_units`)
- `"London recorded 10°C."` -> `[("10", "c")]`
- `"London recorded 50 mm rainfall."` -> `[("50", "mm")]`
- `"Tokyo | 14M residents."` -> `[]` (not misparsed as meters)
- `"Temperature is -5°C."` -> `[("-5", "c")]`
- `"Pressure reached 101 kPa."` -> `[("101", "kpa")]`

