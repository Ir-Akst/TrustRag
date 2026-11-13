# TrustRAG Phase 11 — Step 12 Residual Risks and Nuances

**Audit Role:** Independent Final Acceptance Auditor  
**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**Base HEAD:** `8229aee01a0b6f7fd61a5e774da5bb707bd6a7c1`  
**Execution Timestamp:** 2026-11-12T19:52:49Z  

---

## 1. Executive Risk Summary

Step 12 independent auditing confirmed that all high-priority defect vulnerabilities (`DEF-17`, `DEF-18`, `DEF-19`) have been remediated with zero regressions to historical defect fixes (`DEF-01` through `DEF-16`). No high-severity exploits or uncontained vulnerabilities remain. However, the following residual risks, architectural boundaries, and operational nuances are documented for Phase 13 planning.

---

## 2. Identified Residual Risks & Operational Nuances

### Risk 1: Offline Network Boundary for Hugging Face Hub Acquisition Tests
- **Severity:** Informational / Environmental
- **Impact:** 2 integration tests (`test_boolq_sample_acquisition`, `test_squad_sample_acquisition`) cannot execute in the hermetic sandbox.
- **Current Mitigation:** Deselected via `addopts = "-m 'not integration'"` in `pytest.ini`.
- **Audit Verdict:** Strictly classified as **`BLOCKED`**, never as `PASS`. Unit tests and mock-based acquisition suites continue to pass at 100%.
- **Action for Future Phases:** When network access is granted in production CI/CD, run integration tests against Hugging Face Hub mirrors or cached fixtures.

### Risk 2: Neural Model Dependencies & FilterRAG SLM Fallback
- **Severity:** Low / Architectural
- **Impact:** Neural rerankers and SLM filter models require GPU acceleration and heavy dependencies (`torch`, `transformers`) not loaded in this environment.
- **Current Mitigation:** The system employs deterministic, rule-based fallback components across G1, G2, and G3.
- **Audit Verdict:** The fallback mechanisms operate deterministically, safely, and with high throughput (>200 claims/sec in G3, <5ms in G2). No external neural research parity is claimed.

### Risk 3: Directional Named Entity Extraction Asymmetry in Currency Comparisons (`DEF-17`)
- **Severity:** Low / Edge-Case Limitation
- **Mechanism:**  
  - When a claim uses currency symbols (`Price was $250.`) and evidence uses ISO codes (`Price was 250 USD.`), the numerical currency extractor correctly maps both to `{'amount': 250.0, 'currency': 'usd'}` and returns **`SUPPORTED`**.
  - Conversely, when the claim uses uppercase 3-letter ISO codes (`Price was 250 USD.`) and evidence uses symbols (`Price was $250.`), `_extract_proper_entities()` in `output_verifier.py` treats `USD` as a required named entity token (alongside proper nouns like `IBM` or `NASA`) because `USD/EUR/GBP/JPY` are not listed in `_NON_ENTITY_TEMP_SCALE_WORDS`. Because the evidence text contains only the `$` symbol and not the literal token `usd`, `missing_entities = ['usd']`, resulting in a safe verdict of **`INSUFFICIENT_EVIDENCE`**.
- **Audit Safety Assessment:**  
  This asymmetry is **fail-safe**: it never produces False Support (`SUPPORTED`) or False Contradiction (`CONTRADICTED`). It strictly fails to `INSUFFICIENT_EVIDENCE`.
- **Recommended Remediation in Phase 13:** Add ISO currency codes (`usd`, `eur`, `gbp`, `jpy`) to `_NON_ENTITY_TEMP_SCALE_WORDS` or treat ISO codes as currency attributes rather than proper entity constraints.

### Risk 4: Single-Candidate Retrieval Pool ($N=1$) MSD Boundary Behavior (`DEF-18`)
- **Severity:** Low / Boundary Condition
- **Mechanism:**  
  In `MultiSignalDetector` (`src/trustrag/detection/msd.py`), Signal F5 (`consensus_deviation`) is evaluated only when the candidate document pool has at least 2 non-empty documents (`len(non_empty_indices) >= 2`). When a retrieval pool contains exactly 1 document ($N=1$) from an untrusted source with benign content (F4=1.0) and high query relevance (F3=0.80), F5 remains `UNAVAILABLE` (`None`). Consequently, the untrusted consensus flags (`UNTRUSTED_NO_CONSENSUS`) are not generated, allowing the single document's trust score to reach ~0.80 and classify as `CLEAN`.
- **Audit Safety Assessment:**  
  In multi-document retrieval pools ($N \ge 2$), F5 is evaluated, generates `UNTRUSTED_NO_CONSENSUS`, and strictly prevents `CLEAN` classification. For $N=1$, untrusted sources cannot participate in a consensus attack because there is no consensus to manufacture.
- **Recommended Remediation in Phase 13:** If an untrusted source with $N=1$ should never achieve `CLEAN`, enforce a global ceiling on untrusted document trust scores regardless of F5 availability.

### Risk 5: Uncommitted Working Tree State
- **Severity:** Medium / Governance
- **Impact:** Step 11 remediation code exists in working tree files (`+258 / -25` lines across 6 files and 1 test file) on branch `phase-11`.
- **Audit Requirement:** The auditor was explicitly not authorized to commit, push, merge, create a PR, or deploy.
- **Action for Phase 13:** Authorized release engineering must commit the Step 11 modifications, tag the release commit, and merge to `main`.

### Risk 6: Static Typing Symbol Definition in `text_utils.py`
- **Severity:** Low / Code Quality
- **Impact:** In `src/trustrag/engine/text_utils.py:53-54`, `Dict` is used in annotations without being imported from `typing`.
- **Runtime Behavior:** Because `from __future__ import annotations` is imported, Python postpones evaluation of annotations at runtime, allowing all runtime code and tests to execute with zero errors. However, static type checker `mypy` flags `Name "Dict" is not defined`.
- **Action for Phase 13:** Import `Dict` from `typing` or replace `Dict[str, str]` with builtin `dict[str, str]`.

---

## 3. Residual Risk Matrix

| Risk ID | Component | Severity | Exploitable? | Fail-Safe Behavior | Recommended Action |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **RR-01** | Data Acquisition | Low | No | Tests deselected; recorded as `BLOCKED` | Run in online environment |
| **RR-02** | Reranker / Filter | Low | No | Deterministic rules active | No neural parity claimed |
| **RR-03** | Currency / Entity Slot | Low | No | Returns `INSUFFICIENT_EVIDENCE` | Add ISO codes to non-entity word list |
| **RR-04** | MSD $N=1$ Pool | Low | No | $N \ge 2$ properly guarded | Enforce untrusted score cap for $N=1$ |
| **RR-05** | Git Working Tree | Medium | No | Uncommitted working tree | Commit in authorized release step |
| **RR-06** | Type Annotations | Low | No | Python deferred annotations | Replace `Dict` with `dict` |

