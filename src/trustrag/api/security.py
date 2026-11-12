"""API security middleware: authentication, strict CORS, CSP headers, and rate limiting."""

from __future__ import annotations

import hmac
import threading
import time
from collections import OrderedDict, deque
from typing import Any

from aiohttp import web

from trustrag.api.schemas import APIErrorResponse

DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)


class SlidingWindowRateLimiter:
    """Bounded, thread-safe per-client sliding-window request rate limiter.

    Note: In-memory state is per-process and not shared across distributed workers.
    """

    def __init__(
        self,
        max_requests: int = 120,
        window_seconds: float = 60.0,
        max_clients: int = 10_000,
    ) -> None:
        self._max_requests = max(1, max_requests)
        self._window = max(1.0, window_seconds)
        self._max_clients = max(1, max_clients)
        self._lock = threading.Lock()
        self._hits: OrderedDict[str, deque[float]] = OrderedDict()

    @property
    def client_count(self) -> int:
        with self._lock:
            return len(self._hits)

    def allow(self, client_key: str) -> bool:
        key = str(client_key or "unknown").strip()[:128] or "unknown"
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            dq = self._hits.get(key)
            if dq is None:
                if len(self._hits) >= self._max_clients:
                    expired = [k for k, q in self._hits.items() if not q or q[-1] < cutoff]
                    for k in expired:
                        del self._hits[k]
                    while len(self._hits) >= self._max_clients:
                        self._hits.popitem(last=False)
                dq = deque()
                self._hits[key] = dq
            else:
                self._hits.move_to_end(key)

            while dq and dq[0] < cutoff:
                dq.popleft()
            if len(dq) >= self._max_requests:
                return False
            dq.append(now)
            return True


def json_error(
    status: int,
    *,
    error: str,
    code: str,
    request_id: str | None = None,
    details: list[str] | None = None,
) -> web.Response:
    payload = APIErrorResponse(
        error=error,
        code=code,
        request_id=request_id,
        details=details or [],
    )
    return web.json_response(payload.model_dump(), status=status)


def _extract_token(request: web.Request) -> str | None:
    auth_hdr = request.headers.get("Authorization", "")
    if auth_hdr.lower().startswith("bearer "):
        return auth_hdr[7:].strip()
    api_key = request.headers.get("X-API-Key", "")
    return api_key.strip() or None


def build_security_middleware(
    *,
    api_token: str | None,
    cors_origins: tuple[str, ...] = (),
    rate_limiter: SlidingWindowRateLimiter | None = None,
    require_token_for_mutations: bool = False,
) -> Any:
    """Create aiohttp security middleware enforcing headers, CORS, rate limits, and auth."""
    limiter = rate_limiter or SlidingWindowRateLimiter()
    allowed_origins = {o.strip() for o in cors_origins if o.strip()}

    @web.middleware
    async def security_middleware(request: web.Request, handler: Any) -> web.StreamResponse:
        origin = request.headers.get("Origin")
        cors_headers: dict[str, str] = {}
        if origin and origin in allowed_origins:
            cors_headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key",
                "Vary": "Origin",
            }

        if request.method == "OPTIONS":
            resp: web.StreamResponse = web.Response(status=204, headers=cors_headers)
        else:
            client_ip = request.remote or "unknown"
            if request.path.startswith("/api/") and not limiter.allow(client_ip):
                resp = json_error(
                    429,
                    error="Rate limit exceeded; retry later.",
                    code="RATE_LIMITED",
                )
            elif request.path.startswith("/api/"):
                needs_auth = api_token is not None and request.path != "/api/v1/health"
                if require_token_for_mutations and request.method in {"POST", "PUT", "PATCH", "DELETE"} and api_token is None:
                    resp = json_error(
                        401,
                        error="Authentication token is required for mutating API endpoints in production.",
                        code="AUTH_REQUIRED",
                    )
                elif needs_auth and api_token is not None:
                    supplied = _extract_token(request)
                    if not supplied or not hmac.compare_digest(supplied, api_token):
                        resp = json_error(
                            401,
                            error="Unauthorized: valid Bearer token or X-API-Key required.",
                            code="UNAUTHORIZED",
                        )
                    else:
                        resp = await _safe_invoke(request, handler)
                else:
                    resp = await _safe_invoke(request, handler)
            else:
                resp = await _safe_invoke(request, handler)

        resp.headers.update(cors_headers)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Content-Security-Policy"] = DEFAULT_CSP
        return resp

    return security_middleware


async def _safe_invoke(request: web.Request, handler: Any) -> web.StreamResponse:
    try:
        return await handler(request)
    except web.HTTPException as exc:
        if request.path.startswith("/api/"):
            return json_error(
                exc.status,
                error=exc.reason or "HTTP request error.",
                code=f"HTTP_{exc.status}",
            )
        raise
    except Exception:
        return json_error(
            500,
            error="Internal server error.",
            code="INTERNAL_SERVER_ERROR",
        )
