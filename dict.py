#!/usr/bin/env python3
"""

Ensk.is - Free and open English-Icelandic dictionary

Copyright (c) 2021-2025, Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>
All rights reserved.

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


Code to read and parse dictionary source files.


"""

from typing import DefaultDict

import os
from collections import defaultdict
import orjson as json

from util import read_wordlist


CATEGORIES = read_wordlist("data/catwords.txt")


def read_raw_pages(fn: str | None = None) -> dict[str, list]:
    """Read all text files in the data/dict directory,
    return as an alphabetically indexed dict of lines."""
    base_path = "data/dict/"
    files = sorted(os.listdir(base_path))
    result = DefaultDict()
    result = defaultdict(lambda: [])

    for file in files:
        if fn and file != fn:
            continue
        fp = os.path.join(base_path, file)
        if not os.path.isfile(fp):
            continue
        if not file.endswith(".txt"):
            continue

        with open(fp, "r") as f:
            file_contents = f.read()
        lines = file_contents.split("\n")

        for ln in lines:
            # Skip all empty lines and comments
            lns = ln.strip()
            if not lns or lns.startswith("#"):
                continue
            keyname = file[:-4]
            result[keyname].append(ln)

    return result


def read_pages(fn: str | None = None) -> list[str]:
    """Read all text files in the data/dict directory,
    return as single list of all lines."""

    alphabet2words = read_raw_pages()
    entry_list = []
    for k, v in alphabet2words.items():
        entry_list.extend(v)

    entry_list.sort(key=lambda x: x.lower())
    return entry_list


def read_all_words() -> list[str]:
    """Return a list of all dictionary words."""
    r = read_pages()
    words = []
    for line in r:
        w, d = parse_line(line)
        words.append(w)
    words.sort(key=lambda x: x.lower())
    return words


def parse_line(s: str) -> tuple:
    """Parse a single line entry into its constitutent parts
    i.e. word and definition strings, and return as tuple."""
    comp = s.split()
    NO_VAL = 9999
    idx = NO_VAL
    for i, c in enumerate(comp):
        if c in CATEGORIES:
            idx = i
            break
    if idx == NO_VAL:
        raise Exception(f"No cat found!: {s}")

    wentries = list()
    for c in comp[:idx]:
        c = c.replace("\ufeff", "").strip().replace("  ", " ")
        if not c:
            continue
        if c.startswith("(") and c.endswith(")"):
            # Looks like there's some phonetic junk left over
            raise Exception(f"Invalid entry: {s}")
        wentries.append(c)

    word = " ".join(wentries)
    definition = " ".join(comp[idx:])
    return (word, definition)


def startswith_category(s: str) -> tuple[str, int] | None:
    """Check if a given string starts with a known word category.
    Returns a tuple of the category and the index at which it ends."""
    for c in CATEGORIES:
        if s.strip().startswith(c):
            return (c, s.index(c) + len(c))
    return None


def unpack_definition(s: str) -> dict:
    """Unpack a definition string into a dictionary of categories
    mapped to a list of words in that category."""
    comp = s.split(";")
    currcat = None
    out = defaultdict(list)

    for c in comp:
        sw = startswith_category(c)
        if sw is None:
            out[currcat].append(c.strip())
            continue
        cat, idx = sw
        currcat = cat
        out[currcat].append(c[idx:].strip())

    return dict(out)


WORD_TO_PAGE = None


def page_for_word(w: str) -> int:
    """Look up the page at which a given word occurs in
    Geir T. Zoega's original dictionary."""
    global WORD_TO_PAGE
    if not WORD_TO_PAGE:
        with open("data/word2page.json", "r") as file:
            WORD_TO_PAGE = json.loads(file.read())
    return WORD_TO_PAGE.get(w, 0)
