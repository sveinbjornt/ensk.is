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

    Main web application

"""

from typing import List, Tuple

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, JSONResponse

from pymemcache.client.base import Client
from fastapi_cache import FastAPICache
from fastapi_cache.backends.memcached import MemcachedBackend
from fastapi_cache.decorator import cache

from db import EnskDatabase
from util import read_wordlist, read_pages


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
res = e.read_all_entries()
num_entries = len(res)
words = frozenset([r["word"] for r in res])

# Read master English word list into memory
enwords = read_wordlist("data/wordlists/words.txt")


def _err(msg: str) -> JSONResponse:
    """Return JSON error message."""
    return JSONResponse(content={"error": True, "errmsg": msg})


def _results(q: str, exact_match: bool = False) -> Tuple[List, bool]:
    if not q:
        return [], False

    equal = []
    swith = []
    ewith = []
    other = []

    ql = q.lower()
    for k in res:
        kl = k["word"].lower()
        if (exact_match and ql == kl) or (not exact_match and ql in k["word"].lower()):
            w = k["word"]
            x = k["definition"]
            p = k["page_num"]
            # Italicize English words
            x = x.replace("[", "<em>")
            x = x.replace("]", "</em>")
            # Replace ~ symbol with English word
            x = x.replace("~", w)
            # Fix filename f. audio file
            wfnfixed = w.replace(" ", "_")
            audio_url = f"/static/audio/dict/uk/{wfnfixed}.mp3"
            audio_url_us = f"/static/audio/dict/us/{wfnfixed}.mp3"
            ipa_uk = k.get("ipa_uk") or ""
            ipa_us = k.get("ipa_us") or ""
            # Create item dict
            item = {
                "w": w,
                "x": x,
                "i": ipa_uk,
                "i2": ipa_us,
                "p": p,
                "a": audio_url,
                "a2": audio_url_us,
            }
            if w == q:
                equal.append(item)
            elif w.startswith(q):
                swith.append(item)
            elif w.endswith(q):
                ewith.append(item)
            else:
                other.append(item)

    exact_match_found: bool = len(equal) > 0

    equal.sort(key=lambda d: d["w"])
    swith.sort(key=lambda d: d["w"])
    ewith.sort(key=lambda d: d["w"])
    other.sort(key=lambda d: d["w"])

    results = [*equal, *swith, *ewith, *other]

    # def sortfn(a):
    #     wl = a["w"].lower()
    #     if wl == ql:
    #         return 0
    #     if wl.startswith(ql):
    #         return 1
    #     if wl.endswith(ql):
    #         return 2
    #     return 999

    # results.sort(key=sortfn)

    return results, exact_match_found


# @app.on_event("startup")
# async def startup():
#     client = Client(("pymemcached", 11211))
#     FastAPICache.init(MemcachedBackend(client), prefix="fastapi-cache")


@app.get("/")
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

    # if q in enwords:

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


@app.get("/files")
async def files(request: Request):
    """Page containing download links to data files."""
    return TemplateResponse(
        "files.html", {"request": request, "title": f"Gögn - {WEBSITE_NAME}"}
    )


@app.get("/about")
async def about(request: Request):
    """About page."""
    return TemplateResponse(
        "about.html",
        {
            "request": request,
            "title": f"Um - {WEBSITE_NAME}",
            "num_entries": num_entries,
        },
    )


@app.get("/all")
# @cache(expire=86400)
async def all(request: Request):
    """Page with links to all entries."""
    return TemplateResponse(
        "all.html",
        {"request": request, "title": f"Öll orðin - {WEBSITE_NAME}", "results": res},
    )


@app.get("/additions")
# @cache(expire=86400)
async def additions(request: Request):
    """Page with links to all words that are additions to the original dictionary."""
    add = read_pages(fn="add.txt")

    return TemplateResponse(
        "additions.html",
        {"request": request, "title": f"Viðbætur - {WEBSITE_NAME}", "results": res},
    )


@app.get("/page/{n}")
async def page(request: Request, n):
    """Return page for a single dictionary word definition."""
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


@app.get("/zoega")
async def zoega(request: Request):
    """Page with details about the Zoega dictionary."""
    return TemplateResponse(
        "zoega.html",
        {"request": request, "title": f"Orðabók Geirs T. Zoëga - {WEBSITE_NAME}"},
    )


@app.get("/apidoc")
async def apidoc(request: Request):
    """Page with API documentation."""
    return TemplateResponse(
        "apidoc.html", {"request": request, "title": f"Forritaskil - {WEBSITE_NAME}"}
    )


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


@app.get("/sitemap.xml")
async def sitemap(request: Request) -> Response:
    """Sitemap generated on-demand."""
    return TemplateResponse(
        "sitemap.xml",
        {"request": request, "words": words},
        media_type="application/xml",
    )


@app.get("/robots.txt")
async def robots(request: Request) -> Response:
    """Robots.txt generated on-demand."""
    return TemplateResponse("robots.txt", {"request": request}, media_type="text/plain")
