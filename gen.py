#!/usr/bin/env python3
"""

    Ensk.is - Free and open English-Icelandic dictionary

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

from typing import List, Tuple, Optional

import os
import csv

from util import read_pages, parse_line, page_for_word, zip_file, read_ipa
from db import EnskDatabase, DB_FILENAME


EntryType = Tuple[str, str, str, str, int]
EntryList = List[EntryType]


ENWORD_TO_IPA_UK = read_ipa("data/ipa/uk/en2ipa.json")
ENWORD_TO_IPA_US = read_ipa("data/ipa/us/en2ipa.json")

STATIC_FILES_PATH = "static/files/"


def ipa4entry(s: str, lang="uk") -> Optional[str]:
    """Look up IPA for word."""
    assert lang in ["uk", "us"]
    if lang == "uk":
        word2ipa = ENWORD_TO_IPA_UK
    else:
        word2ipa = ENWORD_TO_IPA_US
    ipa = word2ipa.get(s)
    if not ipa and " " in s:
        # It's a multi-word entry
        wipa = s.split()
        ipa4words = []
        # Look up each individual word and assemble
        for wp in wipa:
            lookup = word2ipa.get(wp)
            if not lookup:
                lookup = word2ipa.get(wp.lower())
            if not lookup:
                lookup = word2ipa.get(wp.capitalize())
            if not lookup:
                break
            else:
                lookup = lookup.lstrip("/").rstrip("/")
                ipa4words.append(lookup)
        if len(ipa4words) == len(wipa):
            ipa = " ".join(ipa4words)
            ipa = f"/{ipa}/"
    return ipa


def read_all_entries() -> EntryList:
    """Read all entries from dictionary text files
    and parse them."""
    r = read_pages()
    entries = []
    for line in r:
        wd = parse_line(line)
        w = wd[0]
        definition = wd[1]
        ipa_uk = ipa4entry(w) or ""
        ipa_us = ipa4entry(w, lang="us") or ""
        pn = page_for_word(w)
        entries.append(tuple([w, definition, ipa_uk, ipa_us, pn]))

    entries.sort(key=lambda d: d[0])  # Sort alphabetically by word
    return entries


def delete_db() -> None:
    """Delete any pre-existing SQLite database file."""
    try:
        os.remove(DB_FILENAME)
    except Exception:
        pass


def add_entries_to_db(entries: EntryList) -> None:
    """Insert all entries into database."""
    db = EnskDatabase()
    for e in entries:
        (w, definition, ipa_uk, ipa_us, pn) = e
        print(f"Adding {w}")
        db.add_entry(w, definition, ipa_uk, ipa_us, pn)
    db.conn().commit()


def generate_database(entries: EntryList) -> str:
    """Generate SQLite database. Returns filename."""
    delete_db()
    add_entries_to_db(entries)
    zipfn = f"{STATIC_FILES_PATH}ensk_dict.db.zip"
    zip_file(DB_FILENAME, zipfn)
    return zipfn


def generate_csv(entries: EntryList) -> str:
    """Generate zipped CSV file. Return file path."""
    fields = ["word", "definition", "ipa", "page_num"]
    old_cwd = os.getcwd()
    os.chdir(STATIC_FILES_PATH)
    filename = "ensk_dict.csv"
    with open(filename, "w") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        csvwriter.writerows(entries)
    zipfn = f"{filename}.zip"
    zip_file(filename, zipfn)
    os.remove(filename)
    os.chdir(old_cwd)
    return f"{STATIC_FILES_PATH}{zipfn}"


def generate_text(entries: EntryList) -> str:
    """Generate zipped text file w. all entries. Return file path."""
    old_cwd = os.getcwd()
    os.chdir(STATIC_FILES_PATH)
    filename = "ensk_dict.txt"
    with open(filename, "w") as file:
        for e in entries:
            file.write(f"{e[0]} {e[1]}\n")
    zipfn = f"{filename}.zip"
    zip_file(filename, zipfn)
    os.remove(filename)
    os.chdir(old_cwd)
    return f"{STATIC_FILES_PATH}{zipfn}"


# def generate_pdf(entries: EntryList) -> str:
#     """Generate PDF. Return file path."""
#     return ""


def main() -> None:
    entries = read_all_entries()
    # print(entries)
    generate_database(entries)
    generate_csv(entries)
    generate_text(entries)
    # generate_pdf(entries)


if __name__ == "__main__":
    """Command line invocation."""
    main()
