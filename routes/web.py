"""
Web routes
"""

from typing import Optional
from datetime import datetime
import re
import aiofiles

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response, RedirectResponse

from .core import (
    TemplateResponse,
    cached_results,
    err_resp,
    KNOWN_MISSING_WORDS,
    num_entries,
    num_additions,
    additions,
    all_words,
    nonascii,
    num_nonascii,
    multiword,
    metadata,
    CAT2ENTRIES,
    CAT_TO_NAME,
    SEARCH_CACHE_SIZE,
    SMALL_CACHE_SIZE,
    e,
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
async def index(request: Request):
    """Index page"""
    return TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": f"{PROJECT.NAME} - {PROJECT.DESCRIPTION}",
        },
    )


@cache_response(SEARCH_CACHE_SIZE)
@router.get("/search", include_in_schema=False)
async def search(request: Request, q: Optional[str] = ""):
    """Return page with search results for query."""

    q = q.strip() if q else q
    if q and len(q) < 2:
        return err_resp("Query too short")

    title = PROJECT.NAME
    if q:
        results, exact = cached_results(q)

        async def _save_missing_word(word: str) -> None:
            """Save word to missing words list."""
            async with aiofiles.open("missing_words.txt", "a+") as file:
                await file.write(f"{word}\n")

        if not exact or not results:
            if re.match(r"^[a-zA-Z]+$", q) and q.lower() not in KNOWN_MISSING_WORDS:
                w = q[:100]
                await _save_missing_word(w)

        title = f'„{q}" - {PROJECT.NAME}'
    else:
        results = []
        exact = False

    return TemplateResponse(
        "result.html",
        {
            "request": request,
            "title": title,
            "q": q,
            "results": results,
            "exact": exact,
        },
    )


@cache_response(SEARCH_CACHE_SIZE)
@router.get("/item/{w}", include_in_schema=False)
@router.head("/item/{w}", include_in_schema=False)
async def item(request: Request, w: str):
    """Return page for a single dictionary word definition."""

    results, _ = cached_results(w, exact_match=True)
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
async def page(request: Request, n: str):
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
async def files(request: Request):
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
async def about(request: Request):
    """About page."""
    return TemplateResponse(
        "about.html",
        {
            "request": request,
            "title": f"Um - {PROJECT.NAME}",
            "num_entries": num_entries,
            "num_additions": num_additions,
            "entries_singular": sing_or_plur(num_entries),
            "additions_singular": sing_or_plur(num_additions),
            "additions_percentage": perc(num_additions, num_entries, icelandic=True),
        },
    )


@router.get("/zoega", include_in_schema=False)
@router.head("/zoega", include_in_schema=False)
@cache_response
async def zoega(request: Request):
    """Page with details about the Zoega dictionary."""
    return TemplateResponse(
        "zoega.html",
        {
            "request": request,
            "title": f"Orðabók Geirs T. Zoëga - {PROJECT.NAME}",
            "num_additions": num_additions,
        },
    )


@router.get("/english", include_in_schema=False)
@router.head("/english", include_in_schema=False)
@cache_response
async def english_redirect(request: Request):
    """Redirect to /english_icelandic_dictionary."""
    return RedirectResponse(url="/english_icelandic_dictionary", status_code=301)


@router.get("/english_icelandic_dictionary", include_in_schema=False)
@router.head("/english_icelandic_dictionary", include_in_schema=False)
@cache_response
async def english(request: Request):
    """English page."""
    return TemplateResponse(
        "english.html",
        {
            "request": request,
            "title": f"{PROJECT.NAME} - {PROJECT.DESCRIPTION_EN}",
            "num_entries": num_entries,
            "num_additions": num_additions,
            "entries_singular": num_entries,
            "additions_singular": num_additions,
            "additions_percentage": perc(num_additions, num_entries),
        },
    )


@router.get("/all", include_in_schema=False)
@router.head("/all", include_in_schema=False)
@cache_response
async def all(request: Request):
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
async def cat(request: Request, category: str):
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
async def capitalized(request: Request):
    """Page with links to all words that are capitalized."""
    capitalized = [e["word"] for e in e.read_all_capitalized()]
    return TemplateResponse(
        "capitalized.html",
        {
            "request": request,
            "title": f"Hástafir - {PROJECT.NAME}",
            "num_capitalized": len(capitalized),
            "capitalized": capitalized,
        },
    )


@router.get("/original", include_in_schema=False)
@router.head("/original", include_in_schema=False)
@cache_response
async def original(request: Request):
    """Page with links to all words that are original."""
    original = [e["word"] for e in e.read_all_original()]
    return TemplateResponse(
        "original.html",
        {
            "request": request,
            "title": f"Upprunaleg orð - {PROJECT.NAME}",
            "num_original": len(original),
            "original": original,
        },
    )


@router.get("/nonascii", include_in_schema=False)
@router.head("/nonascii", include_in_schema=False)
@cache_response
async def nonascii_route(request: Request):
    """Page with links to all words that contain non-ASCII characters."""
    return TemplateResponse(
        "nonascii.html",
        {
            "request": request,
            "title": f"Ekki ASCII - {PROJECT.NAME}",
            "num_nonascii": len(nonascii),
            "nonascii": nonascii,
        },
    )


@router.get("/multiword", include_in_schema=False)
@router.head("/multiword", include_in_schema=False)
@cache_response
async def multiword_route(request: Request):
    """Page with links to all entries with more than one word."""
    return TemplateResponse(
        "multiword.html",
        {
            "request": request,
            "title": f"Fleiri en eitt orð - {PROJECT.NAME}",
            "num_multiword": len(multiword),
            "multiword": multiword,
        },
    )


@router.get("/duplicates", include_in_schema=False)
@router.head("/duplicates", include_in_schema=False)
@cache_response
async def duplicates(request: Request):
    """Page with links to all words that are duplicates."""
    duplicates = [e["word"] for e in e.read_all_duplicates()]
    return TemplateResponse(
        "duplicates.html",
        {
            "request": request,
            "title": f"Samstæður - {PROJECT.NAME}",
            "num_duplicates": len(duplicates),
            "duplicates": duplicates,
        },
    )


@router.get("/additions", include_in_schema=False)
@router.head("/additions", include_in_schema=False)
@cache_response
async def additions_page(request: Request):
    """Page with links to all words that are additions to the original dictionary."""
    return TemplateResponse(
        "additions.html",
        {
            "request": request,
            "title": f"Viðbætur - {PROJECT.NAME}",
            "additions": additions,
            "num_additions": num_additions,
            "additions_percentage": perc(num_additions, num_entries),
        },
    )


@router.get("/stats", include_in_schema=False)
@router.head("/stats", include_in_schema=False)
@cache_response
async def stats(request: Request):
    """Page with statistics on dictionary entries."""

    no_uk_ipa = len(e.read_all_without_ipa(lang="uk"))
    no_us_ipa = len(e.read_all_without_ipa(lang="us"))
    no_page = len(e.read_all_with_no_page())
    num_capitalized = len(e.read_all_capitalized())
    num_duplicates = len(e.read_all_duplicates())
    num_multiword = len(e.read_all_with_multiple_words())

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
            "num_additions": num_additions,
            "perc_additions": perc(num_additions, num_entries),
            "num_original": num_entries - num_additions,
            "perc_original": perc(num_entries - num_additions, num_entries),
            "no_uk_ipa": no_uk_ipa,
            "no_us_ipa": no_us_ipa,
            "perc_no_uk_ipa": perc(no_uk_ipa, num_entries),
            "perc_no_us_ipa": perc(no_us_ipa, num_entries),
            "no_page": no_page,
            "perc_no_page": perc(no_page, num_entries),
            "num_capitalized": num_capitalized,
            "perc_capitalized": perc(num_capitalized, num_entries),
            "num_nonascii": num_nonascii,
            "perc_nonascii": perc(num_nonascii, num_entries),
            "num_multiword": num_multiword,
            "perc_multiword": perc(num_multiword, num_entries),
            "num_duplicates": num_duplicates,
            "perc_duplicates": perc(num_duplicates, num_entries),
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


@router.get("/robots.txt", include_in_schema=False)
@router.head("/robots.txt", include_in_schema=False)
@cache_response
async def robots(request: Request) -> Response:
    return TemplateResponse("robots.txt", {"request": request}, media_type="text/plain")
