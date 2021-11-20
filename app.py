#!/usr/bin/env python3
"""

    Ensk.is: English-Icelandic dictionary web application

    Copyright (c) Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>

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

import json

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from util import icequote

WEBSITE_NAME = "Ensk.is"

app = FastAPI(title=WEBSITE_NAME, openapi_url="/openapi.json")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


data = None
with open("enis.json", "r") as f:
    data = json.load(f)


def _err(msg: str) -> JSONResponse:
    return JSONResponse(content={"err": True, "errmsg": msg})


def _results(q: str) -> List:
    results = []
    if not q:
        return []

    ql = q.lower()
    for k, v in data.items():
        if ql in k.lower():
            x = v["x"]
            x = x.replace("[", "<em>")
            x = x.replace("]", "</em>")
            results.append({"w": k, "x": x, "p": v["n"] + 1})

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
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": f"{WEBSITE_NAME} - Opin og frjáls ensk-íslensk orðabók",
        },
    )


@app.get("/search")
async def search(request: Request, q: str):

    results = _results(q)

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "title": f"{icequote(q)} - {WEBSITE_NAME}",
            "q": q,
            "results": results,
        },
    )


@app.get("/files")
async def files(request: Request):
    return templates.TemplateResponse(
        "files.html", {"request": request, "title": f"Gögn - {WEBSITE_NAME}"}
    )


@app.get("/about")
async def about(request: Request):
    return templates.TemplateResponse(
        "about.html", {"request": request, "title": f"Gögn - {WEBSITE_NAME}"}
    )


@app.get("/apidoc")
async def api(request: Request):
    return templates.TemplateResponse(
        "apidoc.html", {"request": request, "title": f"Forritaskil - {WEBSITE_NAME}"}
    )


@app.get("/api/suggest/{q}")
async def api_suggest(request: Request, q):
    results = _results(q)
    words = [x["w"] for x in results]
    return JSONResponse(content=words)


@app.get("/api/search/{q}")
async def api_search(request: Request, q):
    results = _results(q)

    return JSONResponse(content={"results": results})
