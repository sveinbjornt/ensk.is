#!/usr/bin/env python3
"""

Ensk.is - Free and open English-Icelandic dictionary

Copyright (c) 2021-2025 Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>

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


FastAPI web application.

"""

from typing import Any

import re
import aiofiles

from functools import lru_cache
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import (
    Response,
    RedirectResponse,
    JSONResponse as FastAPIJSONResponse,
)
from starlette.middleware.base import BaseHTTPMiddleware
import orjson

from db import EnskDatabase
from dict import read_wordlist, unpack_definition
from info import PROJECT
from util import icelandic_human_size, perc, is_ascii, sing_or_plur, cache_response

# Create app
app = FastAPI(
    title=PROJECT.NAME,
    description=PROJECT.DESCRIPTION,
    version=PROJECT.VERSION,
    contact={
        "name": PROJECT.EDITOR,
        "email": PROJECT.EMAIL,
    },
    license_info={
        "name": PROJECT.LICENSE,
    },
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")
TemplateResponse = templates.TemplateResponse

# Initialize database singleton
e = EnskDatabase(read_only=True)

# Read everything we want from the database into memory
entries = e.read_all_entries()
num_entries = len(entries)
all_words = [e["word"] for e in entries]
additions = [a["word"] for a in e.read_all_additions()]
num_additions = len(additions)
nonascii = [e["word"] for e in entries if not is_ascii(e["word"])]
num_nonascii = len(nonascii)
multiword = [e["word"] for e in entries if " " in e["word"]]
num_multiword = len(multiword)
metadata = e.read_metadata()

CATEGORIES = read_wordlist("data/catwords.txt")
KNOWN_MISSING_WORDS = read_wordlist("missing.txt")

SEARCH_CACHE_SIZE = 1000
SMALL_CACHE_SIZE = 100


# Get all entries in each category and store in dict
CAT2ENTRIES = {}
for c in CATEGORIES:
    cs = c.rstrip(".")
    CAT2ENTRIES[cs] = e.read_all_in_wordcat(cs)


# Create a middleware class to set custom headers
class AddCustomHeaderMiddleware(BaseHTTPMiddleware):
    """Add custom headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=86400"
        else:
            response.headers["Content-Language"] = "is, en"
        return response


app.add_middleware(AddCustomHeaderMiddleware)


# Custom JSON response class that uses ultrafast orjson for serialization
class CustomJSONResponse(FastAPIJSONResponse):
    """JSON response using the high-performance orjson library to serialize the data."""

    def render(self, content: Any) -> bytes:
        return orjson.dumps(content)


JSONResponse = CustomJSONResponse


def _err(msg: str) -> JSONResponse:
    """Return JSON error message."""
    return JSONResponse(content={"error": True, "errmsg": msg})


MAX_DEF_LENGTH = 200


def _format_item(item: dict[str, Any]) -> dict[str, Any]:
    """Format dictionary entry for presentation."""
    w = item["word"]
    x = item["definition"]

    # if len(item["definition"]) > MAX_DEF_LENGTH:
    #     x = item["definition"][:MAX_DEF_LENGTH] + "..."

    # Replace ~ symbol with English word
    x = x.replace("~", w)

    # Replace %[word]% with link to intra-dictionary entry
    rx = re.compile(r"%\[(.+?)\]%")
    x = rx.sub(
        rf"<strong><em><a href='{PROJECT.BASE_URL}/item/\1'>\1</a></em></strong>", x
    )

    # Italicize English words
    x = x.replace("[", "<em>")
    x = x.replace("]", "</em>")

    # Phonetic spelling
    ipa_uk = item.get("ipa_uk", "")
    ipa_us = item.get("ipa_us", "")

    # Generate URLs to audio files
    audiofn = w.replace(" ", "_")
    audio_url_uk = f"{PROJECT.BASE_URL}/static/audio/dict/uk/{audiofn}.mp3"
    audio_url_us = f"{PROJECT.BASE_URL}/static/audio/dict/us/{audiofn}.mp3"

    # Original dictionary page
    p = item["page_num"]
    p_url = f"{PROJECT.BASE_URL}/page/{p}" if p > 0 else ""

    # Create item dict
    item = {
        "word": w,
        "def": x,
        "ipa_uk": ipa_uk,
        "ipa_us": ipa_us,
        "audio_uk": audio_url_uk,
        "audio_us": audio_url_us,
        "page_num": p,
        "page_url": p_url,
    }
    return item


def _results(q: str, exact_match: bool = False) -> tuple[list, bool]:
    """Return processed search results for a bareword textual query."""
    if not q:
        return [], False

    equal = []
    swith = []
    ewith = []
    other = []

    ql = q.lower()
    for k in entries:
        kl = k["word"].lower()
        if (exact_match and ql == kl) or (
            not exact_match and ql.lower() in k["word"].lower()
        ):
            item = _format_item(k)
            lw = item["word"].lower()
            lq = q.lower()
            if lw == lq:
                equal.append(item)
            elif lw.startswith(lq):
                swith.append(item)
            elif lw.endswith(lq):
                ewith.append(item)
            else:
                other.append(item)

    exact_match_found: bool = len(equal) > 0

    equal.sort(key=lambda d: d["word"].lower())
    swith.sort(key=lambda d: d["word"].lower())
    ewith.sort(key=lambda d: d["word"].lower())
    other.sort(key=lambda d: d["word"].lower())

    results = [*equal, *swith, *ewith, *other]

    # If no results found, try removing trailing 's' from query
    # and search again since it might be a plural form
    if len(results) == 0 and exact_match is False and len(q) >= 3 and q.endswith("s"):
        return _results(q[:-1], exact_match=True)

    return results, exact_match_found


@lru_cache(maxsize=SEARCH_CACHE_SIZE)
def _cached_results(q: str, exact_match: bool = False):
    return _results(q, exact_match)


@app.exception_handler(404)
def not_found_exception_handler(request: Request, exc: HTTPException):
    return TemplateResponse(
        "404.html",
        {"request": request, "title": "404 - Síða fannst ekki"},
        status_code=404,
    )


@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
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


@app.get("/search", include_in_schema=False)  # type: ignore
@cache_response(SEARCH_CACHE_SIZE)
async def search(request: Request, q: str):
    """Return page with search results for query."""

    q = q.strip()
    if len(q) < 2:
        return _err("Query too short")

    results, exact = _cached_results(q)

    async def _save_missing_word(word: str) -> None:
        """Save word to missing words list."""
        async with aiofiles.open("missing_words.txt", "a+") as file:
            await file.write(f"{word}\n")

    if not exact or not results:
        if re.match(r"^[a-zA-Z]+$", q) and q.lower() not in KNOWN_MISSING_WORDS:
            w = q[:100]
            await _save_missing_word(w)

    return TemplateResponse(
        "result.html",
        {
            "request": request,
            "title": f"Niðurstöður fyrir „{q}“ - {PROJECT.NAME}",
            "q": q,
            "results": results,
            "exact": exact,
        },
    )


# To JSON configuration file?
CAT_TO_NAME = {
    "n.": "nafnorð",
    "nft.": "nafnorð (í fleirtölu)",
    "l.": "lýsingarorð",
    "s.": "sagnorð",
    "ao.": "atviksorð",
    "fsk.": "forskeyti",
    "st.": "samtenging",
    "gr.": "greinir",
    "fs.": "forsetning",
    "uh.": "upphrópun",
    "fn.": "fornafn",
    "stytt.": "stytting",
    "sks.": "skammstöfun",
}


@app.get("/item/{w}", include_in_schema=False)  # type: ignore
@app.head("/item/{w}", include_in_schema=False)  # type: ignore
@cache_response(SEARCH_CACHE_SIZE)
async def item(request: Request, w: str):
    """Return page for a single dictionary word definition."""

    results, _ = _cached_results(w, exact_match=True)
    if not results:
        raise HTTPException(status_code=404, detail="Síða fannst ekki")

    # Parse definition string into components
    comp = unpack_definition(results[0]["def"])

    # Translate category abbreviations to human-friendly words
    comp = {CAT_TO_NAME[k]: v for k, v in comp.items()}

    return TemplateResponse(
        "item.html",
        {
            "request": request,
            "title": f"{w} - {PROJECT.NAME}",
            "q": w,
            "results": results,
            "word": w,
            "comp": comp,
        },
    )


@app.get("/page/{n}", include_in_schema=False)  # type: ignore
@app.head("/page/{n}", include_in_schema=False)  # type: ignore
@cache_response(SMALL_CACHE_SIZE)
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


@app.get("/files", include_in_schema=False)
@app.head("/files", include_in_schema=False)
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
            "last_updated": formatted_date,
        },
    )


@app.get("/about", include_in_schema=False)
@app.head("/about", include_in_schema=False)
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


@app.get("/zoega", include_in_schema=False)
@app.head("/zoega", include_in_schema=False)
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


@app.get("/english", include_in_schema=False)
@app.head("/english", include_in_schema=False)
@cache_response
async def english_redirect(request: Request):
    """Redirect to /english_icelandic_dictionary."""
    return RedirectResponse(url="/english_icelandic_dictionary", status_code=301)


@app.get("/apple-touch-icon.png", include_in_schema=False)
@cache_response
async def apple_touch_icon_redirect(request: Request):
    """Redirect to /apple-touch-icon.png"""
    return RedirectResponse(url="/static/img/apple-touch-icon.png", status_code=301)


@app.get("/english_icelandic_dictionary", include_in_schema=False)
@app.head("/english_icelandic_dictionary", include_in_schema=False)
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


@app.get("/all", include_in_schema=False)
@app.head("/all", include_in_schema=False)
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


@app.get("/cat/{category}", include_in_schema=False)  # type: ignore
@app.head("/cat/{category}", include_in_schema=False)  # type: ignore
@cache_response(SMALL_CACHE_SIZE)
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


@app.get("/capitalized", include_in_schema=False)
@app.head("/capitalized", include_in_schema=False)
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


@app.get("/original", include_in_schema=False)
@app.head("/original", include_in_schema=False)
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


@app.get("/nonascii", include_in_schema=False)
@app.head("/nonascii", include_in_schema=False)
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


@app.get("/multiword", include_in_schema=False)
@app.head("/multiword", include_in_schema=False)
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


@app.get("/duplicates", include_in_schema=False)
@app.head("/duplicates", include_in_schema=False)
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


@app.get("/additions", include_in_schema=False)
@app.head("/additions", include_in_schema=False)
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


@app.get("/stats", include_in_schema=False)
@app.head("/stats", include_in_schema=False)
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


@app.get("/favicon.ico", include_in_schema=False)
@app.head("/favicon.ico", include_in_schema=False)
@cache_response
async def favicon(request: Request):
    return RedirectResponse(url="/static/img/favicon.ico", status_code=301)


@app.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
@app.head("/apple-touch-icon-precomposed.png", include_in_schema=False)
@cache_response
async def apple_touch_icon(request: Request):
    return RedirectResponse(url="/static/img/apple-touch-icon.png", status_code=301)


@app.get("/sitemap.xml", include_in_schema=False)
@app.head("/sitemap.xml", include_in_schema=False)
@cache_response
async def sitemap(request: Request) -> Response:
    return TemplateResponse(
        "sitemap.xml",
        {"request": request, "words": all_words},
        media_type="application/xml",
    )


@app.get("/robots.txt", include_in_schema=False)
@app.head("/robots.txt", include_in_schema=False)
@cache_response
async def robots(request: Request) -> Response:
    return TemplateResponse("robots.txt", {"request": request}, media_type="text/plain")


# API endpoints


@app.get("/api/metadata")
@cache_response
async def api_metadata(request: Request) -> JSONResponse:
    """Return metadata about the dictionary."""
    return JSONResponse(content=metadata)


@app.get("/api/suggest/{q}")  # type: ignore
@cache_response(SEARCH_CACHE_SIZE)
async def api_suggest(request: Request, q: str, limit: int = 10) -> JSONResponse:
    """Return autosuggestion results for partial string in input field."""
    results, _ = _cached_results(q)
    words = [x["word"] for x in results][:limit]
    return JSONResponse(content=words)


@app.get("/api/search/{q}")  # type: ignore
@cache_response(SEARCH_CACHE_SIZE)
async def api_search(request: Request, q: str) -> JSONResponse:
    """Return search results in JSON format."""
    if len(q) < 2:
        return _err("Query too short")

    results, _ = _cached_results(q)

    return JSONResponse(content={"results": results})


@app.get("/api/item/{w}")  # type: ignore
@cache_response(SEARCH_CACHE_SIZE)
async def api_item(request: Request, w: str) -> JSONResponse:
    """Return single dictionary entry in JSON format."""
    ws = w.strip()

    results, exact = _cached_results(ws, exact_match=True)
    if not results or not exact:
        return _err(f"No entry found for '{ws}'")

    return JSONResponse(content=results[0])


@app.get("/api/item/parsed/{w}")  # type: ignore
@cache_response(SEARCH_CACHE_SIZE)
async def api_item_parsed(request: Request, w: str) -> JSONResponse:
    """Return single dictionary entry in JSON format with parsed definition."""
    ws = w.strip()

    results, exact = _cached_results(ws, exact_match=True)
    if not results or not exact:
        return _err(f"No entry found for '{ws}'")

    result = results[0]

    # Parse definition string into components
    comp = unpack_definition(result["def"])

    # Translate category abbreviations to human-friendly words
    comp = {CAT_TO_NAME[k]: v for k, v in comp.items()}

    result["parsed"] = comp

    return JSONResponse(content=result)


def _strip_html(s: str) -> str:
    """Strip HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", s)


def _strip_parentheses(s: str) -> str:
    """Strip parentheses from a string."""
    return re.sub(r"\(.*?\)", "", s)


@app.get("/api/item/parsed/many/")  # type: ignore
@cache_response(SMALL_CACHE_SIZE)
async def api_item_parsed_many(
    request: Request, q: str, strip_html: int = 0, strip_parentheses: int = 0
) -> JSONResponse:
    q = q.strip()

    words = [w.strip() for w in q.split(",")]

    def _process_item(s: str) -> str:
        if strip_html:
            s = _strip_html(s)
        if strip_parentheses:
            s = _strip_parentheses(s)
        return s.strip()

    res = {}
    for w in words:
        results, exact = _cached_results(w, exact_match=True)
        if not results or not exact:
            continue
        result = results[0]
        # Parse definition string into components
        comp = unpack_definition(result["def"])
        # Translate category abbreviations to human-friendly words
        comp = {CAT_TO_NAME[k]: [_process_item(i) for i in v] for k, v in comp.items()}
        res[w] = comp

    return JSONResponse(content=res)
