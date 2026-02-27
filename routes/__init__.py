"""
Routes module
"""

from .api import router as api_router
from .static import router as static_router
from .web import router as web_router

__all__ = ["web_router", "api_router", "static_router"]
