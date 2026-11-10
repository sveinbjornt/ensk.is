#!/usr/bin/env python3
"""

Ensk.is - Free and open English-Icelandic dictionary

Copyright (c) 2021-2026 Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or other
materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may
be used to endorse or promote products derived from this software without specific
prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.


Ensk.is FastAPI web application.

"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastmcp import FastMCP
from fastmcp.server.providers.openapi import MCPType
from fastmcp.utilities.openapi import HTTPRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from routes import api_router, static_router, web_router
from routes.core import TemplateResponse
from settings import PROJECT, settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run the MCP server's lifespan (session manager) alongside the app."""
    async with mcp_app.lifespan(app):
        yield


# Create app
app = FastAPI(
    title=PROJECT.NAME,
    description=PROJECT.DESCRIPTION,
    version=PROJECT.VERSION,
    contact={
        "name": PROJECT.EDITOR,
        "email": PROJECT.EMAIL,
    },
    license_info={
        "name": PROJECT.LICENSE,
    },
    lifespan=lifespan,
)

# Static files
STATIC_DIR = "static"
app.mount(f"/{STATIC_DIR}", StaticFiles(directory=STATIC_DIR), name=STATIC_DIR)

CACHE_CONTROL_MAX_AGE = 86400  # seconds


# Create a middleware class to set custom headers
class AddCustomHeaderMiddleware(BaseHTTPMiddleware):
    """Add custom headers to all responses."""

    CSP_DIRECTIVES = {
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "'unsafe-inline'",
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
        ],
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'"],
        "media-src": ["'self'"],
        "object-src": ["'none'"],
        "connect-src": ["'self'"],
        "form-action": ["'self'"],
        "frame-ancestors": ["'none'"],
        "frame-src": ["'none'"],
        "upgrade-insecure-requests": "",
        "base-uri": ["'none'"],
    }

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.url.path.startswith(f"/{STATIC_DIR}/"):
            response.headers["Cache-Control"] = (
                f"public, max-age={CACHE_CONTROL_MAX_AGE}"
            )
        else:
            response.headers["Content-Language"] = "is, en"

        csp_parts = [
            f"{directive} {' '.join(sources)}"
            for directive, sources in self.CSP_DIRECTIVES.items()
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_parts)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
        )

        return response


app.add_middleware(AddCustomHeaderMiddleware)


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    """Handle 404 Not Found errors."""
    return TemplateResponse(
        request,
        "404.html",
        {"request": request, "title": "404 - Síða fannst ekki"},
        status_code=404,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to catch all unhandled exceptions."""
    # Log the full exception for debugging purposes
    logging.error(
        "Unhandled exception for request %s: %s", request.url, exc, exc_info=True
    )

    # Return a JSON response for API routes
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"error": True, "errmsg": "An internal server error occurred."},
        )

    # Return a user-friendly HTML error page for all other routes
    return TemplateResponse(
        request,
        "500.html",
        {"request": request, "title": "500 - Villa kom upp"},
        status_code=500,
    )


# Include routers
app.include_router(web_router)
app.include_router(api_router)
app.include_router(static_router)


# MCP Configuration
MCP_PATH = "/mcp"
MCP_OPERATIONS = [
    "get_metadata",
    "search_for_word",
    "lookup_word",
    "lookup_single_word_parsed",
    "lookup_many_words_parsed",
]


def mcp_route_map(route: HTTPRoute, mcp_type: MCPType) -> MCPType:
    """Expose only the whitelisted API operations as MCP tools."""
    return MCPType.TOOL if route.operation_id in MCP_OPERATIONS else MCPType.EXCLUDE


# Create MCP server from the FastAPI app's OpenAPI schema
mcp = FastMCP.from_fastapi(
    app,
    name=PROJECT.NAME,
    instructions=f"{PROJECT.DESCRIPTION_SHORT_EN} MCP server",
    version=PROJECT.VERSION,
    route_map_fn=mcp_route_map,
)

# Serve the MCP streamable HTTP endpoint at exactly /mcp. Added as a route
# (not a mount) so other unmatched paths still hit the app's 404 handler and
# /mcp is not redirected to /mcp/.
mcp_app = mcp.http_app(path=MCP_PATH)
app.add_route(MCP_PATH, mcp_app)  # pyright: ignore[reportArgumentType]


# CLI invocation
if __name__ == "__main__":
    from argparse import ArgumentParser

    import uvicorn

    parser = ArgumentParser()
    parser.add_argument("--host", default=settings.web_app_host, type=str)
    parser.add_argument("--port", default=settings.web_app_port, type=int)
    parser.add_argument("--reload", default=settings.debug_mode, action="store_true")
    parser.add_argument("--log-level", default=settings.log_level, type=str)

    args = parser.parse_args()

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )
