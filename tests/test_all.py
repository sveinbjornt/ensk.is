#!/usr/bin/env python3
"""

    Ensk.is - Free and open English-Icelandic dictionary

    Copyright (c) 2023 Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>

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

    Tests for ensk.is

"""

from typing import Dict, Any

import os
import sys

from fastapi.testclient import TestClient
from gen import delete_db
from db import EnskDatabase

# Add parent dir to path so we can import from there
basepath, _ = os.path.split(os.path.realpath(__file__))
src_path = os.path.join(basepath, "..")
sys.path.append(src_path)

from app import app


def in_ci_env() -> bool:
    return os.getenv("IN_CI_ENVIRONMENT") is not None


client = TestClient(app)


PAGE_ROUTES = [
    "/",
    "/about",
    "/files",
    "/item/vindictive",
    "/page/1",
    "/page/707",
    "/zoega",
    "/all",
    "/additions",
    "/robots.txt",
    "/sitemap.xml",
    "/apidoc",
]


def test_pages_routes() -> None:
    """Test page routes."""

    for route in PAGE_ROUTES:
        response = client.get(route)
        assert response.status_code == 200


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


def _verify_api_item(item: Dict[str, Any]) -> None:
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
        assert response.status_code == 200
        _verify_api_item(response.json())

    # /api/search/<word>
    for route in SEARCH_API_ROUTES:
        response = client.get(route)
        assert response.status_code == 200
        json = response.json()
        assert "results" in json
        assert len(json["results"]) > 10
        for r in json["results"]:
            _verify_api_item(r)
    for route in SINGLE_SEARCH_API_ROUTES:
        response = client.get(route)
        assert response.status_code == 200
        json = response.json()
        assert "results" in json
        assert len(json["results"]) == 1
        _verify_api_item(json["results"][0])

    # /api/suggest/<word>
    for route in SUGGEST_API_ROUTES:
        response = client.get(route)
        assert response.status_code == 200
        json = response.json()
        assert isinstance(json, list)
        assert len(json) == 10
        for i in json:
            assert isinstance(i, str)
    for route in SINGLE_SUGGEST_API_ROUTES:
        response = client.get(route)
        assert response.status_code == 200
        json = response.json()
        assert isinstance(json, list)
        assert len(json) == 1
        assert isinstance(json[0], str)


# NB: This test needs to run after all the other tests and
# should be kept at the bottom of the source file.
def test_db() -> None:
    """Test database wrapper."""
    # We only run these tests in CI environment
    if not in_ci_env():
        return

    # # Delete any pre-existing database file
    # delete_db()

    # # Reinstantiate DB wrapper
    # e = EnskDatabase().reinstantiate()

    # # The database is initially empty, so we should get no results
    # entries = e.read_all_entries()
    # assert len(entries) == 0
    # entries = e.read_all_additions()
    # assert len(entries) == 0
    # # entries = e.read_all_duplicates()
    # # assert len(entries) == 0

    # # Add an entry
    # e.add_entry("cat", "n. köttur", "", "", 0)

    # # Make sure there's only a single entry now
    # entries = e.read_all_entries()
    # assert len(entries) == 1
    # entries = e.read_all_additions()
    # assert len(entries) == 1
