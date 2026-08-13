"""CSRF / Origin Protection Middleware."""

from urllib.parse import urlparse

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import settings

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
EXEMPT_PATHS = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}


def extract_origin(url_str: str | None) -> str | None:
    """Extract origin (scheme://netloc) from a URL string."""
    if not url_str:
        return None
    parsed = urlparse(url_str)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


class OriginProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing trusted Origin header validation for state-changing requests."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Safe methods are exempt from CSRF checks
        if request.method in SAFE_METHODS:
            return await call_next(request)

        # Explicitly exempt endpoints (like health check)
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Extract Origin or Referer header
        origin_header = request.headers.get("origin")
        referer_header = request.headers.get("referer")

        request_origin = extract_origin(origin_header) or extract_origin(referer_header)

        # Check if session cookie is present (authenticated request via cookie)
        has_session_cookie = "session_token" in request.cookies

        # If request carries an authentication cookie and is state-changing,
        # enforce that Origin/Referer matches a trusted CORS origin.
        if has_session_cookie:
            if not request_origin:
                return Response(
                    content='{"detail":"Missing Origin header for authenticated request"}',
                    status_code=status.HTTP_403_FORBIDDEN,
                    media_type="application/json",
                )

            trusted_origins = settings.cors_origin_list
            if request_origin not in trusted_origins:
                return Response(
                    content='{"detail":"Untrusted request origin"}',
                    status_code=status.HTTP_403_FORBIDDEN,
                    media_type="application/json",
                )

        return await call_next(request)
