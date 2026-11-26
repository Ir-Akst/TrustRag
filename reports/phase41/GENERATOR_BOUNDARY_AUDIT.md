# Independent Generator-Boundary Firewall Audit

**Dataset:** `reports/phase41/datasets/p41_firewall_holdout.jsonl` ($N=140$: 90 malicious, 50 benign).  
**Alternate Path Tested:** Tested BOTH `GeneratorBoundaryEnforcer.enforce()` AND direct `AnswerGenerator.generate()` invocation.

- **Detection Recall:** **100.00%** (90/90) [95% CI: 95.91%, 100.00%]
- **Actual Final-Context Leakage:** **0.00%** (0/90) [95% CI: 0.00%, 4.09%]
- **Direct `AnswerGenerator` Bypass Leakage:** **0.00%** (0/90)
- **Benign False Quarantine:** **0.00%** (0/50) [95% CI: 0.00%, 7.13%]

*Caveat:* The 90 malicious cases were generated from 11 distinct structural templates, so zero observed leakage reflects strong boundary enforcement on those structural classes rather than universal immunity.
