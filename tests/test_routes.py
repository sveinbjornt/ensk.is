#!/usr/bin/env python3
"""
Test ensk.is web application routes
"""

from typing import Any

import os
import sys
from http import HTTPStatus

from fastapi.testclient import TestClient

# Add parent dir to path so we can import from there
basepath, _ = os.path.split(os.path.realpath(__file__))
src_path = os.path.join(basepath, "..")
sys.path.append(src_path)

from app import app  # noqa: E402


def in_ci_env() -> bool:
    return os.getenv("IN_CI_ENVIRONMENT") is not None


client = TestClient(app)

PAGE_ROUTES = [
    "/",
    "/about",
    "/english",
    "/english_icelandic_dictionary",
    "/files",
    "/item/vindictive",
    "/page/1",
    "/page/707",
    "/zoega",
    "/all",
    "/additions",
    "/original",
    "/duplicates",
    "/capitalized",
    "/multiword",
    "/nonascii",
    "/stats",
    "/robots.txt",
    "/sitemap.xml",
    "/favicon.ico",
    "/cat/ao",
    "/cat/fn",
    "/search?q=quick",
]


def test_pages_routes() -> None:
    """Test page routes."""

    for route in PAGE_ROUTES:
        response = client.get(route)
        assert response.status_code == HTTPStatus.OK


REQ_ITEM_KEYS = [
    "word",
    "def",
    "ipa_uk",
    "ipa_us",
    "audio_uk",
    "audio_us",
    "page_num",
    "page_url",
]


def _verify_api_item(item: dict[str, Any]) -> None:
    keys = item.keys()
    for rk in REQ_ITEM_KEYS:
        assert rk in keys


ITEM_API_ROUTES = ["/api/item/calumny", "/api/item/zymotic"]

SEARCH_API_ROUTES = ["/api/search/con", "/api/search/mon"]
SINGLE_SEARCH_API_ROUTES = ["/api/search/quintessence", "/api/search/zombie"]

SUGGEST_API_ROUTES = ["/api/suggest/con", "/api/suggest/mon"]
SINGLE_SUGGEST_API_ROUTES = ["/api/suggest/quintessence", "/api/suggest/zombie"]


def test_api_routes() -> None:
    """Test API routes."""

    # /api/item/<word>
    for route in ITEM_API_ROUTES:
        response = client.get(route)
        assert response.status_code == HTTPStatus.OK
        _verify_api_item(response.json())

    # /api/search/<word>
    for route in SEARCH_API_ROUTES:
        response = client.get(route)
        assert response.status_code == HTTPStatus.OK
        json = response.json()
        assert "results" in json
        assert len(json["results"]) > 10
        for r in json["results"]:
            _verify_api_item(r)
    for route in SINGLE_SEARCH_API_ROUTES:
        response = client.get(route)
        assert response.status_code == HTTPStatus.OK
        json = response.json()
        assert "results" in json
        assert len(json["results"]) == 1
        _verify_api_item(json["results"][0])

    # /api/suggest/<word>
    for route in SUGGEST_API_ROUTES:
        response = client.get(route)
        assert response.status_code == HTTPStatus.OK
        json = response.json()
        assert isinstance(json, list)
        assert len(json) == 10
        for i in json:
            assert isinstance(i, str)
    for route in SINGLE_SUGGEST_API_ROUTES:
        response = client.get(route)
        assert response.status_code == HTTPStatus.OK
        json = response.json()
        assert isinstance(json, list)
        assert len(json) == 1
        assert isinstance(json[0], str)
