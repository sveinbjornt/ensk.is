"""
Ensk.is
Web routes
"""

from typing import Optional
from datetime import datetime
import re
import aiofiles
import aiofiles.os

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response, RedirectResponse

from .core import (
    TemplateResponse,
    cached_results,
    KNOWN_MISSING_WORDS,
    DEFAULT_SEARCH_LIMIT,
    num_entries,
    all_words,
    original_entries,
    num_original_entries,
    additional_entries,
    num_additional_entries,
    nonascii_entries,
    num_nonascii_entries,
    multiword_entries,
    num_multiword_entries,
    capitalized_entries,
    num_capitalized_entries,
    duplicate_entries,
    num_duplicate_entries,
    # no_uk_ipa_entries,
    num_no_uk_ipa_entries,
    # no_us_ipa_entries,
    num_no_us_ipa_entries,
    # no_page_entries,
    num_no_page_entries,
    metadata,
    CAT2ENTRIES,
    CAT_TO_NAME,
    SEARCH_CACHE_SIZE,
    SMALL_CACHE_SIZE,
)
from info import PROJECT
from dict import unpack_definition, linked_synonyms_for_word
from util import (
    icelandic_human_size,
    perc,
    sing_or_plur,
    cache_response,
)

# Create router
router = APIRouter()


@router.get("/", include_in_schema=False)
@router.head("/", include_in_schema=False)
@cache_response
async def index(request: Request) -> Response:
    """Index page"""
    return TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": f"{PROJECT.NAME} - {PROJECT.DESCRIPTION}",
        },
    )


MISSING_WORD_MAXLEN = 100
MISSING_WORDS_FILE = "missing_words.txt"
MISSING_WORDS_MAX_SIZE = 1_000_000  # 1 MB limit


async def _save_missing_word(word: str) -> None:
    """Save word to missing words list."""
    try:
        size = await aiofiles.os.path.getsize(MISSING_WORDS_FILE)
        if size > MISSING_WORDS_MAX_SIZE:  # 1 MB limit
            return
    except FileNotFoundError:
        pass  # File doesn't exist yet, that's OK

    try:
        async with aiofiles.open(MISSING_WORDS_FILE, "a+") as file:
            await file.write(f"{word[:MISSING_WORD_MAXLEN]}\n")  # 100 char limit
    except Exception:
        pass  # Fail silently if we can't write


@cache_response(SEARCH_CACHE_SIZE)
@router.get("/search", include_in_schema=False)
async def search(
    request: Request, q: Optional[str] = "", limit: Optional[int] = DEFAULT_SEARCH_LIMIT
) -> Response:
    """Return page with search results for query."""

    q = q.strip() if q else q

    title = PROJECT.NAME
    if q:
        results, exact, has_more = cached_results(q, exact_match=False, limit=limit)

        # If a search word might be missing, log it to a file but
        # only if it is a single word and not a known missing word
        if not exact or not results:
            if re.match(r"^[a-zA-Z]+$", q) and q.lower() not in KNOWN_MISSING_WORDS:
                await _save_missing_word(q)

        title = f'„{q}" - {PROJECT.NAME}'
    else:
        results = []
        exact = False
        has_more = False

    return TemplateResponse(
        "result.html",
        {
            "request": request,
            "title": title,
            "q": q,
            "results": results,
            "exact": exact,
            "limit": limit,
            "has_more": has_more,
        },
    )


@cache_response(SEARCH_CACHE_SIZE)
@router.get("/item/{w}", include_in_schema=False)
@router.head("/item/{w}", include_in_schema=False)
async def item(request: Request, w: str) -> Response:
    """Return page for a single dictionary word definition."""

    results, _, _ = cached_results(w, exact_match=True)
    if not results:
        raise HTTPException(status_code=404, detail="Síða fannst ekki")

    # Parse definition string into components
    comp = unpack_definition(results[0]["def"])

    # Translate category abbreviations to human-friendly words
    comp = {CAT_TO_NAME[k]: v for k, v in comp.items()}

    synonyms = linked_synonyms_for_word(w, all_words)

    return TemplateResponse(
        "item.html",
        {
            "request": request,
            "title": f"{w} - {PROJECT.NAME}",
            "q": w,
            "results": results,
            "word": w,
            "comp": comp,
            "synonyms": synonyms,
        },
    )


@cache_response(SMALL_CACHE_SIZE)
@router.get("/page/{n}", include_in_schema=False)
@router.head("/page/{n}", include_in_schema=False)
async def page(request: Request, n: str) -> Response:
    """Return page for a single dictionary page image."""
    try:
        page_num = int(n)
    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid page number")
    if page_num < 1 or page_num > 707:
        raise HTTPException(status_code=404, detail="Síða fannst ekki")

    pad = page_num - 1

    return TemplateResponse(
        "page.html",
        {
            "request": request,
            "title": f"Zoëga bls. {page_num} - {PROJECT.NAME}",
            "n": page_num,
            "npad": f"{pad:03}",
        },
    )


@router.get("/files", include_in_schema=False)
@router.head("/files", include_in_schema=False)
@cache_response
async def files(request: Request) -> Response:
    """Page containing download links to data files."""

    sqlite_size = icelandic_human_size(
        f"static/files/{PROJECT.BASE_DATA_FILENAME}.db.zip"
    )
    csv_size = icelandic_human_size(
        f"static/files/{PROJECT.BASE_DATA_FILENAME}.csv.zip"
    )
    json_size = icelandic_human_size(
        f"static/files/{PROJECT.BASE_DATA_FILENAME}.json.zip"
    )
    text_size = icelandic_human_size(
        f"static/files/{PROJECT.BASE_DATA_FILENAME}.txt.zip"
    )
    try:
        pdf_size = icelandic_human_size(
            f"static/files/{PROJECT.BASE_DATA_FILENAME}.pdf"
        )
    except FileNotFoundError:
        pdf_size = "ekki til"

    try:
        apple_dictionary_size = icelandic_human_size(
            f"static/files/{PROJECT.BASE_DATA_FILENAME}.dictionary.zip"
        )
    except FileNotFoundError:
        apple_dictionary_size = "ekki til"

    date_object = datetime.fromisoformat(metadata.get("generation_date", ""))
    formatted_date = date_object.strftime("%d/%m/%Y")

    return TemplateResponse(
        "files.html",
        {
            "request": request,
            "title": f"Gögn - {PROJECT.NAME}",
            "sqlite_size": sqlite_size,
            "csv_size": csv_size,
            "json_size": json_size,
            "text_size": text_size,
            "pdf_size": pdf_size,
            "apple_dictionary_size": apple_dictionary_size,
            "last_updated": formatted_date,
        },
    )


@router.get("/about", include_in_schema=False)
@router.head("/about", include_in_schema=False)
@cache_response
async def about(request: Request) -> Response:
    """About page."""
    return TemplateResponse(
        "about.html",
        {
            "request": request,
            "title": f"Um - {PROJECT.NAME}",
            "num_entries": num_entries,
            "num_additions": num_additional_entries,
            "entries_singular": sing_or_plur(num_entries),
            "additions_singular": sing_or_plur(num_additional_entries),
            "additions_percentage": perc(
                num_additional_entries, num_entries, icelandic=True
            ),
        },
    )


@router.get("/zoega", include_in_schema=False)
@router.head("/zoega", include_in_schema=False)
@cache_response
async def zoega(request: Request) -> Response:
    """Page with details about the Zoega dictionary."""
    return TemplateResponse(
        "zoega.html",
        {
            "request": request,
            "title": f"Orðabók Geirs T. Zoëga - {PROJECT.NAME}",
            "num_additions": num_additional_entries,
        },
    )


@router.get("/english", include_in_schema=False)
@router.head("/english", include_in_schema=False)
@cache_response
async def english_redirect(request: Request) -> Response:
    """Redirect to /english_icelandic_dictionary."""
    return RedirectResponse(url="/english_icelandic_dictionary", status_code=301)


@router.get("/english_icelandic_dictionary", include_in_schema=False)
@router.head("/english_icelandic_dictionary", include_in_schema=False)
@cache_response
async def english(request: Request) -> Response:
    """English page."""
    return TemplateResponse(
        "english.html",
        {
            "request": request,
            "title": f"{PROJECT.NAME} - {PROJECT.DESCRIPTION_EN}",
            "num_entries": num_entries,
            "num_additions": num_additional_entries,
            "entries_singular": num_entries,
            "additions_singular": num_additional_entries,
            "additions_percentage": perc(num_additional_entries, num_entries),
        },
    )


@router.get("/all", include_in_schema=False)
@router.head("/all", include_in_schema=False)
@cache_response
async def all(request: Request) -> Response:
    """Page with links to all entries."""
    return TemplateResponse(
        "all.html",
        {
            "request": request,
            "title": f"Öll orðin - {PROJECT.NAME}",
            "num_words": len(all_words),
            "words": all_words,
        },
    )


@cache_response(SMALL_CACHE_SIZE)
@router.get("/cat/{category}", include_in_schema=False)
@router.head("/cat/{category}", include_in_schema=False)
async def cat(request: Request, category: str) -> Response:
    """Page with links to all entries in the given category."""
    entries = CAT2ENTRIES.get(category, [])
    words = [e["word"] for e in entries]
    return TemplateResponse(
        "cat.html",
        {
            "request": request,
            "title": f"Öll orð í flokknum {category} - {PROJECT.NAME}",
            "words": words,
            "category": category,
        },
    )


@router.get("/capitalized", include_in_schema=False)
@router.head("/capitalized", include_in_schema=False)
@cache_response
async def capitalized(request: Request) -> Response:
    """Page with links to all words that are capitalized."""
    return TemplateResponse(
        "capitalized.html",
        {
            "request": request,
            "title": f"Hástafir - {PROJECT.NAME}",
            "num_capitalized": num_capitalized_entries,
            "capitalized": capitalized_entries,
        },
    )


@router.get("/original", include_in_schema=False)
@router.head("/original", include_in_schema=False)
@cache_response
async def original(request: Request) -> Response:
    """Page with links to all words that are original."""
    return TemplateResponse(
        "original.html",
        {
            "request": request,
            "title": f"Upprunaleg orð - {PROJECT.NAME}",
            "num_original": num_original_entries,
            "original": original_entries,
        },
    )


@router.get("/nonascii", include_in_schema=False)
@router.head("/nonascii", include_in_schema=False)
@cache_response
async def nonascii_route(request: Request) -> Response:
    """Page with links to all words that contain non-ASCII characters."""
    return TemplateResponse(
        "nonascii.html",
        {
            "request": request,
            "title": f"Ekki ASCII - {PROJECT.NAME}",
            "num_nonascii": num_nonascii_entries,
            "nonascii": nonascii_entries,
        },
    )


@router.get("/multiword", include_in_schema=False)
@router.head("/multiword", include_in_schema=False)
@cache_response
async def multiword_route(request: Request) -> Response:
    """Page with links to all entries with more than one word."""
    return TemplateResponse(
        "multiword.html",
        {
            "request": request,
            "title": f"Fleiri en eitt orð - {PROJECT.NAME}",
            "num_multiword": num_multiword_entries,
            "multiword": multiword_entries,
        },
    )


@router.get("/duplicates", include_in_schema=False)
@router.head("/duplicates", include_in_schema=False)
@cache_response
async def duplicates(request: Request) -> Response:
    """Page with links to all words that are duplicates."""
    return TemplateResponse(
        "duplicates.html",
        {
            "request": request,
            "title": f"Samstæður - {PROJECT.NAME}",
            "num_duplicates": num_duplicate_entries,
            "duplicates": duplicate_entries,
        },
    )


@router.get("/additions", include_in_schema=False)
@router.head("/additions", include_in_schema=False)
@cache_response
async def additions_page(request: Request) -> Response:
    """Page with links to all words that are additions to the original dictionary."""
    return TemplateResponse(
        "additions.html",
        {
            "request": request,
            "title": f"Viðbætur - {PROJECT.NAME}",
            "additions": additional_entries,
            "num_additions": num_additional_entries,
            "additions_percentage": perc(num_additional_entries, num_entries),
        },
    )


@router.get("/stats", include_in_schema=False)
@router.head("/stats", include_in_schema=False)
@cache_response
async def stats(request: Request) -> Response:
    """Page with statistics on dictionary entries."""

    wordstats = {}
    for c in CAT2ENTRIES:
        cat = c.rstrip(".")
        wordstats[cat] = {}
        wordstats[cat]["num"] = len(CAT2ENTRIES[c])
        wordstats[cat]["perc"] = perc(wordstats[cat]["num"], num_entries)

    return TemplateResponse(
        "stats.html",
        {
            "request": request,
            "title": f"Tölfræði - {PROJECT.NAME}",
            "num_entries": num_entries,
            "num_additions": num_additional_entries,
            "perc_additions": perc(num_additional_entries, num_entries),
            "num_original": num_entries - num_additional_entries,
            "perc_original": perc(num_entries - num_additional_entries, num_entries),
            "no_uk_ipa": num_no_uk_ipa_entries,
            "no_us_ipa": num_no_us_ipa_entries,
            "perc_no_uk_ipa": perc(num_no_uk_ipa_entries, num_entries),
            "perc_no_us_ipa": perc(num_no_us_ipa_entries, num_entries),
            "no_page": num_no_page_entries,
            "perc_no_page": perc(num_no_page_entries, num_entries),
            "num_capitalized": num_capitalized_entries,
            "perc_capitalized": perc(num_capitalized_entries, num_entries),
            "num_nonascii": num_nonascii_entries,
            "perc_nonascii": perc(num_nonascii_entries, num_entries),
            "num_multiword": num_multiword_entries,
            "perc_multiword": perc(num_multiword_entries, num_entries),
            "num_duplicates": num_duplicate_entries,
            "perc_duplicates": perc(num_duplicate_entries, num_entries),
            "wordstats": wordstats,
        },
    )


@router.get("/sitemap.xml", include_in_schema=False)
@router.head("/sitemap.xml", include_in_schema=False)
@cache_response
async def sitemap(request: Request) -> Response:
    return TemplateResponse(
        "sitemap.xml",
        {"request": request, "words": all_words},
        media_type="application/xml",
    )
