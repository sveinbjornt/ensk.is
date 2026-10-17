#!/usr/bin/env python3
"""
Test the response cache decorator used by the ensk.is routes
"""

import asyncio
import os
import sys
from typing import Any

from fastapi import Request
from fastapi.testclient import TestClient

# Add parent dir to path so we can import from there
basepath, _ = os.path.split(os.path.realpath(__file__))
src_path = os.path.join(basepath, "..")
sys.path.append(src_path)

from app import app  # noqa: E402
from routes.core import _ENTRY_OVERHEAD_BYTES, cache_response  # noqa: E402

client = TestClient(app)


def _fake_request(path: str = "/", query: str = "") -> Request:
    """Build a throwaway Request, as FastAPI would inject into an endpoint."""
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "query_string": query.encode(),
            "headers": [],
        }
    )


def test_distinct_requests_hit_the_same_cache_entry() -> None:
    """A fresh Request per call must not produce a fresh cache entry.

    Regression test: the key was previously built from the Request object,
    which hashes by identity, so every call missed and the cache grew forever.
    """
    calls = 0

    @cache_response
    async def endpoint(request: Request) -> str:
        nonlocal calls
        calls += 1
        return "rendered"

    async def run() -> None:
        for _ in range(5):
            assert await endpoint(request=_fake_request()) == "rendered"

    asyncio.run(run())

    assert calls == 1, "endpoint should have been rendered only once"
    assert len(endpoint.cache) == 1, "cache should hold a single entry"


def test_parameters_still_separate_cache_entries() -> None:
    """Excluding the Request must not collapse distinct parameters together."""
    calls = []

    @cache_response
    async def endpoint(request: Request, w: str) -> str:
        calls.append(w)
        return f"entry:{w}"

    async def run() -> None:
        assert await endpoint(request=_fake_request(), w="cat") == "entry:cat"
        assert await endpoint(request=_fake_request(), w="dog") == "entry:dog"
        assert await endpoint(request=_fake_request(), w="cat") == "entry:cat"

    asyncio.run(run())

    assert calls == ["cat", "dog"]
    assert len(endpoint.cache) == 2


class _SizedResponse:
    """Stand-in for a rendered response of a known size."""

    def __init__(self, nbytes: int) -> None:
        self.body = b"x" * nbytes


BODY = 4096
ENTRY = BODY + _ENTRY_OVERHEAD_BYTES


def test_cache_is_bounded_by_total_bytes() -> None:
    """The LRU must evict on total size, not entry count."""
    budget = 3 * ENTRY

    @cache_response(budget)
    async def endpoint(request: Request, w: str) -> _SizedResponse:
        return _SizedResponse(BODY)

    async def run() -> None:
        for w in ("a", "b", "c", "d", "e", "f"):
            await endpoint(request=_fake_request(), w=w)

    asyncio.run(run())

    assert endpoint.cache.currsize <= budget
    assert len(endpoint.cache) == 3, "six requests, budget for three"


def test_oversized_response_is_served_but_not_cached() -> None:
    """A response larger than the whole budget must not evict everything."""
    budget = 2 * ENTRY

    @cache_response(budget)
    async def endpoint(request: Request, n: int) -> _SizedResponse:
        return _SizedResponse(n)

    async def run() -> None:
        await endpoint(request=_fake_request(), n=BODY)
        # This one alone exceeds the whole budget
        huge = await endpoint(request=_fake_request(), n=budget * 4)
        assert len(huge.body) == budget * 4, "oversized response still served"

    asyncio.run(run())

    assert len(endpoint.cache) == 1, "small entry survived, huge one not stored"
    assert endpoint.cache.currsize == ENTRY


def test_exceptions_are_not_cached() -> None:
    """A failing call must not poison the cache with a stored exception."""
    calls = 0

    @cache_response
    async def endpoint(request: Request) -> str:
        nonlocal calls
        calls += 1
        raise ValueError("boom")

    async def run() -> None:
        for _ in range(2):
            try:
                await endpoint(request=_fake_request())
            except ValueError:
                pass

    asyncio.run(run())

    assert calls == 2
    assert len(endpoint.cache) == 0


def test_repeated_page_requests_do_not_grow_the_cache() -> None:
    """End-to-end: repeated identical requests must reuse one cached response."""
    from routes.web import sitemap

    sitemap.cache.clear()

    for _ in range(3):
        assert client.get("/sitemap.xml").status_code == 200

    assert len(sitemap.cache) == 1
    assert sitemap.cache.currsize <= sitemap.cache.maxsize


def test_cached_route_still_serves_correct_per_word_content() -> None:
    """Distinct words must not serve each other's cached page."""
    cat = client.get("/item/cat")
    dog = client.get("/item/dog")

    assert cat.status_code == 200
    assert dog.status_code == 200
    assert cat.text != dog.text
    assert "cat" in cat.text
    assert "dog" in dog.text


def test_search_limit_is_clamped() -> None:
    """A non-positive or huge limit must not render the whole dictionary."""
    from routes.core import DEFAULT_SEARCH_LIMIT, MAX_SEARCH_LIMIT, clamp_search_limit

    assert clamp_search_limit(0) == DEFAULT_SEARCH_LIMIT
    assert clamp_search_limit(-1) == DEFAULT_SEARCH_LIMIT
    assert clamp_search_limit(None) == DEFAULT_SEARCH_LIMIT
    assert clamp_search_limit(10) == 10
    assert clamp_search_limit(99999) == MAX_SEARCH_LIMIT


def test_unbounded_limit_cannot_blow_up_the_search_cache() -> None:
    """Regression: /search?limit=0 used to render ~19 MB and cache it."""
    from routes.web import search

    search.cache.clear()

    for q in ("a", "e", "i", "o", "u"):
        r = client.get(f"/search?q={q}&limit=0")
        assert r.status_code == 200
        assert len(r.content) < 2 * 1024 * 1024, "single response stayed bounded"

    assert search.cache.currsize <= search.cache.maxsize


def test_unhashable_parameter_falls_back_to_uncached() -> None:
    """An unhashable parameter must serve uncached, not raise.

    hashkey() builds its tuple lazily, so the TypeError surfaces only when the
    key is hashed; the guard has to force that itself.
    """
    calls = 0

    @cache_response
    async def endpoint(request: Request, q: Any) -> str:
        nonlocal calls
        calls += 1
        return "served"

    async def run() -> None:
        assert await endpoint(request=_fake_request(), q=["a", "b"]) == "served"
        assert await endpoint(request=_fake_request(), q={"a": 1}) == "served"

    asyncio.run(run())

    assert calls == 2
    assert len(endpoint.cache) == 0, "unhashable calls must not be cached"


def test_long_parameters_do_not_bloat_the_cache_key() -> None:
    """Keys must be bounded, since handlers truncate only after keying.

    A multi-kilobyte query would otherwise be retained verbatim in the key --
    memory the response-size budget cannot see.
    """
    from routes.core import MAX_KEY_ARG_LENGTH, _response_cache_key

    short = _response_cache_key((), {"q": "cat"})
    huge = _response_cache_key((), {"q": "x" * 8000})

    assert sum(len(str(p)) for p in huge) < 4 * MAX_KEY_ARG_LENGTH
    assert "x" * 200 not in str(huge), "raw query must not survive in the key"
    assert short != huge


def test_distinct_long_parameters_stay_distinct() -> None:
    """Digesting the key must not make different queries share a response."""
    from routes.core import _response_cache_key

    a = _response_cache_key((), {"q": "a" * 5000 + "ONE"})
    b = _response_cache_key((), {"q": "a" * 5000 + "TWO"})
    assert a != b
    assert hash(a) != hash(b)


def test_digest_cannot_collide_with_a_literal_string_argument() -> None:
    """A caller passing a digest-shaped string must not hit a digested key."""
    import hashlib

    from routes.core import _response_cache_key

    long_q = "z" * 500
    digest = hashlib.sha256(long_q.encode()).hexdigest()
    assert _response_cache_key((), {"q": long_q}) != _response_cache_key(
        (), {"q": digest}
    )
