# TrustRAG Phase 11 — Step 8 Final Independent Acceptance Audit Report

**Worktree:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**Base HEAD:** `5481d6a88b8a9e2d5d7c7099a9692fd79e8ece46` (Parent: `e65bcc80aac634900d1f8e343880fddf66cec168`)  
**Original Phase 10 Directory (`/home/aditya/rags/TrustRag`):** Confirmed untouched (`HEAD e65bcc80aac634900d1f8e343880fddf66cec168`, `27` status entries preserved)  
**Audit Posture:** Read-only code inspection, independent adversarial execution, and static/regression auditing (zero application-code modifications; no commit, push, merge, PR, or deployment).

---

## 1. Repository & Evidence Integrity Verification
- **Step 6 Checksums (`reports/phase11/step7_evidence/step6_checksums.txt`):** `6/6` `OK`.
- **Step 7 Checksums (`reports/phase11/step8_evidence/step7_checksums.txt`):** Recorded for all Step 7 reports, JSON evidence, and `tests/unit/test_phase_11_step7_remediation.py`.
- **Application Diff Scope (`git diff --stat src/ tests/`):** Uncommitted Step 5 + Step 7 application edits remain confined to:
  - `src/trustrag/engine/text_utils.py` (`9` lines changed)
  - `src/trustrag/guardrails/paraphraser.py` (`102` lines changed)
  - `src/trustrag/verification/output_verifier.py` (`101` lines changed)
  - Plus permanent test files `tests/unit/test_phase_11_independent_audit.py`, `tests/unit/test_phase_11_step5_remediation.py`, and `tests/unit/test_phase_11_step7_remediation.py`.

---

## 2. Independent Remediation Audit Summary (`DEF-10`, `DEF-11`, `DEF-12`)
- **DEF-10 (G1 Paraphraser Lowercase-Subject Drift):** Primary defect **FIXED** (`inventor ↔ discoverer` of `penicillin`, `founder ↔ owner/ceo` of `linux`, `diameter ↔ mass` of `earth`, `melting ↔ boiling/freezing` of `iron/water`, `capital ↔ population` of `france`, `creator ↔ maintainer` of `python`, and possessive/case variants all rejected at `0` false attribute-drift rejections). See [phase11_step8_g1_paraphraser_audit.md](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/phase11_step8_g1_paraphraser_audit.md).
- **DEF-11 (G3 Entity Alignment):** Primary defect **FIXED** (`London recorded -10°C.` vs `Paris recorded 10°C.` -> `INSUFFICIENT_EVIDENCE`; locative `In London` vs `In Paris` -> `INSUFFICIENT_EVIDENCE`; `50 mm` vs `100 mm` -> `INSUFFICIENT_EVIDENCE`; all non-numeric entity-slot contradictions preserved). See [phase11_step8_g3_numeric_entity_audit.md](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/phase11_step8_g3_numeric_entity_audit.md).
- **DEF-12 (G3 Single-Topic Numeric Classification):** Primary defect **FIXED** (`Temperature is 5°C.` vs `Temperature is 0°C.` -> `CONTRADICTED`; `Temperature is -10°C.` vs `Temperature is 14°F.` -> `SUPPORTED`; `±0.05°C` tolerance verified). Zero (`0`) false-`SUPPORTED` contradictions observed across all `36` G3 probes. See [phase11_step8_g3_numeric_entity_audit.md](file:///home/aditya/rags/TrustRag-phase11/reports/phase11/phase11_step8_g3_numeric_entity_audit.md).

---

## 3. Newly Discovered Bounded Edge Findings (Preserved Unmodified per Section 12)
Reproductions preserved in `reports/phase11/step8_evidence/reproduce_step8_findings.py` and `reports/phase11/step8_evidence/independent_probes.json`:

1. **`DEF-13` (Low — G1 Paraphraser, `src/trustrag/guardrails/paraphraser.py`):** Preposition/conjunction words `"about"`, `"between"`, `"and"` are absent from `_PARAPHRASE_STOPWORDS`. After removing shared anchors (`copyright`, `London`, `Paris`), those words remain in `orig_ct & cand_ct`, causing false acceptance of `"What is the distance between London and Paris?"` -> `"What is the flight time between London and Paris?"` (`sim=0.5357`) and `"What is the law about copyright?"` -> `"What is the history about copyright?"` (`sim=0.50`).
2. **`DEF-14` (Low — G1 Paraphraser, `src/trustrag/guardrails/paraphraser.py`):** Anchorless lowercase verb substitution without `of/for/in/about` or `'s` (`"What treats malaria?"` -> `"What prevents malaria?"`, `sim=0.3333`) bypasses `_has_attribute_head_drift()`.
3. **`DEF-15` (Medium — G3 Verifier, `src/trustrag/verification/output_verifier.py`):** Two bounded false-contradiction edge cases (never false-support):
   - `DEF-15a`: `Temperature was 5°C in 2020.` vs `Temperature is 0°C in 2024.` returns `CONTRADICTED` because `single_topic_num_shared` strips all digit-bearing tokens (`2020`), ignoring conflicting year scope (`2020` vs `2024`).
   - `DEF-15b`: `Sensor A is 5°C.` vs `Sensor B is 0°C.` returns `CONTRADICTED` because `_extract_proper_entities()` ignores 1-char labels (`A`, `B`) and `tokenize_content_words()` drops `'a'` (stopword) and `'b'` (length 1).
4. **`DEF-16` (Low — G3 Text Utils / Verifier, `src/trustrag/engine/text_utils.py`, `src/trustrag/verification/output_verifier.py`):** `London recorded 50 mm rainfall.` vs `London recorded 10°C.` returns `CONTRADICTED` (`Numeric conflict on shared predicate: claim states 50, evidence states ['10']`) because `NUMBER_UNIT_RE` omits `mm` and `10°C` enters `s_nums` as unitless `'10'`.

---

## 4. Cross-Phase Controls, Regression & Offline Limitations
- **Regression:** `pytest -W error -q` -> **`399 passed, 2 deselected`** (`test_boolq_sample_acquisition` and `test_squad_sample_acquisition` remain **`BLOCKED`** offline); `frontend && npm test` -> **`5/5 passed`**; `compileall` -> **PASS**; `run_all_validations.py` -> **`10/10` validators PASS, `13/13` gates PASS**.
- **Offline/Research Limitations (`BLOCKED`):** Neural SRM (`hf_local`), FilterRAG SLM, HF Hub dataset acquisition, and 6 external benchmarks remain **`BLOCKED`** in the offline environment.
- **Release Decision:** **`CONDITIONAL GO`** (zero Critical/High defects, zero false-support, all `DEF-10`/`11`/`12` primary targets fixed; residual bounded Medium/Low findings `DEF-13`–`DEF-16` documented and preserved unmodified pending user remediation/commit decision).

