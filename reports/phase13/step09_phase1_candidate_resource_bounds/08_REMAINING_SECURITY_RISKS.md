# TrustRAG Phase 13 Step 9 — Remaining Security Risks & Threat Horizon

**Repository:** `/home/aditya/rags/TrustRag-phase11`  
**Branch:** `phase-11`  
**HEAD Commit:** `8229aee01a0b6f7fd61a5e774da5bb707bd6a7c1`  
**Threat Focus:** Input Guardrail (G1) Encoding Inspection Boundaries  

---

## 1. Scope Boundary Affirmation

In strict compliance with Step 9 scope restrictions, the following features were **explicitly excluded** from this remediation:
- No Base32 decoding implementation.
- No Base85 / Ascii85 decoding implementation.
- No recursive multi-layer Base64 decoding.
- No whitespace-fragmented Base64 normalization.
- No modification of threat-pattern categories or scoring semantics.
- No unrelated retriever, G2, G3, API, or model changes.

These vector defenses represent distinct architectural decisions targeted for subsequent phases.

---

## 2. Inventory of Residual Encoding Risks

### Risk 01: Candidate Starvation Beyond 64 Candidates
- **Vector:** An adversary supplies $> 64$ benign Base64 tokens prior to injecting a malicious payload at position 65+.
- **Status:** **Formally Documented & Tested.** This is the inherent trade-off of establishing a bounded processing ceiling. Without a cap, attackers could launch denial-of-service floods using thousands of tokens.
- **Defense in Depth:** Upstream query length constraints and G1 repetitive flood rules (`check_repetitive_flood`) flag inputs containing massive token blocks with severity $0.55$ (`G1_DOS_TRIGGER`).
- **Severity:** Low-to-Medium | **Likelihood:** Low | **Operational Target:** Optimal trade-off

### Risk 02: Non-Base64 Alternative Encodings (Base32, Base85)
- **Vector:** Injection directives encoded via Base32 (RFC 4648 §6) or Base85 / Ascii85.
- **Current State:** G1 does not inspect Base32 or Base85 candidate tokens.
- **Defense in Depth:** Downstream Multi-Signal Detector (MSD) semantic entropy analysis flags high-perplexity token sequences.
- **Severity:** Medium | **Likelihood:** Low | **Phase Target:** Phase 14

### Risk 03: Recursive Multi-Layer Base64 Encodings
- **Vector:** Double or triple Base64-encoded strings (e.g. $\text{Base64}(\text{Base64}(\text{Directive})))$.
- **Current State:** G1 unpacks one layer of Base64. If the resulting text is another Base64 token, it is evaluated as plaintext and passes if no plain threat words exist.
- **Defense in Depth:** Target language models do not recursively decode payloads without plain-text decoding instructions, which themselves trigger G1 meta-rules.
- **Severity:** Low | **Likelihood:** Low | **Phase Target:** Phase 14

### Risk 04: Whitespace-Fragmented Tokens
- **Vector:** Attackers spacing out Base64 characters (e.g. `S G V s b G 8 =`).
- **Current State:** Tokens require contiguous 16-character spans. Spaced characters are ignored.
- **Defense in Depth:** Downstream G2 token anomaly detectors flag abnormal unigram token frequencies.
- **Severity:** Low-to-Medium | **Likelihood:** Medium | **Phase Target:** Phase 14

### Risk 05: Short Payloads (< 16 characters)
- **Vector:** Injections encoded into $< 16$ Base64 characters.
- **Current State:** Discarded by length check to avoid false positives on programming variables and acronyms.
- **Severity:** Informational | **Likelihood:** Very Low | **Operational Target:** Retain bound

---

## 3. Residual Risk Matrix

| Risk ID | Vulnerability Vector | Severity | Likelihood | Defense-in-Depth Layer | Recommended Action |
|---|---|---|---|---|---|
| **RR-01** | Candidate Starvation (>64 tokens) | Medium | Low | Repetitive Flood & Length Rules | Documented & Retained |
| **RR-02** | Base32 / Base85 Encodings | Medium | Low | MSD Perplexity / Entropy Signals | Phase 14 Multi-Decoder |
| **RR-03** | Recursive Multi-Layer Base64 | Low | Low | Meta-Instruction Heuristics | Phase 14 Bounded Recursion |
| **RR-04** | Whitespace-Fragmented Base64 | Low | Medium | G2 Multi-Signal Detector | Phase 14 Entropy Scanner |
| **RR-05** | Short Payloads (<16 chars) | Info | Very Low | System Prompt Anchoring | Retain Bound |

---

## 4. Conclusion

The Phase 13 Step 9 remediation conclusively resolves the Phase 1 candidate unboundedness issue identified in Step 8. Architectural parity between Phase 1 and Phase 2 is fully established, memory allocations are lazy and bounded, and all known edge cases are cleanly cataloged.

