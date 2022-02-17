#!/usr/bin/env python3
"""

    Ensk.is - English-Icelandic dictionary

    Copyright (c) 2022, Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>
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

    Generate SQLite database from alphabetic dictionary text files

"""

from typing import List, Tuple

import os

from util import read_pages, parse_line, page_for_word
from db import EnskDatabase, DB_FILENAME


EntryType = Tuple[str, str, int]
EntryList = List[EntryType]


def read_all_entries() -> EntryList:
    r = read_pages()
    entries = []
    for line in r:
        wd = parse_line(line)
        w = wd[0]
        definition = wd[1]
        pn = page_for_word(w)
        entries.append(tuple([w, definition, pn]))
    return entries


def delete_db() -> None:
    """Delete ny pre-existing SQLite database file."""
    try:
        os.remove(DB_FILENAME)
    except:
        pass


def add_entries_to_db(entries: EntryList) -> None:
    """Insert all entries into database."""
    db = EnskDatabase()
    for e in entries:
        (w, definition, pn) = e
        print(f"Adding {w}")
        db.add_entry(w, definition, pn)


def generate_database(entries: EntryList) -> str:
    """Generate SQLite database. Returns filename."""
    delete_db()
    add_entries_to_db(entries)
    return DB_FILENAME


def generate_csv(entries: EntryList) -> str:
    """Generate zipped CSV file in static/files/. Return file path."""
    pass


def generate_text(entries: EntryList) -> str:
    """Generate zipped text files in static/files/. Return file path."""
    pass


def generate_pdf(entries: EntryList) -> str:
    """Generate PDF in static/files/. Return file path."""
    pass


if __name__ == "__main__":
    """Command line invocation."""
    entries = read_all_entries()
    generate_database(entries)
    generate_csv(entries)
    generate_text(entries)
    generate_pdf(entries)
