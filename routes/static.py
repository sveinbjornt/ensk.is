"""
Static resource routes.
"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from util import cache_response

router = APIRouter()


@router.get("/favicon.ico", include_in_schema=False)
@router.head("/favicon.ico", include_in_schema=False)
@cache_response
async def favicon(request: Request):
    return RedirectResponse(url="/static/img/favicon.ico", status_code=301)


@router.get("/apple-touch-icon.png", include_in_schema=False)
@cache_response
async def apple_touch_icon_redirect(request: Request):
    """Redirect to /apple-touch-icon.png"""
    return RedirectResponse(url="/static/img/apple-touch-icon.png", status_code=301)


@router.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
@router.head("/apple-touch-icon-precomposed.png", include_in_schema=False)
@cache_response
async def apple_touch_icon(request: Request):
    return RedirectResponse(url="/static/img/apple-touch-icon.png", status_code=301)
