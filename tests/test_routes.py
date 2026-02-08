#!/usr/bin/env python3
"""
Test ensk.is web application routes
"""

from typing import Any
from unittest.mock import patch

import os
import sys
from http import HTTPStatus

from fastapi.testclient import TestClient

# Add parent dir to path so we can import from there
basepath, _ = os.path.split(os.path.realpath(__file__))
src_path = os.path.join(basepath, "..")
sys.path.append(src_path)


# Mock synonym functions before importing app
def mock_synonyms_for_word(w: str) -> list[str]:
    """Mock function for synonyms_for_word."""
    return ["test", "mock"]


def mock_linked_synonyms_for_word(w: str, wordlist: list[str]) -> list[dict[str, Any]]:
    """Mock function for linked_synonyms_for_word."""
    return [{"word": "test", "exists": False}, {"word": "mock", "exists": False}]


with patch("dict.synonyms_for_word", side_effect=mock_synonyms_for_word):
    with patch(
        "dict.linked_synonyms_for_word", side_effect=mock_linked_synonyms_for_word
    ):
        from app import app  # noqa: E402


def in_ci_env() -> bool:
    """Check if running in CI environment."""
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
    "/cat/ao",
    "/cat/fn",
    "/search?q=quick",
    "/robots.txt",
    "/sitemap.xml",
    "/apple-touch-icon.png",
    "/apple-touch-icon-precomposed.png",
    "/favicon.ico",
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
    """Verify that an API item has the required keys."""
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

    # /api/metadata
    response = client.get("/api/metadata")
    assert response.status_code == HTTPStatus.OK
    assert "editor" in response.json()

    # /api/item/parsed/<word>
    response = client.get("/api/item/parsed/calumny")
    assert response.status_code == HTTPStatus.OK
    json = response.json()
    _verify_api_item(json)
    assert "parsed" in json

    # /api/item/parsed/many/
    response = client.get("/api/item/parsed/many/?q=calumny,zymotic")
    assert response.status_code == HTTPStatus.OK
    json = response.json()
    assert "calumny" in json
    assert "zymotic" in json


def test_more_web_routes() -> None:
    """Test more web routes."""

    # /search with empty query
    response = client.get("/search?q=")
    assert response.status_code == HTTPStatus.OK

    # /page with invalid page number
    response = client.get("/page/9999")
    assert response.status_code == HTTPStatus.NOT_FOUND

    # /cat with invalid category
    response = client.get("/cat/invalidcat")
    assert response.status_code == HTTPStatus.OK


def test_edge_cases() -> None:
    """Test edge cases."""

    # Search with a very long query string
    response = client.get("/search?q=" + "a" * 1000)
    assert response.status_code == HTTPStatus.OK

    # Search with a query string containing only special characters
    response = client.get("/search?q=!@#$%^&*()")
    assert response.status_code == HTTPStatus.OK

    # Item that doesn't exist
    response = client.get("/item/a_word_that_does_not_exist")
    assert response.status_code == HTTPStatus.NOT_FOUND

    # API item that doesn't exist
    response = client.get("/api/item/a_word_that_does_not_exist")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["error"] is True

    # API parsed single that doesn't exist
    response = client.get("/api/item/parsed/a_word_that_does_not_exist")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["error"] is True

    # API parsed many with empty query
    response = client.get("/api/item/parsed/many/?q=")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {}

    # API parsed many with strip_html and strip_parentheses
    response = client.get(
        "/api/item/parsed/many/?q=abacus&strip_html=1&strip_parentheses=1"
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() != {}

    # API parsed many with a very long query
    response = client.get("/api/item/parsed/many/?q=" + ",".join(["a"] * 1000))
    assert response.status_code == HTTPStatus.OK

    # Page with non-integer page number
    response = client.get("/page/abc")
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # Page with negative page number
    response = client.get("/page/-1")
    assert response.status_code == HTTPStatus.NOT_FOUND
