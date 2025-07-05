"""
Ensk.is
Static resource routes
"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, FileResponse

from util import cache_response


router = APIRouter()


@cache_response
@router.get("/apple-touch-icon.png", include_in_schema=False)
async def apple_touch_icon_redirect(request: Request) -> RedirectResponse:
    """Redirect to /apple-touch-icon.png"""
    return RedirectResponse(url="static/img/apple-touch-icon.png", status_code=301)


@cache_response
@router.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
@router.head("/apple-touch-icon-precomposed.png", include_in_schema=False)
async def apple_touch_icon(request: Request) -> RedirectResponse:
    return RedirectResponse(url="static/img/apple-touch-icon.png", status_code=301)


@cache_response
@router.get("/favicon.ico", include_in_schema=False)
@router.head("/favicon.ico", include_in_schema=False)
async def favicon(request: Request) -> FileResponse:
    return FileResponse("static/img/favicon.ico", media_type="image/x-icon")


@cache_response
@router.get("/robots.txt", include_in_schema=False)
@router.head("/robots.txt", include_in_schema=False)
async def robots(request: Request) -> FileResponse:
    return FileResponse("static/files/robots.txt", media_type="text/plain")
