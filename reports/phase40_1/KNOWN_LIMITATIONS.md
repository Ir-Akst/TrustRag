# Known Limitations & Remaining Gaps

1. **Quoted Malicious Content FPR (10/25 on `benign_quoted_content`, 10.00% overall G1 FPR):** Misses the $\le 3\%$ target when analytical sentences use attribution phrasing outside the frozen attribution regex (`"Security auditors test whether..."`).
2. **G1 Adaptive Evasion (75.00% on `obfuscated_and_adaptive`):** 10/40 adaptive paraphrases bypassed G1.
3. **Chinese Unseen Variants (83.33% ADR):** 5/30 Chinese variants bypassed multilingual detection.
4. **G3 4-Class `INSUFFICIENT_EVIDENCE` vs `CONTRADICTED`:** 12/25 unsupported claims still triggered `CONTRADICTED` rather than `INSUFFICIENT_EVIDENCE` (safe release gate = 100%, 4-class status = 91.43%).
