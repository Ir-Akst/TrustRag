# TrustRAG Phase 11 — Step 3 Master Remediation Report

**Worktree:** `/home/aditya/rags/TrustRag-phase11` | **Branch:** `phase-11` | **Base HEAD:** `e65bcc80aac634900d1f8e343880fddf66cec168`

All 7 confirmed defects (`DEF-01` through `DEF-07`) have been investigated, fixed at root cause, and covered by permanent regression tests in `tests/unit/test_phase_11_remediation.py`.

| ID | Subsystem | Fix Summary | Modified Files |
| :---: | :--- | :--- | :--- |
| **DEF-01** | G1 Guardrail | Added `instruction_hierarchy_override` rule detecting explicit override prefixes and guardrail-bypass commands while preserving benign developer/admin queries. | `src/trustrag/guardrails/input_guardrail.py` |
| **DEF-02** | G2 F5 & F3 | Deduplicated/source-weighted F5 independent peer counts by `(source_key, content_sig)` and deduplicated TF-IDF inputs in `_compute_standalone_similarities`. | `src/trustrag/detection/signals.py`, `src/trustrag/detection/msd.py` |
| **DEF-03** | G3 Verifier | Added `_find_temporal_or_unitless_numeric_contradiction` for normalized °C/°F units, temporal years/ranges, and shared-entity unitless numeric conflicts while preserving `0.0` FSR. | `src/trustrag/verification/output_verifier.py` |
| **DEF-04** | G1 Paraphraser | Added possessive-normalized `_content_tokens` Jaccard blend in `validate_paraphrase` without lowering `min_similarity=0.30` or weakening drift checks. | `src/trustrag/guardrails/paraphraser.py` |
| **DEF-05** | API Rate Limiter | Replaced unbounded `defaultdict` with bounded LRU `OrderedDict(max_clients=10_000)` + expired-entry pruning + sanitized client keys. | `src/trustrag/api/security.py` |
| **DEF-06** | Audit Log Store | Added POSIX `fcntl.flock` advisory locking + cross-process tail sync + `os.fsync` + malformed-line resilience (with explicit warning fallback if `fcntl` unavailable). | `src/trustrag/api/audit.py` |
| **DEF-07** | Evaluation / MSD | Aligned `run_g2_phase10_experiment` signal lookup to canonical production key `"provenance"`. | `src/trustrag/evaluation/experiments/phase10_runner.py` |

**Remaining Limitations:**
- Neural SRM (`hf_local`), FilterRAG SLM, and external corpora remain `BLOCKED` offline.
- `SlidingWindowRateLimiter` is per-process in-memory (not distributed across independent nodes).
- `AuditLogStore` hash chain is tamper-evident, not tamper-proof against root/host-level file deletion.
- `35` legacy `mypy` errors in 4 untouched files and `1348` legacy `ruff` style lints remain outside Phase 11 scope.

