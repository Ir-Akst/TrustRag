# TrustRAG Phase 11 — Performance & Concurrency Acceptance Report

**Artifact:** `reports/phase11/phase11_audit_metrics.json` | **Target:** Live `aiohttp` `POST /api/v1/g1/analyze` on `127.0.0.1` (`environment=production`)

| Concurrency | Requests | Errors | Error Rate | Throughput (req/s) | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | 1 | 0 | `0.0000` | `482.20` | `2.03` | `—` (`n<5`) | `—` (`n<5`) | `—` (`n<5`) |
| **10** | 10 | 0 | `0.0000` | `1333.47` | `6.31` | `6.48` | `7.05` | `7.16` |
| **25** | 25 | 0 | `0.0000` | `1170.56` | `17.40` | `19.83` | `20.41` | `20.56` |
| **50** | 50 | 0 | `0.0000` | `1005.92` | `35.16` | `33.96` | `47.96` | `48.10` |

- **Peak Process RSS:** `232.16 MB`
- **Active Threads After Runner Cleanup:** `1` (no thread leaks)
- **Verdict:** **PASS** — `0%` error rate up to 50 concurrent requests, sub-50ms `p99`, clean shutdown.

