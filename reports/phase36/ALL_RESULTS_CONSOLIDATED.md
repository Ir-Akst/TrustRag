# TrustRAG Phase 36 — All Results Consolidated

## Comprehensive Benchmark Summary
This document consolidates raw predictions, evaluation logs, and audit scorecards for Phase 36:

### 1. Workstream A: G1 Semantic Injection Defense
- Attack Detection Rate (ADR): 100.0% (160/160, 95% CI: [97.7%, 100.0%])
- Attack Success Rate (ASR): 0.0% (0/160)
- False Positive Rate (FPR): 0.0% (0/80, 95% CI: [0.0%, 4.6%])
- Novel Action Verbs ADR: 100.0% (40/40)
- Security Education FPR: 0.0% (0/40)

### 2. Workstream B: Document Firewall & Generator Boundary
- Detection Recall: 100.0% (80/80, 95% CI: [95.4%, 100.0%])
- Generator Context Leakage: 0.0% (0/80, 95% CI: [0.0%, 4.6%])
- False Quarantine Rate: 0.0% (0/40, 95% CI: [0.0%, 8.8%])
- Mean Utility Retention: 61.11%

### 3. Workstream C: Multilingual & Transliteration Defense
- Native Script ADR: 100.0% (135/135, 95% CI: [97.2%, 100.0%])
- Transliteration ADR: 100.0% (135/135, 95% CI: [97.2%, 100.0%])
- Overall Combined ADR: 100.0% (270/270, 95% CI: [98.6%, 100.0%])

### 4. Workstream D: Evidence Verification Utility
- Overall Accuracy: 87.5% (70/80, 95% CI: [78.5%, 93.1%])
- Supported Claim Acceptance: 100.0% (20/20, 95% CI: [83.9%, 100.0%])
- False Abstention Rate: 0.0% (0/20, 95% CI: [0.0%, 16.1%])
- Contradiction Recall: 50.0% (10/20, 95% CI: [29.9%, 70.1%])
- Unsupported Leakage: 0.0% (0/20, 95% CI: [0.0%, 16.1%])

### 5. Workstream E: Production Neural Inference Audit
- Profile A: 0 forward passes, 25.12 ms mean latency
- Profile B: 600 forward passes (24.0 passes/request), 1818.89 ms mean latency (~75.79 ms/pass)
- Concurrency, timeout, and shutdown fail-safe protections all verified.

### 6. Workstream F: Frontend & Backend E2E Integration
- 5/5 HTTP endpoints verified functional with HTTP 200 OK.
