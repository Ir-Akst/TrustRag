# TrustRAG Phase 11 — Audit Log Integrity Remediation (`DEF-06`)

- **Original Behavior:** `AuditLogStore` in `src/trustrag/api/audit.py` used `threading.RLock()` without OS file locking or cross-process tail synchronization, risking sequence/hash-chain forks under multi-process writers.
- **Fix:** Added `_advisory_file_lock()` using `fcntl.flock(LOCK_EX)` on POSIX (logging an explicit warning if `fcntl` is unavailable), `_sync_tail_locked()` to advance `seq`/`_last_hash` from records written by peer processes before appending, `flush()` + `os.fsync()`, and graceful skipping of truncated/malformed lines during `_load_existing()`.
- **Regression Test:** `test_def06_multiprocess_audit_log_chain_integrity` spawns 3 independent processes writing 5 records each (`15` total) to the same JSONL file and verifies `verify_chain() is True`, sequential count `15`, and crash-safe reload after a truncated trailing line.
- **Remaining Limitation:** Hash-chaining + advisory locking provide tamper-evidence and multi-process write integrity, not tamper-proofing against privileged OS deletion/modification.

