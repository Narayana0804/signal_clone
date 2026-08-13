"""Middleware package barrel export."""

from app.middleware.csrf import OriginProtectionMiddleware

__all__ = ["OriginProtectionMiddleware"]
