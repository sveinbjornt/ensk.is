#!/usr/bin/env python3
"""

    Ensk.is: English-Icelandic dictionary web application

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

from typing import List

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, JSONResponse

from db import EnskDatabase

# Website settings
WEBSITE_NAME = "Ensk.is"
WEBSITE_DESC = "Oping og frjáls ensk-íslensk orðabók"

# Create app
app = FastAPI(title=WEBSITE_NAME, openapi_url="/openapi.json")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")
TemplateResponse = templates.TemplateResponse

# Initialize database singleton
e = EnskDatabase()


res = e.read_all_entries()


def _err(msg: str) -> JSONResponse:
    return JSONResponse(content={"err": True, "errmsg": msg})


def _results(q: str, exact_match: bool = False) -> List:
    results = []
    if not q:
        return []

    ql = q.lower()
    for k in res:
        kl = k["word"].lower()
        if (exact_match and ql == kl) or (not exact_match and ql in k["word"].lower()):
            w = k["word"]
            x = k["definition"]
            x = x.replace("[", "<em>")
            x = x.replace("]", "</em>")
            x = x.replace("~", k["word"])
            # x = re.sub(r"\(.+?\)\s", " ", x, 1)
            wfnfixed = w.replace(" ", "_")
            audio_url = f"/static/audio/dict/{wfnfixed}.mp3"
            ipa = k.get("ipa") or ""
            results.append({"w": w, "x": x, "i": ipa, "p": 1, "a": audio_url})

    def sortfn(a):
        wl = a["w"].lower()
        if wl == ql:
            return 0
        if wl.startswith(ql):
            return 1
        if wl.endswith(ql):
            return 2
        return 999

    results.sort(key=sortfn)

    return results


@app.get("/")
async def index(request: Request):
    return TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": f"{WEBSITE_NAME} - {WEBSITE_DESC}",
        },
    )


@app.get("/search")
async def search(request: Request, q: str):

    results = _results(q)

    return TemplateResponse(
        "result.html",
        {
            "request": request,
            "title": f"{q} - {WEBSITE_NAME}",
            "q": q,
            "results": results,
        },
    )


@app.get("/item/{w}")
async def item(request: Request, w):

    results = _results(w, exact_match=True)

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
    return TemplateResponse(
        "files.html", {"request": request, "title": f"Gögn - {WEBSITE_NAME}"}
    )


@app.get("/about")
async def about(request: Request):
    return TemplateResponse(
        "about.html", {"request": request, "title": f"Um - {WEBSITE_NAME}"}
    )


@app.get("/zoega")
async def zoega(request: Request):
    return TemplateResponse(
        "zoega.html",
        {"request": request, "title": f"Orðabók Geirs T. Zoëga - {WEBSITE_NAME}"},
    )


@app.get("/apidoc")
async def api(request: Request):
    return TemplateResponse(
        "apidoc.html", {"request": request, "title": f"Forritaskil - {WEBSITE_NAME}"}
    )


@app.get("/api/suggest/{q}")
async def api_suggest(request: Request, q, limit: int = 10) -> JSONResponse:
    results = _results(q)
    words = [x["w"] for x in results][:limit]
    return JSONResponse(content=words)


@app.get("/api/search/{q}")
async def api_search(request: Request, q) -> JSONResponse:
    results = _results(q)
    return JSONResponse(content={"results": results})


@app.get("/sitemap.xml")
async def sitemap(request: Request) -> Response:
    return Response(content="", media_type="application/xml")
