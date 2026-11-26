# Generator-Boundary Security Report

**Holdout Dataset:** `reports/phase40/datasets/holdout_firewall.jsonl` ($N=150$: 100 malicious, 50 benign controls).

## Execution Path & Enforcement
1. Retrieved documents pass through `DocumentInjectionFirewall.sanitize_retrieved_documents` (Unicode confusable folding, zero-width stripping, multi-line block segmentation).
2. `GeneratorBoundaryEnforcer.enforce()` preserves `trust_score` and `provenance` metadata, checks cross-document split instructions, serializes evidence inside `<untrusted_evidence>` tags, and runs independent pre-invocation `validate_serialized_context()`.
3. Both `TrustRAGPipeline.run()` and `AnswerGenerator.generate()` enforce this boundary fail-closed.

## Empirical Boundary Results
- **Detection Recall:** **100.00%** (100/100) [95% CI: 96.30%, 100.00%]
- **Observed Generator-Boundary Leakage:** **0.00%** (0/100) [95% CI: 0.00%, 3.70%]
- **False Quarantine on Benign Security Docs:** **0.00%** (0/50) [95% CI: 0.00%, 7.13%]

*Note:* Zero observed leakage in $N=100$ cases establishes an upper 95% confidence bound of 3.70% residual risk, not absolute impossibility.
