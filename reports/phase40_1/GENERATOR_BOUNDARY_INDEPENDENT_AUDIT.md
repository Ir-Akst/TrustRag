# Generator-Boundary Independent Audit (Phase 40.1)

**Holdout:** `reports/phase40_1/datasets/holdout_firewall.jsonl` ($N=150$: 100 malicious, 50 benign controls).

- **Detection Recall:** **100.00%** (100/100) [95% CI: 96.30%, 100.00%]
- **Actual Final-Context Leakage:** **0.00%** (0/100) [95% CI: 0.00%, 3.70%]
- **Benign False Quarantine:** **0.00%** (0/50) [95% CI: 0.00%, 7.13%]

All 100 malicious cases (unseen citations `[Citation 9]`/`Footnote 7`/`Bibliography [5]`, Unicode-obfuscated role headers, nested markdown/HTML, multi-doc poisoned sets, split cross-doc instructions, and long-context prose injections) were blocked or sanitized before generator invocation.
