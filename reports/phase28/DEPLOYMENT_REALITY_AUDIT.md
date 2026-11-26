# Phase 28 — Deployment Reality & Execution Audit

---

## 1. Architectural Serving Reality vs. Research Paper Claims

| Architectural Layer | Claim in Conceptual Paper | Verified Code Reality in Repository | Audit Finding |
| :--- | :--- | :--- | :--- |
| **G1 Execution** | Multi-vector input analysis | High-speed compiled regex matching (`input_guardrail.py`) | **Deterministic CPU Pattern Matcher** |
| **G1 Latency** | $0.11$ ms median | $0.1995$ ms median, $0.2660$ ms $p99$ on full suite | **$0.20$ ms empirical median** |
| **G2 Retrieval Filter** | Multi-signal detection engine | K-means clustering with 50% removal cap (`multi_signal_detector.py`) | **Verified with Removal Cap** |
| **SRM Production Serving** | DeBERTa-v3 neural cross-encoder | `DeterministicFallbackBackend` (`is_real_model = False`) | **Serving Heuristics, Not Neural Weights** |
| **Neural DeBERTa Status** | Active inference layer | Offline research evaluation prototype only | **Not Active in Live Server** |
| **Error Handling Policy** | Rigorous security containment | Fail-open (`ALLOW` / `G1_CLEAN` on exception) | **Fail-Open Availability Bias** |

---

## 2. Detailed Technical Audit

### 2.1 The Small Reasoning Model (SRM) Disconnect
- File: `src/trustrag/srm/client.py` and `src/trustrag/srm/backends.py`
- Default Configuration:
  ```python
  srm_config.backend = "disabled" # or "halluguard-srm-fallback"
  ```
- Runtime Execution:
  When a query is processed by the API server (`src/trustrag/api/server.py`), `SRMClient()` initializes `DeterministicFallbackBackend`. It checks simple string overlaps and pre-computed G2/G3 heuristic scores.
- Checkpoint Reality:
  The frozen checkpoint `/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch` exists and is valid, but is only instantiated when explicitly invoking offline evaluation classes (`NeuralNLISRMBackend`). It is **never loaded into memory during standard live server execution**.

### 2.2 Fail-Open Architecture
- In `src/trustrag/guardrails/input_guardrail.py`:
  ```python
  try:
      # evaluate regex matches
  except Exception as e:
      LOGGER.error(f"G1 guardrail failed: {e}")
      return GuardrailResult(decision=Decision.ALLOW, risk_score=0.0)
  ```
- In enterprise applications, fail-open preserves user experience during transient crashes. In an adversarial security context, however, an attacker who deliberately causes an internal regex timeout (e.g. via catastrophic backtracking) will bypass the filter entirely.

### 2.3 The Sybil Removal Cap ($C_r = 0.50$) as a Deterministic Vulnerability
- In `src/trustrag/retrieval/multi_signal_detector.py`:
  - `max_removal_ratio` is hardcoded to $0.50$.
  - When $K = 5$ retrieved passages are returned:
    - If 1 is poisoned ($20\%$): removed (0 in context).
    - If 2 are poisoned ($40\%$): removed (0 in context).
    - If 3 are poisoned ($60\%$): removal capped at $\lfloor 5 \times 0.5 \rfloor = 2$. **1 poisoned passage passes to context**.
    - If 4 are poisoned ($80\%$): removal capped at 2. **2 poisoned passages pass to context**.
- Under majority poisoning, G2 deterministically admits malicious passages.

---

## 3. Mandatory Paper Disclosures

Any manuscript submitted to a peer-reviewed venue must include the following explicit disclosures:
1. **Runtime Execution Disclosure**: The sub-millisecond pipeline latency ($1.42$ ms) is measured exclusively with `is_real_model = False` (CPU deterministic fallback). Neural cross-encoder latency ($\approx 65$ ms) must be reported separately.
2. **Fail-Open Policy Disclosure**: Acknowledge that G1 fails open under unhandled exceptions, prioritizing uptime over containment.
3. **Sybil Cap Frontier Disclosure**: Clearly state that G2 guarantees delivery of poisoned passages when the adversary controls $>50\%$ of the candidate pool.
