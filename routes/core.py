"""
Ensk.is
Core utilities and shared data for routes
"""

import asyncio
import re
from collections.abc import Awaitable, Callable
from functools import lru_cache, wraps
from typing import Any, Protocol, cast, overload

import orjson
from cachetools import LRUCache
from cachetools.keys import hashkey
from fastapi.responses import JSONResponse as FastAPIJSONResponse
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import Response

from db import EnskDatabase
from dict import CATEGORIES
from settings import PROJECT
from util import is_ascii, read_wordlist


# Custom JSON response class that uses ultrafast orjson for serialization
class CustomJSONResponse(FastAPIJSONResponse):
    """JSON response using the high-performance orjson library for serialization."""

    def render(self, content: Any) -> bytes:
        """Render content to bytes using orjson."""
        return orjson.dumps(content)


JSONResponse = CustomJSONResponse

# Set up templates
TEMPLATES_DIR = "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)
TemplateResponse = templates.TemplateResponse

# Initialize database singleton
edb = EnskDatabase(read_only=True)

# Read everything we want from the database into memory
entries = edb.read_all_entries()
num_entries = len(entries)

all_words = [e["word"] for e in entries]
all_words_set = frozenset(all_words)

original_entries = [e["word"] for e in edb.read_all_original()]
num_original_entries = len(original_entries)

additional_entries = [a["word"] for a in edb.read_all_additions()]
num_additional_entries = len(additional_entries)

nonascii_entries = [e["word"] for e in entries if not is_ascii(e["word"])]
num_nonascii_entries = len(nonascii_entries)

multiword_entries = [e["word"] for e in edb.read_all_with_multiple_words()]
num_multiword_entries = len(multiword_entries)

capitalized_entries = [e["word"] for e in edb.read_all_capitalized()]
num_capitalized_entries = len(capitalized_entries)

duplicate_entries = [e["word"] for e in edb.read_all_duplicates()]
num_duplicate_entries = len(duplicate_entries)

no_uk_ipa_entries = [e["word"] for e in edb.read_all_without_ipa(lang="uk")]
num_no_uk_ipa_entries = len(no_uk_ipa_entries)

no_us_ipa_entries = [e["word"] for e in edb.read_all_without_ipa(lang="us")]
num_no_us_ipa_entries = len(no_us_ipa_entries)

no_page_entries = [e["word"] for e in edb.read_all_with_no_page()]
num_no_page_entries = len(no_page_entries)

metadata = edb.read_metadata()

# Get all entries in each category and store in dict
CAT2ENTRIES = {}
for c in CATEGORIES:
    cs = c.rstrip(".")
    CAT2ENTRIES[cs] = edb.read_all_in_wordcat(cs)

SEARCH_CACHE_SIZE = 1000  # entries, for the cached_results() lookup cache

# Response caches are bounded in BYTES, not in number of entries. A single
# rendered page can be megabytes, so an entry count is not a memory bound:
# 1000 search responses at ~16 MB each would be ~13 GB.
DEFAULT_CACHE_BYTES = 8 * 1024 * 1024  # 8 MB
SEARCH_CACHE_BYTES = 16 * 1024 * 1024  # 16 MB
SMALL_CACHE_BYTES = 4 * 1024 * 1024  # 4 MB


# Per-request objects that FastAPI injects into endpoint signatures. These
# identify the caller, not the response content, and must be kept out of the
# cache key: Request is hashable only by identity, so including it makes every
# lookup a miss and lets the cache grow once per request, forever.
_PER_REQUEST_TYPES = (Request, Response, BackgroundTasks)


def _response_cache_key(args: tuple, kwargs: dict[str, Any]) -> tuple:
    """Build a cache key from an endpoint's own path/query parameters."""
    return hashkey(
        *(a for a in args if not isinstance(a, _PER_REQUEST_TYPES)),
        **{k: v for k, v in kwargs.items() if not isinstance(v, _PER_REQUEST_TYPES)},
    )


# Charged per cache entry on top of its body, so that entries with an empty
# body (redirects) still count against the budget, and to cover the context a
# template response keeps alive alongside its rendered bytes.
_ENTRY_OVERHEAD_BYTES = 512


def _response_size(value: Any) -> int:
    """Approximate the retained size of a cached response, in bytes.

    Based on the rendered body, which dominates. This is a floor, not an exact
    figure: a template response also retains its context.
    """
    body = getattr(value, "body", None)
    return _ENTRY_OVERHEAD_BYTES + (len(body) if body is not None else 0)


AsyncEndpoint = Callable[..., Awaitable[Any]]


class CachedEndpoint(Protocol):
    """An endpoint wrapped by cache_response, exposing its own LRU cache."""

    cache: LRUCache

    def __call__(self, *args: Any, **kwargs: Any) -> Awaitable[Any]: ...


@overload
def cache_response(max_bytes: AsyncEndpoint) -> CachedEndpoint: ...


@overload
def cache_response(
    max_bytes: int = DEFAULT_CACHE_BYTES,
) -> Callable[[AsyncEndpoint], CachedEndpoint]: ...


def cache_response(
    max_bytes: int | AsyncEndpoint = DEFAULT_CACHE_BYTES,
) -> CachedEndpoint | Callable[[AsyncEndpoint], CachedEndpoint]:
    """Decorator that caches the responses of an async FastAPI endpoint.

    Usable bare (``@cache_response``) or with an explicit budget
    (``@cache_response(SMALL_CACHE_BYTES)``). Each decorated endpoint gets its
    own LRU cache, keyed on the endpoint's own parameters only -- the injected
    Request is excluded, since it would otherwise make every lookup a miss.

    The cache is bounded by the total size of the responses it holds, not by
    their number, so an endpoint that can render a large page cannot grow past
    its budget. A response bigger than the whole budget is served but not
    stored, rather than evicting everything else.

    Only successful responses are stored; exceptions (such as the HTTPException
    raised for a missing entry) propagate uncached. The lock is held across the
    call so that concurrent requests for the same uncached key render once
    rather than piling up on an expensive template.

    Responses are reused across requests, so this must only be applied to
    endpoints whose output depends solely on their parameters. Do not use it for
    responses that carry per-request state -- notably FileResponse, which
    latches Content-Length and ETag onto the object on first send.
    """
    func: AsyncEndpoint | None = None
    budget = DEFAULT_CACHE_BYTES
    if callable(max_bytes):  # Bare @cache_response, no parentheses
        func = max_bytes
    else:
        budget = max_bytes

    def decorator(f: AsyncEndpoint) -> CachedEndpoint:
        cache: LRUCache = LRUCache(maxsize=budget, getsizeof=_response_size)
        lock = asyncio.Lock()

        @wraps(f)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                key = _response_cache_key(args, kwargs)
            except TypeError:
                # Unhashable parameter: serve uncached rather than fail
                return await f(*args, **kwargs)

            async with lock:
                if key in cache:
                    return cache[key]
                result = await f(*args, **kwargs)
                try:
                    cache[key] = result
                except ValueError:
                    # Response alone exceeds the budget; serve it uncached
                    pass
                return result

        wrapper.cache = cache  # type: ignore[attr-defined]
        return cast(CachedEndpoint, wrapper)

    return decorator(func) if func is not None else decorator


KNOWN_MISSING_WORDS = frozenset(read_wordlist("data/missing.txt"))

DEFAULT_SEARCH_LIMIT = 50  # Default limit for search results
MAX_SEARCH_LIMIT = 200  # Hard ceiling on caller-supplied result limits


# Clear the database reference to free memory
# It will not be needed after this point
edb.close()
del edb


def err_resp(msg: str, status_code: int = 200) -> JSONResponse:
    """Return JSON error message."""
    return JSONResponse(content={"error": True, "errmsg": msg}, status_code=status_code)


def _prepare_item(item: dict[str, Any]) -> dict[str, Any]:
    """Prepare a raw database entry for consumption by all routes.
    Parses synonyms/antonyms, filters syllables, generates audio URLs.
    No HTML formatting."""
    w = item["word"]

    # Replace ~ symbol with English word
    d = item["definition"].replace("~", w)

    # Only show syllables if they are different from the word itself
    syll = item.get("syllables", "")
    syllables = syll if len(syll) != len(w) else ""

    # Generate URLs to audio files
    audiofn = w.replace(" ", "_")
    audio_url_uk = f"{PROJECT.BASE_URL}/static/audio/dict/uk/{audiofn}.mp3"
    audio_url_us = f"{PROJECT.BASE_URL}/static/audio/dict/us/{audiofn}.mp3"

    # Original dictionary page image URL and page URL
    p = item["page_num"]
    page_image = f"{PROJECT.BASE_URL}/static/img/pages/{p - 1:03}.jpg" if p > 0 else ""
    page_url = f"{PROJECT.BASE_URL}/page/{p}" if p > 0 else ""

    # Synonyms
    synonyms_str = item.get("synonyms", "")
    synonyms = synonyms_str.split(",") if synonyms_str else []

    # Antonyms
    antonyms_str = item.get("antonyms", "")
    antonyms = antonyms_str.split(",") if antonyms_str else []

    return {
        "word": w,
        "def": d,
        "syllables": syllables,
        "ipa_uk": item.get("ipa_uk", ""),
        "ipa_us": item.get("ipa_us", ""),
        "audio_uk": audio_url_uk,
        "audio_us": audio_url_us,
        "page_num": p,
        "page_image": page_image,
        "page_url": page_url,
        "synonyms": synonyms,
        "antonyms": antonyms,
    }


LINK_FORMAT_REGEX = re.compile(r"%\[(.+?)\]%")


def format_def_html(s: str) -> str:
    """Apply HTML formatting to a definition string."""

    # Replace %[word]% with link to intra-dictionary entry
    s = LINK_FORMAT_REGEX.sub(
        rf"<strong><em><a href='{PROJECT.BASE_URL}/item/\1'>\1</a></em></strong>", s
    )

    # Italicize English words
    s = s.replace("[", "<em>")
    s = s.replace("]", "</em>")

    return s


def format_item_html(item: dict[str, Any]) -> dict[str, Any]:
    """Add HTML formatting to a prepared dictionary entry definition for web display."""
    item = dict(item)  # Don't mutate the cached original
    item["def"] = format_def_html(item["def"])

    return item


def _results(
    q: str, exact_match: bool = False, limit: int = DEFAULT_SEARCH_LIMIT
) -> tuple[list, bool, bool]:
    """Return processed search results for a bareword text query."""
    if not q:
        return ([], False, False)

    equal = []
    swith = []
    ewith = []
    other = []

    ql = q.lower()
    exact_match_found = False

    # Collect all matching entries
    for k in entries:
        kl = k["word"].lower()

        if exact_match:
            # In exact match mode, only collect case-sensitive exact matches
            if q == k["word"]:
                equal.append(k)
                exact_match_found = True
        else:
            # In substring mode, categorize by match type
            if ql in kl:
                if kl == ql:
                    equal.append(k)
                    exact_match_found = True
                elif kl.startswith(ql):
                    swith.append(k)
                elif kl.endswith(ql):
                    ewith.append(k)
                else:
                    other.append(k)

    # Sort each category
    equal.sort(key=lambda d: d["word"].lower())
    swith.sort(key=lambda d: d["word"].lower())
    ewith.sort(key=lambda d: d["word"].lower())
    other.sort(key=lambda d: d["word"].lower())

    # Assemble results in priority order: exact, startswith, endswith, contains
    all_results = equal + swith + ewith + other

    # Apply limit if specified
    if limit > 0:
        limited_results = all_results[:limit]
        has_more = len(all_results) > limit
    else:
        limited_results = all_results
        has_more = False

    # If no results found, try removing trailing 's' from query
    # and search again since it might be a plural form
    if (
        not exact_match
        and len(limited_results) == 0
        and len(q) >= 3
        and q.endswith("s")
    ):
        return _results(q[:-1], exact_match=True, limit=limit)

    # Prepare final results (no HTML formatting)
    prepared_results = [_prepare_item(item) for item in limited_results]

    return prepared_results, exact_match_found, has_more


def clamp_search_limit(limit: int | None) -> int:
    """Clamp a caller-supplied result limit into a sane range.

    A non-positive limit used to mean "no limit", which let a single request
    render every matching entry -- ~19 MB of HTML for a one-letter query, and
    the same again retained in the response cache.
    """
    if limit is None or limit <= 0:
        return DEFAULT_SEARCH_LIMIT
    return min(limit, MAX_SEARCH_LIMIT)


def cached_results(
    q: str, exact_match: bool = False, limit: int = DEFAULT_SEARCH_LIMIT
) -> tuple[list, bool, bool]:
    """Return cached search results for a bareword text query."""
    # Clamp before the cache key is formed, so out-of-range limits cannot
    # each occupy their own entry.
    return _cached_results(q, exact_match, clamp_search_limit(limit))


@lru_cache(maxsize=SEARCH_CACHE_SIZE)
def _cached_results(q: str, exact_match: bool, limit: int) -> tuple[list, bool, bool]:
    """Memoized backend for cached_results(); assumes an already-clamped limit."""
    return _results(q, exact_match, limit)
