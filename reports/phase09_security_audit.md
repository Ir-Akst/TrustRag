# TrustRAG Phase 09 — Security & Access-Control Audit

**Audited Scope:** [`src/trustrag/api/`](file:///home/aditya/rags/TrustRag/src/trustrag/api/security.py) and [`frontend/`](file:///home/aditya/rags/TrustRag/frontend/index.html)

---

## 1. Threat Matrix & Implemented Controls

| Threat Vector | Mitigation Implemented | Verification Evidence |
| :--- | :--- | :--- |
| **Unauthorized API Access** | Constant-time (`hmac.compare_digest`) Bearer / `X-API-Key` validation via `TRUSTRAG_API_TOKEN`. `TRUSTRAG_ENV=production` refuses startup without a token. | Verified `401 Unauthorized` on unauthenticated `/api/v1/config` & `/api/v1/pipeline/execute` in unit tests and live port `18090` smoke test. |
| **Broken Access / Weakening Defense** | Only 7 safe fields exposed in `_EDITABLE_SPECS`; `guardrails.enabled`, `removal_cap_ratio`, and `msd.enable_freq_density` are immutable (`422` rejected). | Verified `422` rejection on `guardrails.enabled=False` in `test_phase_09_api.py`. |
| **Cross-Site Scripting (XSS)** | Zero `innerHTML` usage with untrusted strings (`textContent` / `createTextNode` only); strict `Content-Security-Policy` (`script-src 'self'; object-src 'none'`). | Verified XSS payload stays inert text node in `frontend/tests/dashboard.test.mjs`; CSP header verified in API tests. |
| **Unsafe CORS** | Default same-origin only; explicit `TRUSTRAG_CORS_ORIGINS` allowlist without wildcard `*` credentials. | Verified allowed origin returns ACAO header while disallowed origin omits it. |
| **Path Traversal** | Static asset handler resolves paths and verifies `candidate.startswith(base_resolved)`; API never accepts raw filesystem paths. | Verified `GET /../configs/base.yaml` returns `404` in `test_phase_09_fullstack_integration.py`. |
| **Unbounded Resource / DoS** | `client_max_size=1_048_576` (1 MiB), sliding-window per-IP rate limiter (`429`), bounded `asyncio.wait_for` execution timeouts (`504`/`503`). | Verified `429 RATE_LIMITED` and bounded timeout isolation in tests. |
| **Secret Leakage & Stack Traces** | `_safe_invoke` omits stack traces (`500 INTERNAL_SERVER_ERROR`); `AuditLogStore` redacts Bearer/API keys (`[REDACTED]`); config snapshot strips `llm.api_key`. | Verified `[REDACTED]` persistence in `test_phase_09_api.py`. |
| **Audit-Log Tampering** | Append-only JSONL with SHA-256 `prev_hash -> entry_hash` chain; no edit/delete endpoints; `verify_chain()` surfaces tampering. | Verified `chain_valid=True` in `AuditQueryResponse`. |
| **Clickjacking / MIME Sniffing** | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`. | Verified response headers in `test_phase_09_api.py`. |

---

## 2. Residual Security Limitations (Documented)
1. **Single Static Shared Token:** Authentication uses a configured `TRUSTRAG_API_TOKEN` rather than multi-user RBAC/OIDC (appropriate for single-tenant/internal deployment; put behind an authenticating reverse proxy/IdP for multi-tenant enterprise use).
2. **In-Memory Rate Limiter:** `SlidingWindowRateLimiter` is per-process in-memory; multi-worker deployments should place rate limiting at an API gateway/reverse proxy.
3. **Browser Token Storage:** Dashboard stores optional operator token in `sessionStorage` (cleared on tab close) rather than HttpOnly cookies.
