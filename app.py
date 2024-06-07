#!/usr/bin/env python3
"""

    Ensk.is - Free and open English-Icelandic dictionary

    Copyright (c) 2021-2024 Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>

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


    FastAPI web application


"""

from typing import List, Dict, Tuple, Any, Union

import re
import aiofiles
from functools import wraps

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import (
    Response,
    RedirectResponse,
    JSONResponse as FastAPIJSONResponse,
)
import orjson

from db import EnskDatabase
from util import human_size, perc
from dict import read_wordlist


# Website settings
WEBSITE_NAME = "Ensk.is"
WEBSITE_DESC = "Opin og frjáls ensk-íslensk orðabók"
BASE_URL = "https://ensk.is"

# Create app
app = FastAPI(title=WEBSITE_NAME, openapi_url="/openapi.json")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")
TemplateResponse = templates.TemplateResponse

# Initialize database singleton
e = EnskDatabase(read_only=True)

# Read all dictionary entries into memory
entries = e.read_all_entries()
num_entries = len(entries)
all_words = [e["word"] for e in entries]
additions = [a["word"] for a in e.read_all_additions()]
num_additions = len(additions)

CATEGORIES = read_wordlist("data/catwords.txt")

# Get all entries in each category and store in dict
CAT2ENTRIES = {}
for c in CATEGORIES:
    cs = c.rstrip(".")
    CAT2ENTRIES[cs] = e.read_all_in_wordcat(cs)


class CustomJSONResponse(FastAPIJSONResponse):
    """JSON response using the high-performance orjson library to serialize the data."""

    def render(self, content: Any) -> bytes:
        assert (
            orjson is not None
        ), "orjson must be installed to use CustomJSONResponse class"
        return orjson.dumps(content)


JSONResponse = CustomJSONResponse


def _err(msg: str) -> JSONResponse:
    """Return JSON error message."""
    return JSONResponse(content={"error": True, "errmsg": msg})


def _format_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Format dictionary entry for presentation."""
    w = item["word"]
    x = item["definition"]

    # Replace ~ symbol with English word
    x = x.replace("~", w)

    # Replace %[word]% with link to intra-dictionary entry
    rx = re.compile(r"%\[(.+?)\]%")
    x = rx.sub(r"<strong><em><a href='/item/\1'>\1</a></em></strong>", x)

    # Italicize English words
    x = x.replace("[", "<em>")
    x = x.replace("]", "</em>")

    # Phonetic spelling
    ipa_uk = item.get("ipa_uk", "")
    ipa_us = item.get("ipa_us", "")

    # Generate URLs to audio files
    audiofn = w.replace(" ", "_")
    audio_url_uk = f"{BASE_URL}/static/audio/dict/uk/{audiofn}.mp3"
    audio_url_us = f"{BASE_URL}/static/audio/dict/us/{audiofn}.mp3"

    # Original dictionary page
    p = item["page_num"]
    p_url = f"{BASE_URL}/page/{p}" if p > 0 else ""

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


def _results(q: str, exact_match: bool = False) -> Tuple[List, bool]:
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

    return results, exact_match_found


def cache_response(func):
    """
    Decorator that indefinitely caches the response of a FastAPI async function.

    Example:
    ```
        app = FastAPI()

        @app.get("/")
        @cache_response
        async def example():
            return {"message": "Hello World"}
    ```
    """
    response = None

    @wraps(func)
    async def wrapper(*args, **kwargs):
        nonlocal response
        if not response:
            response = await func(*args, **kwargs)
        return response

    return wrapper


@app.get("/")
@app.head("/")
@cache_response
async def index(request: Request):
    """/ main page"""
    return TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": f"{WEBSITE_NAME} - {WEBSITE_DESC}",
        },
    )


async def _save_missing_word(word: str):
    """Save word to missing words list."""
    async with aiofiles.open("missing_words.txt", "a+") as file:
        await file.write(f"{word}\n")


@app.get("/search")
async def search(request: Request, q: str):
    """Return page with search results for query."""
    q = q.strip()
    if len(q) < 2:
        return _err("Query too short")

    results, exact = _results(q)

    if not exact or not results:
        if re.match(r"^[a-zA-Z]+$", q):
            await _save_missing_word(q)

    return TemplateResponse(
        "result.html",
        {
            "request": request,
            "title": f"„{q}“ - {WEBSITE_NAME}",
            "q": q,
            "results": results,
            "exact": exact,
        },
    )


@app.get("/item/{w}")
async def item(request: Request, w):
    """Return page for a single dictionary word definition."""
    results, _ = _results(w, exact_match=True)
    if not results:
        raise HTTPException(status_code=404, detail="Síða fannst ekki")
    return TemplateResponse(
        "item.html",
        {
            "request": request,
            "title": f"{w} - {WEBSITE_NAME}",
            "q": w,
            "results": results,
            "word": w,
        },
    )


@app.get("/page/{n}")
async def page(request: Request, n):
    """Return page for a single dictionary page image."""
    n = int(n)
    if n < 1 or n > 707:
        raise HTTPException(status_code=404, detail="Blaðsíða fannst ekki")

    pad = n - 1

    return TemplateResponse(
        "page.html",
        {
            "request": request,
            "title": f"Zoëga bls. {n} - {WEBSITE_NAME}",
            "n": n,
            "npad": f"{pad:03}",
        },
    )


@app.get("/files")
@cache_response
async def files(request: Request):
    """Page containing download links to data files."""

    sqlite_size = human_size("static/files/ensk_dict.db.zip")
    csv_size = human_size("static/files/ensk_dict.csv.zip")
    text_size = human_size("static/files/ensk_dict.txt.zip")

    return TemplateResponse(
        "files.html",
        {
            "request": request,
            "title": f"Gögn - {WEBSITE_NAME}",
            "sqlite_size": sqlite_size,
            "csv_size": csv_size,
            "text_size": text_size,
        },
    )


@app.get("/about")
@cache_response
async def about(request: Request):
    """About page."""

    def sing_or_plur(s: Union[str, int]) -> bool:
        return str(s).endswith("1") and not str(s).endswith("11")

    return TemplateResponse(
        "about.html",
        {
            "request": request,
            "title": f"Um - {WEBSITE_NAME}",
            "num_entries": num_entries,
            "num_additions": num_additions,
            "entries_singular": sing_or_plur(num_entries),
            "additions_singular": sing_or_plur(num_additions),
            "additions_percentage": perc(num_additions, num_entries),
        },
    )


@app.get("/english")
@cache_response
async def english_redirect(request: Request):
    """Redirect to /english_icelandic_dictionary."""

    return RedirectResponse(url="/english_icelandic_dictionary", status_code=301)


@app.get("/english_icelandic_dictionary")
@cache_response
async def english(request: Request):
    """English page."""

    return TemplateResponse(
        "english.html",
        {
            "request": request,
            "title": f"{WEBSITE_NAME} - Free and open English-Icelandic dictionary",
            "num_entries": num_entries,
            "num_additions": num_additions,
            "entries_singular": num_entries,
            "additions_singular": num_additions,
            "additions_percentage": perc(num_additions, num_entries),
        },
    )


@app.get("/all")
@cache_response
async def all(request: Request):
    """Page with links to all entries."""
    return TemplateResponse(
        "all.html",
        {
            "request": request,
            "title": f"Öll orðin - {WEBSITE_NAME}",
            "words": all_words,
        },
    )


@app.get("/cat/{category}")
async def cat(request: Request, category: str):
    """Page with links to all entries in the given category."""
    entries = CAT2ENTRIES.get(category, [])
    words = [e["word"] for e in entries]

    return TemplateResponse(
        "cat.html",
        {
            "request": request,
            "title": f"Öll orð í flokknum {category} - {WEBSITE_NAME}",
            "words": words,
            "category": category,
        },
    )


@app.get("/additions")
@cache_response
async def additions_page(request: Request):
    """Page with links to all words that are additions to the original dictionary."""
    return TemplateResponse(
        "additions.html",
        {
            "request": request,
            "title": f"Viðbætur - {WEBSITE_NAME}",
            "additions": additions,
            "num_additions": num_additions,
            "additions_percentage": perc(num_additions, num_entries),
        },
    )


@app.get("/zoega")
@cache_response
async def zoega(request: Request):
    """Page with details about the Zoega dictionary."""
    return TemplateResponse(
        "zoega.html",
        {"request": request, "title": f"Orðabók Geirs T. Zoëga - {WEBSITE_NAME}"},
    )


@app.get("/stats")
@cache_response
async def stats(request: Request):
    """Page with statistics on dictionary entries."""

    no_uk_ipa = len(e.read_all_without_ipa(lang="uk"))
    no_us_ipa = len(e.read_all_without_ipa(lang="us"))
    no_page = len(e.read_all_with_no_page())
    num_capitalized = len(e.read_all_capitalized())
    num_duplicates = len(e.read_all_duplicates())

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
            "title": f"Tölfræði - {WEBSITE_NAME}",
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
            "num_duplicates": num_duplicates,
            "perc_duplicates": perc(num_duplicates, num_entries),
            "wordstats": wordstats,
        },
    )


@app.get("/apidoc")
@cache_response
async def apidoc(request: Request):
    """Page with API documentation."""
    return TemplateResponse(
        "apidoc.html", {"request": request, "title": f"Forritaskil - {WEBSITE_NAME}"}
    )


@app.get("/sitemap.xml")
@app.head("/sitemap.xml")
@cache_response
async def sitemap(request: Request) -> Response:
    """Sitemap generated on-demand."""
    return TemplateResponse(
        "sitemap.xml",
        {"request": request, "words": all_words},
        media_type="application/xml",
    )


@app.get("/robots.txt")
@app.head("/robots.txt")
@cache_response
async def robots(request: Request) -> Response:
    """Robots.txt generated on-demand."""
    return TemplateResponse("robots.txt", {"request": request}, media_type="text/plain")


# API endpoints


@app.get("/api/suggest/{q}")
async def api_suggest(request: Request, q: str, limit: int = 10) -> JSONResponse:
    """Return autosuggestion results for partial string in input field."""
    results, _ = _results(q)
    words = [x["word"] for x in results][:limit]
    return JSONResponse(content=words)


@app.get("/api/search/{q}")
async def api_search(request: Request, q: str) -> JSONResponse:
    """Return search results in JSON format."""
    if len(q) < 2:
        return _err("Query too short")

    results, _ = _results(q)
    return JSONResponse(content={"results": results})


@app.get("/api/item/{w}")
async def api_item(request: Request, w: str) -> JSONResponse:
    """Return single dictionary entry in JSON format."""
    ws = w.strip()
    results, exact = _results(ws, exact_match=True)
    if not results or not exact:
        return _err(f"No entry found for '{ws}'")

    return JSONResponse(content=results[0])


# @app.post("/api/report_missing/{w}")
# async def api_report_missing(request: Request) -> JSONResponse:
#     """Report that a word is missing from the dictionary."""
#     if not w:
#         return _err("Missing 'w' parameter")
#     w = w.strip()
#     if not w:
#         return _err("Empty 'w' parameter")
#     if w in all_words:
#         return _err(f"Word '{w}' is already in the dictionary")

#     return JSONResponse(content={"success": True})
