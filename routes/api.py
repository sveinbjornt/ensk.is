"""
Ensk.is
API routes
"""

from fastapi import APIRouter, Request

from .core import (
    JSONResponse,
    cached_results,
    err_resp,
    SEARCH_CACHE_SIZE,
    SMALL_CACHE_SIZE,
    CAT_TO_NAME,
    metadata,
)
from dict import unpack_definition
from util import (
    cache_response,
    strip_html_from_string,
    strip_parentheses_from_string,
)

# Create router
router = APIRouter(prefix="/api")


@cache_response
@router.get("/metadata", operation_id="get_metadata")
async def api_metadata(request: Request) -> JSONResponse:
    """Return metadata about the English-Icelandic dictionary."""
    return JSONResponse(content=metadata)


DEFAULT_SUGGESTION_LIMIT = 10


@cache_response(SEARCH_CACHE_SIZE)
@router.get("/suggest/{q}")
async def api_suggest(
    request: Request, q: str, limit: int = DEFAULT_SUGGESTION_LIMIT
) -> JSONResponse:
    """Return autosuggestion results for partial string in input field."""
    results, _, _ = cached_results(q, exact_match=False, limit=limit)
    words = [x["word"] for x in results][:limit]
    return JSONResponse(content=words)


@cache_response(SEARCH_CACHE_SIZE)
@router.get("/search/{q}", operation_id="search_for_word")
async def api_search(request: Request, q: str) -> JSONResponse:
    """Return search results in JSON format from the English-Icelandic dictionary."""
    results, _, _ = cached_results(q)

    return JSONResponse(content={"results": results})


@cache_response(SEARCH_CACHE_SIZE)
@router.get("/item/{w}", operation_id="lookup_single_word")
async def api_item(request: Request, w: str) -> JSONResponse:
    """Return single English-Icelandic dictionary entry in JSON format."""
    ws = w.strip()

    results, exact, _ = cached_results(ws, exact_match=True)
    if not results or not exact:
        return err_resp(f"No entry found for '{ws}'")

    return JSONResponse(content=results[0])


@cache_response(SEARCH_CACHE_SIZE)
@router.get("/item/parsed/{w}", operation_id="lookup_single_word_parsed")
async def api_item_parsed(request: Request, w: str) -> JSONResponse:
    """Return single English-Icelandic dictionary entry in JSON format with parsed definition."""
    ws = w.strip()

    results, exact, _ = cached_results(ws, exact_match=True)
    if not results or not exact:
        return err_resp(f"No entry found for '{ws}'")

    result = results[0]

    # Parse definition string into components
    comp = unpack_definition(result["def"])

    # Translate category abbreviations to human-friendly words
    comp = {CAT_TO_NAME[k]: v for k, v in comp.items()}

    result["parsed"] = comp

    return JSONResponse(content=result)


@cache_response(SMALL_CACHE_SIZE)
@router.get("/item/parsed/many/", operation_id="lookup_many_words_parsed")
async def api_item_parsed_many(
    request: Request, q: str, strip_html: int = 0, strip_parentheses: int = 0
) -> JSONResponse:
    """Return multiple English-Icelandic dictionary entries in JSON format with
    parsed definitions. The q parameter should be a list of comma-separated terms.
    Optionally, strip HTML tags and all text within parentheses."""
    q = q.strip()

    words = [w.strip() for w in q.split(",")]

    def _process_item(s: str) -> str:
        """Process a single item by stripping HTML and parentheses."""
        if strip_html:
            s = strip_html_from_string(s)
        if strip_parentheses:
            s = strip_parentheses_from_string(s)
        return s.strip()

    res = {}
    for w in words:
        results, exact, _ = cached_results(w, exact_match=True)
        if not results or not exact:
            continue
        result = results[0]
        # Parse definition string into components
        comp = unpack_definition(result["def"])
        # Translate category abbreviations to human-friendly words
        comp = {CAT_TO_NAME[k]: [_process_item(i) for i in v] for k, v in comp.items()}
        res[w] = comp

    return JSONResponse(content=res)
