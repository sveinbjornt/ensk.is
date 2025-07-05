#!/usr/bin/env python3
"""

Ensk.is - Free and open English-Icelandic dictionary

Copyright (c) 2021-2025 Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>

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
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi_mcp import FastApiMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from info import PROJECT
from routes import web_router, api_router, static_router
from routes.core import TemplateResponse

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
)

# Static files
STATIC_DIR = "static"
app.mount(f"/{STATIC_DIR}", StaticFiles(directory=STATIC_DIR), name=STATIC_DIR)


# Create a middleware class to set custom headers
class AddCustomHeaderMiddleware(BaseHTTPMiddleware):
    """Add custom headers to all responses."""

    CSP_DIRECTIVES = {
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "'unsafe-inline'",
            "https://scripts.simpleanalyticscdn.com",
        ],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'"],
        "media-src": ["'self'"],
        "object-src": ["'none'"],
        "connect-src": ["'self'", "https://scripts.simpleanalyticscdn.com"],
        "form-action": ["'self'"],
        "frame-ancestors": ["'none'"],
    }

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.url.path.startswith(f"/{STATIC_DIR}/"):
            response.headers["Cache-Control"] = "public, max-age=86400"
        else:
            response.headers["Content-Language"] = "is, en"

        csp_parts = [
            f"{directive} {' '.join(sources)}"
            for directive, sources in self.CSP_DIRECTIVES.items()
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_parts)
        response.headers["X-Content-Type-Options"] = "nosniff"
        # response.headers["X-Frame-Options"] = "DENY"
        # response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
        )
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response


app.add_middleware(AddCustomHeaderMiddleware)


@app.exception_handler(404)
def not_found_exception_handler(request: Request, exc: HTTPException):
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
        f"Unhandled exception for request {request.url}: {exc}", exc_info=True
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
        "500.html",  # This template would need to be created
        {"request": request, "title": "500 - Villa kom upp"},
        status_code=500,
    )


# Include routers
app.include_router(web_router)
app.include_router(api_router)
app.include_router(static_router)


# MCP Configuration
MCP_OPERATIONS = [
    "get_metadata",
    "search_for_word",
    "lookup_word",
    "lookup_single_word_parsed",
    "lookup_many_words_parsed",
]

# Create and mount the MCP server for the FastAPI app
mcp = FastApiMCP(
    app,
    name=PROJECT.NAME,  # Name for your MCP server
    description=f"{PROJECT.DESCRIPTION_SHORT_EN} MCP server",  # Description
    # describe_all_responses=True,  # Include all possible response schemas
    describe_full_response_schema=True,  # Include full JSON schema in descriptions
    include_operations=MCP_OPERATIONS,
)
mcp.mount()


# CLI invocation
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
