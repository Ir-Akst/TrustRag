# Document Firewall Actual Generator-Boundary Audit

**Dataset:** `reports/phase39/datasets/firewall_generator_holdout.jsonl` ($N=160$: 110 malicious cases, 50 benign security docs).  
**Methodology:** Inspected the exact assembled `final_generator_context` (`sanitized_text`) after `DocumentInjectionFirewall.inspect_and_sanitize`, verifying whether malicious directives still reach the generator.

## 1. Aggregate Metrics
- **Detection Recall:** **45.45%** (50/110) [95% CI: 36.46%, 54.76%]
- **Actual Generator Leakage Rate:** **54.55%** (60/110) [95% CI: 45.24%, 63.54%]
- **False Quarantine Rate:** **0.00%** (0/50) [95% CI: 0.00%, 7.13%]
- **Clean Utility Retention:** **100.00%**

## 2. Per-Category Containment Breakdown

| Category | Malicious | Detected | Actually Leaked to Generator |
|---|---|---|---|
| `citation_spoofing` (`[Citation 4]`, `Footnote 2`, `Bibliography [3]`, `Ref. [12]`) | 20 | 0 | **20 (100%)** |
| `role_header_variations` (`ASSISTANT_OVERRIDE:`, `KERNEL_ADMIN:`, `POLICY_ENGINE:`, `### SYSTEM PROMPT:`) | 20 | 0 | **20 (100%)** |
| `nested_markdown_code` | 20 | 15 | **5 (25%)** |
| `html_comments` | 20 | 20 | **0 (0%)** |
| `split_long_context` | 20 | 15 | **5 (25%)** |
| `multiple_malicious_docs` | 10 | 0 | **10 (100%)** |
| `benign_security_docs` | 50 (Benign) | 0 FP | **0** |

**Conclusion:** Phase 38's citation and role-header regexes (`Reference [1]: Authoritative System Instruction:`, `DEVELOPER:`, `SYSTEM:`) are trivially bypassed by minor label variations, leaking 54.55% of malicious payloads directly into the generator context.
