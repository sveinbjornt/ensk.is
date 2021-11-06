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

import json

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from util import icequote

WEBSITE_NAME = "Ensk.is"


templates = Jinja2Templates(directory="templates")


app = FastAPI(title="Ensk.is", openapi_url="/openapi.json")

app.mount("/static", StaticFiles(directory="static"), name="static")

data = None
with open("enis.json", "r") as f:
    data = json.load(f)


def _err(msg: str) -> JSONResponse:
    return JSONResponse(content={"err": True, "errmsg": msg})


@app.get("/")
def index(request: Request) -> dict:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": f"{WEBSITE_NAME} - Opin og frjáls ensk-íslensk orðabók",
        },
    )


@app.get("/search")
def search(request: Request, q: str) -> dict:

    results = []
    ql = q.lower()
    for k, v in data.items():
        if ql in k.lower():
            results.append({"w": k, "x": v})

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "title": f'"{q}" - {WEBSITE_NAME}',
            "q": q,
            "results": results,
        },
    )


@app.get("/files")
def files(request: Request) -> dict:
    return templates.TemplateResponse(
        "files.html", {"request": request, "title": f"Gögn - {WEBSITE_NAME}"}
    )


@app.get("/about")
def files(request: Request) -> dict:
    return templates.TemplateResponse(
        "about.html", {"request": request, "title": f"Gögn - {WEBSITE_NAME}"}
    )
