#!/usr/bin/env python3
"""

    Ensk.is - Free and open English-Icelandic dictionary

    Copyright (c) 2022 Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>

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

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, JSONResponse

from db import EnskDatabase
from cache import cache_response


# Website settings
WEBSITE_NAME = "Ensk.is"
WEBSITE_DESC = "Opin og frjáls ensk-íslensk orðabók"

# Create app
app = FastAPI(title=WEBSITE_NAME, openapi_url="/openapi.json")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")
TemplateResponse = templates.TemplateResponse

# Initialize database singleton
e = EnskDatabase()

# Read all dictionary entries into memory
entries = e.read_all_entries()
num_entries = len(entries)
all_words = [e["word"] for e in entries]
additions = [a["word"] for a in e.read_all_additions()]
num_additions = len(additions)


def _err(msg: str) -> JSONResponse:
    """Return JSON error message."""
    return JSONResponse(content={"error": True, "errmsg": msg})


def _format_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Format dictionary entry for presentation."""
    w = item["word"]
    x = item["definition"]
    p = item["page_num"]
    # Replace ~ symbol with English word
    x = x.replace("~", w)
    # TODO: Replace %[word]% with link to item
    rx = re.compile(r"%\[(.+)\]%")
    x = rx.sub(r"<strong><a href='/item/\1'>\1</a></strong>", x)
    pass
    # Italicize English words
    x = x.replace("[", "<em>")
    x = x.replace("]", "</em>")
    # Fix filename f. audio file
    wfnfixed = w.replace(" ", "_")
    audio_url_uk = f"/static/audio/dict/uk/{wfnfixed}.mp3"
    audio_url_us = f"/static/audio/dict/us/{wfnfixed}.mp3"
    # Phonetic spelling
    ipa_uk = item.get("ipa_uk") or ""
    ipa_us = item.get("ipa_us") or ""
    # Create item dict
    item = {
        "w": w,
        "x": x,
        "i": ipa_uk,
        "i2": ipa_us,
        "p": p,
        "a": audio_url_uk,
        "a2": audio_url_us,
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
            lw = item["w"].lower()
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

    equal.sort(key=lambda d: d["w"].lower())
    swith.sort(key=lambda d: d["w"].lower())
    ewith.sort(key=lambda d: d["w"].lower())
    other.sort(key=lambda d: d["w"].lower())

    results = [*equal, *swith, *ewith, *other]

    return results, exact_match_found


@app.get("/")
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


@app.get("/search")
async def search(request: Request, q: str):
    """Return page with search results for query."""
    q = q.strip()
    results, exact = _results(q)

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
    return TemplateResponse(
        "files.html", {"request": request, "title": f"Gögn - {WEBSITE_NAME}"}
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


@app.get("/apidoc")
@cache_response
async def apidoc(request: Request):
    """Page with API documentation."""
    return TemplateResponse(
        "apidoc.html", {"request": request, "title": f"Forritaskil - {WEBSITE_NAME}"}
    )


@app.get("/sitemap.xml")
@cache_response
async def sitemap(request: Request) -> Response:
    """Sitemap generated on-demand."""
    return TemplateResponse(
        "sitemap.xml",
        {"request": request, "words": all_words},
        media_type="application/xml",
    )


@app.get("/robots.txt")
@cache_response
async def robots(request: Request) -> Response:
    """Robots.txt generated on-demand."""
    return TemplateResponse("robots.txt", {"request": request}, media_type="text/plain")


# API endpoints


@app.get("/api/suggest/{q}")
async def api_suggest(request: Request, q, limit: int = 10) -> JSONResponse:
    """Return autosuggestion results for partial string in input field."""
    results, _ = _results(q)
    words = [x["w"] for x in results][:limit]
    return JSONResponse(content=words)


@app.get("/api/search/{q}")
async def api_search(request: Request, q) -> JSONResponse:
    """Return search results in JSON format."""
    results, _ = _results(q)
    return JSONResponse(content={"results": results})


@app.get("/api/item/{w}")
async def api_item(request: Request, w) -> JSONResponse:
    """Return single dictionary entry in JSON format."""
    ws = w.strip()
    results, exact = _results(ws, exact_match=True)
    if not results or not exact:
        return _err(f"No entry found for '{ws}'")

    return JSONResponse(content=results[0])
