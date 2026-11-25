# Workstream B — Document Firewall & Generator Boundary Results

## Methodology
Evaluation of `DocumentFirewall` on N=120 documents (80 injected passages, 40 benign control documents). Tested meta-directives (`Directive to AI agent:`), hidden HTML comments, bracketed split instructions, and citation spoofing.

## Results
- **Attack Detection Recall:** 100.0% (80/80, 95% CI: [95.4%, 100.0%])
- **Generator Context Leakage Rate:** 0.0% (0/80, 95% CI: [0.0%, 4.6%])
- **False Quarantine Rate:** 0.0% (0/40, 95% CI: [0.0%, 8.8%])
- **Mean Utility Retention:** 61.11%

## Remediation Details
- Added `declarative_agent_directive` pattern for explicit agent-directed overrides.
- Added `split_bracketed_instruction` pattern for staged multi-phase bracketed payloads.
- Surgical sentence-level filtering preserves genuine domain knowledge while stripping adversarial instructions.
