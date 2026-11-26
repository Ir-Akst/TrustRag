# Phase 44 — Security Regression & Production Verification Results

## 1. Document Firewall & Generator-Boundary Enforcement ($N=140$)
Evaluated across 90 malicious documents and 50 benign documents:
- **Context Leakage:** `0.0%` (0/90, Wilson 95% CI `[0.00%, 4.09%]`)
- **Direct `AnswerGenerator` Bypass Leakage:** `0.0%` (0/90)
- **False Quarantine (Benign):** `0.0%` (0/50)

## 2. G1 Security Preservation
- **Fresh Holdout ($N=160$):** `ADR = 98.33%` (59/60, 95% CI `[91.14%, 99.71%]`), `ASR = 1.67%`, `FPR = 0.0%` (0/100, 95% CI `[0.00%, 3.70%]`).
- **Multilingual & Transliterated Attacks:** `100.0%` (15/15, 95% CI `[79.61%, 100.0%]`).
- **Direct Attacks:** `100.0%` (15/15).
- **Indirect & Narrative Attacks:** `100.0%` (15/15).
- **Mixed Benign + Embedded Attack:** `93.33%` (14/15, 95% CI `[70.18%, 98.81%]`).

## 3. Profile B Genuine DeBERTa Neural Execution & Production Lifecycle
Measured with the frozen DeBERTa-v3-small NLI checkpoint (`/home/aditya/rags/models/trained/deberta-v3-small-nli-phase11_1-full3epoch`):
- **Warm Requests:** `15`
- **Genuine `torch` Forward Passes:** `82`
- **NLI Cache:** `209` cache hits, `466` cache misses
- **Warm Latency:** Mean `1642.258 ms`, p50 `1622.672 ms`, p95 `1887.055 ms`, p99 `1994.663 ms`
- **Peak RSS:** `1543.22 MB`
- **8-Thread Concurrency:** `true` (all succeeded)
- **Timeout Fail-Closed (`abstained=True`):** `true`
- **Shutdown Fail-Closed (`abstained=True`):** `true`

## 4. Frozen Checkpoint & Release Anchor Integrity
- **Frozen Model SHA-256 (`checksums.sha256`):** All 8 files (`checkpoint_meta.json`, `config.json`, `model.safetensors`, `optimizer.pt`, `rng_state.pt`, `scheduler.pt`, `tokenizer.json`, `tokenizer_config.json`) verified `OK`.
- **Release Anchor (`531bff32745ede1bd1b38609cc6daf653d3eff24` / `trustrag-v1.0.0-rc1`):** Verified intact in Git ancestry (`git merge-base --is-ancestor` exited 0).
