"""
Ensk.is
Static resource routes
"""

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter()

# These responses are not cached with @cache_response. Constructing them is
# cheap (FileResponse reads from disk on every send regardless), and a cached
# FileResponse is actively wrong: Starlette sets Content-Length/Last-Modified/
# ETag with setdefault on first send, so a reused instance would keep serving
# the first request's headers after the file changed on disk.


@router.get("/apple-touch-icon.png", include_in_schema=False)
@router.head("/apple-touch-icon.png", include_in_schema=False)
async def apple_touch_icon_redirect(request: Request) -> RedirectResponse:
    return RedirectResponse(url="static/img/apple-touch-icon.png", status_code=301)


@router.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
@router.head("/apple-touch-icon-precomposed.png", include_in_schema=False)
async def apple_touch_icon(request: Request) -> RedirectResponse:
    return RedirectResponse(url="static/img/apple-touch-icon.png", status_code=301)


@router.get("/favicon.ico", include_in_schema=False)
@router.head("/favicon.ico", include_in_schema=False)
async def favicon(request: Request) -> FileResponse:
    return FileResponse("static/img/favicon.ico", media_type="image/x-icon")


@router.get("/robots.txt", include_in_schema=False)
@router.head("/robots.txt", include_in_schema=False)
async def robots(request: Request) -> FileResponse:
    return FileResponse("static/files/robots.txt", media_type="text/plain")
