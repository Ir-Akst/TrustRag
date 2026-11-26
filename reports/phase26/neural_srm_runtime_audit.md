# TrustRAG Phase 26: Neural SRM & Runtime Subsystem Audit

**Audit Date:** 2026-11-24  
**Auditor:** Principal Systems Architect & Independent ML Auditor  
**Runtime Target:** TrustRAG Service (`src/trustrag/serving/service.py`) & Backend API Daemon  

---

## 1. Crucial Architectural Reality

A rigorous inspection of the codebase, runtime configurations, and live daemon logs was conducted to ascertain whether the DeBERTa-v3 model or SRM (Selective Risk Model) is active in inference:

### Summary of Component Modes:

1. **G1 Input Guardrail:**
   - **Mode:** Purely deterministic, CPU-bound string normalization and compiled regular expressions (`SHARED_THREAT_PATTERNS` and `HarmfulIntentPolicy`).
   - **Neural Model Usage:** **NONE (0%)**. G1 does not load, invoke, or query any neural language model or embedding matrix.
2. **G2 Multi-Signal Detector (MSD):**
   - **Mode:** Multi-signal document scoring (TF-IDF cosine similarity, perplexity thresholding, regex instruction scanning).
   - **Neural Model Usage:** Optional embedding/perplexity inputs, but default execution operates with TF-IDF and heuristic rules.
3. **G3 Claim Verification / SRM:**
   - **Configured Backend in Production:** `settings.srm.backend = 'disabled'`
   - **Configured Verification Backend:** `settings.verification.nli_backend = 'heuristic'`
   - **Active SRM Backend:** `DeterministicFallbackBackend`
   - **SRM Model Name:** `halluguard-srm-fallback`
   - **Real Model Active (`is_real_model`):** **`False`**

---

## 2. Evidence from Service Health Inspection

Inspection of `TrustRAGService.health()` returns the following explicit runtime structure:

```python
{
  "status": "healthy",
  "ready": True,
  "srm_backend": "disabled",
  "srm_health": {
    "backend_name": "deterministic_fallback",
    "model_name": "halluguard-srm-fallback",
    "initialized": True,
    "available": True,
    "is_real_model": False,
    "device": "cpu",
    "inference_mode": "deterministic",
    "detail": "Rule-based fallback active (NOT a trained neural SRM).",
    "model_loaded": False,
    "checkpoint_verified": False,
    "state": "READY"
  }
}
```

---

## 3. Publication Integrity Invariants

1. **No False Claims of Neural Detection:**
   Any paper draft claiming that TrustRAG performs "neural prompt injection detection" or that G1 relies on deep learning is **factually false**. G1 is a deterministic regex rule-engine.
2. **Honest SRM Reporting:**
   The paper must explicitly state that the production runtime serves a rule-based deterministic fallback (`is_real_model=False`) for the SRM subsystem, preserving neural weights in an offline research evaluation capacity.
