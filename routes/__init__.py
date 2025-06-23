"""
Routes module for the Ensk.is dictionary.
"""

from .web import router as web_router
from .api import router as api_router
from .static import router as static_router

__all__ = ["web_router", "api_router", "static_router"]