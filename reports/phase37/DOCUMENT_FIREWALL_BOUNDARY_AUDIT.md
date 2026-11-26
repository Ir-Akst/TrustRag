# Document Firewall & Generator Boundary Audit

## Quantitative Results (N=140)
- Detection Recall: 66.67% (60/90, 95% CI: [56.42%, 75.55%])
- Generator Context Leakage Rate: 33.33% (30/90, 95% CI: [24.45%, 43.58%])
- False Quarantine Rate: 0.00% (0/50, 95% CI: [0.00%, 7.13%])
- Mean Utility Retention (Attacks): 78.61%
- Mean Utility Retention (All Docs): 86.25%

## Category Leakage Analysis
- `meta_declarative`: 15/15 quarantined, 0 leaked (0.0% leakage)
- `bracketed_split`: 15/15 quarantined, 0 leaked (0.0% leakage)
- `hidden_html_comment`: 15/15 quarantined, 0 leaked (0.0% leakage)
- `multi_sentence_injection`: 15/15 quarantined, 0 leaked (0.0% leakage)
- `citation_spoofing`: 0/15 quarantined, 15 leaked (100.0% leakage) — CRITICAL GAP
- `misleading_role_header`: 0/15 quarantined, 15 leaked (100.0% leakage) — CRITICAL GAP
