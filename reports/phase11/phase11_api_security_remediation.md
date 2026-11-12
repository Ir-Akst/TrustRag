# TrustRAG Phase 11 — API Security Remediation (`DEF-05`)

- **Original Behavior:** `SlidingWindowRateLimiter` in `src/trustrag/api/security.py` used an unbounded `defaultdict(deque)` keyed by `client_key`, permitting unbounded memory growth under distributed IP churn.
- **Fix:** Replaced `defaultdict` with a bounded LRU `OrderedDict[str, deque[float]]` (`max_clients=10_000` default). When at capacity, expired client entries are pruned first, followed by oldest-LRU eviction (`popitem(last=False)`). Client keys are sanitized (`strip()[:128] or "unknown"`), and `X-Forwarded-For` remains untrusted by default.
- **Regression Test:** `test_def05_bounded_rate_limiter_under_ip_churn_and_concurrency` verifies `client_count <= 50` under 200-IP flood, malformed key enforcement, and 8-thread concurrent safety.
- **Remaining Limitation:** In-memory rate limiting is per-process and not shared across separate worker processes or nodes.
