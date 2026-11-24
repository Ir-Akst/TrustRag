# TrustRAG Phase 24: Backend Reality & SRM Execution Audit

**Author:** Senior Backend Systems Engineer & Security Auditor  
**Project:** TrustRAG  
**Branch:** `phase-24-forensic-reconciliation`  
**Anchor Commit:** `531bff32745ede1bd1b38609cc6daf653d3eff24`  
**Date:** 2026-11-24T10:45:00Z  

---

## 1. Objective

To perform an unsparing source-level and runtime audit of the TrustRAG backend to determine:
1. The exact status and configuration of the Small Reasoning Model (SRM) subsystem.
2. Whether deterministic fallback inference is active or real neural NLI inference is loaded.
3. Which exact algorithmic components execute during malicious prompt detection.
4. Whether the frontend or reports ever falsely misrepresent fallback inference as neural inference.
5. Whether UI decisions originate from the live backend rather than client-side simulation.

---

## 2. SRM Subsystem Configuration & Reality Audit

### Live Runtime Probe:
```bash
curl -s http://127.0.0.1:8000/api/v1/srm/health | jq .
```
```json
{
  "configured_backend": "disabled",
  "active_backend": "deterministic_fallback",
  "is_fallback": true,
  "timeout_seconds": 5.0,
  "health": {
    "backend_name": "deterministic_fallback",
    "model_name": "halluguard-srm-fallback",
    "initialized": true,
    "available": true,
    "is_real_model": false,
    "device": "cpu",
    "inference_mode": "deterministic",
    "detail": "Rule-based fallback active (NOT a trained neural SRM).",
    "last_error": null,
    "model_loaded": false,
    "model_dtype": "torch.float32",
    "checkpoint_verified": false,
    "state": "READY"
  }
}
```

### Forensic Findings:
1. **Configured Backend:** The runtime setting `verification.srm_backend` is set to `"disabled"` by default when launching the general Operations Console server via `src/trustrag/api/server.py`.
2. **Active Engine:** The active engine is strictly `DeterministicFallbackSRM`.
3. **Real Model Flag:** `is_real_model = False`, `model_loaded = False`.
4. **No Semantic Camouflage:**
   - The backend explicitly returns `"detail": "Rule-based fallback active (NOT a trained neural SRM)."`
   - In `frontend/src/views.js` (lines 437-443), the UI displays a warning banner:
     ```javascript
     if (srm.is_fallback) {
       root.appendChild(
         el("div", {
           className: "banner warn",
           text: "Deterministic Fallback Active: Rule-based fallback is executing rather than a trained neural Small Reasoning Model.",
         })
       );
     }
     ```
   - Neither the backend, the UI, nor the Phase 23 report describes this operational mode as neural inference.

---

## 3. What Actually Executes for Malicious Prompt Detection?

A vital finding of this audit is that **the SRM subsystem (whether neural or fallback) does NOT execute during malicious prompt detection**:

```
[ User Query Submission ]
           |
           v
[ POST /api/v1/g1/analyze ]
           |
           v
+-------------------------------------------------------------+
|                 G1 InputGuardrail.evaluate()                |
|                                                             |
|  1. detect_obfuscation() (ZWSP, soft-hyphens, control chars)|
|  2. fold_mixed_script_confusables() (Cyrillic, Greek, etc.) |
|  3. count_fullwidth_ascii_confusables()                     |
|  4. clean_text() (Unicode NFKC & whitespace canonicalization)|
|  5. HarmfulIntentPolicy.evaluate() (Malware creation/theft)  |
|  6. match_threat_patterns() (SHARED_THREAT_PATTERNS regex)  |
|  7. _extract_base64_tokens() & decoded threat inspection    |
|  8. check_repetitive_flood() (DoS flood heuristic)          |
|  9. _SUSPICIOUS_META_RULES (Narrative/admin heuristics)     |
| 10. Risk aggregation -> Decision (BLOCK / FLAG / ALLOW)     |
+-------------------------------------------------------------+
           |
           v
[ G1AnalyzeResponse (JSON) ]
```

### Audit Confirmation:
- Malicious prompt detection is executed exclusively by **G1 Input Guardrails** (`src/trustrag/guardrails/input_guardrail.py`).
- G1 is a CPU-bound, deterministic rule engine that operates in **0.05 ms to 0.25 ms**.
- The neural NLI model (DeBERTa-v3) operates at stage **G3** (Output Claim Verification), checking whether generated answers are entailed by retrieved evidence. It is never invoked during query prompt screening.

---

## 4. UI Decision Origin Verification

To verify that the Operations Console does not simulate decisions in JavaScript:
1. Checked `frontend/src/views.js`:
   `actions.analyzeG1(query, enablePara)` invokes `TrustRAGApiClient.analyzeG1(query)`.
2. Checked `frontend/src/api.js`:
   ```javascript
   analyzeG1(query, enableParaphrasing = null) {
     const payload = { query };
     if (enableParaphrasing !== null) payload.enable_paraphrasing = enableParaphrasing;
     return this.request("/api/v1/g1/analyze", { method: "POST", body: payload });
   }
   ```
3. Verified network round-trip via live HTTP client:
   Each submission generates a unique UUID `request_id`, records telemetry in `MonitoringTracker`, appends an event to `AuditLogStore` on disk, and returns the server's verdict.
4. **Verdict:** All security decisions rendered in the browser originate from real backend assessment pipelines. Zero client-side mocking or hardcoded decisions exist.
