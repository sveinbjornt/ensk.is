#!/usr/bin/env python3
"""

Ensk.is - Free and open English-Icelandic dictionary

Copyright (c) 2021-2026, Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>
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


Generate SQLite database + other files from raw dictionary text files.


"""

import os
import sys
import inspect

from typing import Optional

import csv
import datetime
import json as std_json

import sqlite_utils
import nltk

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


from dict import (  # noqa: E402
    read_pages,
    parse_line,
    page_for_word,
    syllables_for_word,
    synonyms_for_word,
    antonyms_for_word,
)
from db import EnskDatabase, DB_FILENAME  # noqa: E402
from util import zip_file, read_json, silently_remove  # noqa: E402
from info import PROJECT  # noqa: E402


EntryType = tuple[str, str, str, str, str, int, int, str, str]
EntryList = list[EntryType]


ENWORD_TO_IPA_UK = read_json("data/ipa/uk/en2ipa.json")
ENWORD_TO_IPA_US = read_json("data/ipa/us/en2ipa.json")
WORD_FREQ_MAP = read_json("data/freq/word_frequency_map.json")


def ipa4entry(s: str, lang: str = "uk") -> str | None:
    """Look up International Phonetic Alphabet spelling for word."""
    assert lang in ["uk", "us"]
    if lang == "uk":
        word2ipa = ENWORD_TO_IPA_UK
    else:
        word2ipa = ENWORD_TO_IPA_US

    def only_first_ipa(s: Optional[str]) -> str:
        """Return only the first IPA spelling in a string."""
        if not s:
            return ""
        # Split by space and return the first part
        parts = s.split(", ")
        if len(parts) > 1:
            return parts[0]
        return s

    ipa = only_first_ipa(word2ipa.get(s))
    if not ipa and " " in s:
        # It's a multi-word entry
        wipa = s.split()
        ipa4words = []
        # Look up each individual word and assemble
        for wp in wipa:
            lookup = only_first_ipa(word2ipa.get(wp))
            if not lookup:
                lookup = only_first_ipa(word2ipa.get(wp.lower()))
            if not lookup:
                lookup = only_first_ipa(word2ipa.get(wp.capitalize()))
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
    """Read all entries from dictionary text files and parse them."""
    r = read_pages()

    entries = []
    for line in r:
        wd = parse_line(line)
        w = wd[0]
        definition = wd[1]
        syll = syllables_for_word(w)
        ipa_uk = ipa4entry(w, lang="uk") or ""
        ipa_us = ipa4entry(w, lang="us") or ""
        pn = page_for_word(w)
        freq = WORD_FREQ_MAP.get(w, -1)
        syns = ",".join(synonyms_for_word(w))
        ants = ",".join(antonyms_for_word(w))
        entries.append(
            tuple([w, definition, syll, ipa_uk, ipa_us, pn, freq, syns, ants])
        )

    entries.sort(key=lambda d: d[0].lower())  # Sort alphabetically by word

    return entries


def generate_database(entries: EntryList) -> str:
    """Generate SQLite database and create a corresponding zip archive.
    Returns path to zip file."""

    # Remove pre-existing database file
    delete_db()

    # Create new db and add data
    num_entries = add_entries_to_db(entries)
    add_metadata_to_db(num_entries)
    optimize_db()

    # Zip it
    zipfn = f"{PROJECT.STATIC_FILES_PATH}{PROJECT.BASE_DATA_FILENAME}.db.zip"
    zip_file(DB_FILENAME, zipfn)

    return zipfn


def delete_db() -> None:
    """Delete any pre-existing SQLite database file."""
    silently_remove(DB_FILENAME)


def add_metadata_to_db(num_entries) -> None:
    """Add metadata to database."""
    db = EnskDatabase()
    db.add_metadata("name", PROJECT.NAME)
    db.add_metadata("description", PROJECT.DESCRIPTION)
    db.add_metadata("license", PROJECT.LICENSE)
    db.add_metadata("website", PROJECT.BASE_URL)
    db.add_metadata("source", PROJECT.REPO_URL)
    db.add_metadata("editor", PROJECT.EDITOR)
    db.add_metadata("editor_email", PROJECT.EMAIL)
    db.add_metadata("generation_date", datetime.datetime.now(datetime.UTC).isoformat())
    db.add_metadata("num_entries", num_entries)
    # db.add_metadata("version", PROJECT.VERSION)


def add_entries_to_db(entries: EntryList) -> int:
    """Insert all entries into database."""
    db = EnskDatabase()

    cursor = db.conn().cursor()
    cursor.executemany(
        "INSERT INTO dictionary (word, definition, syllables, ipa_uk, ipa_us, page_num, freq, synonyms, antonyms) VALUES (?,?,?,?,?,?,?,?,?)",
        entries,
    )
    db.conn().commit()

    return len(entries)


def optimize_db() -> None:
    """Optimize database."""
    conn = EnskDatabase().conn()

    # Enable full-text search indexing
    sqlite_utils.Database(conn).table("dictionary").enable_fts(("word", "definition"))

    # Create index on word column
    conn.cursor().execute("CREATE INDEX idx_word ON dictionary(word COLLATE NOCASE)")

    # Analyze and vacuum
    conn.cursor().execute("ANALYZE;")
    conn.cursor().execute("VACUUM;")
    conn.commit()


def generate_csv(entries: EntryList, unlink_csv: bool = False) -> str:
    """Generate zipped CSV file. Return file path."""
    fields = [
        "word",
        "definition",
        "syllables",
        "ipa_uk",
        "ipa_us",
        "page_num",
        "freq",
        "synonyms",
        "antonyms",
    ]

    # Change to static files dir
    old_cwd = os.getcwd()
    os.chdir(PROJECT.STATIC_FILES_PATH)

    # Write the CSV and zip it
    filename = f"{PROJECT.BASE_DATA_FILENAME}.csv"
    with open(filename, "w") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        csvwriter.writerows(entries)
    zipfn = f"{filename}.zip"
    zip_file(filename, zipfn)

    if unlink_csv:
        silently_remove(filename)

    # Restore previous CWD
    os.chdir(old_cwd)

    return f"{PROJECT.STATIC_FILES_PATH}{zipfn}"


def generate_text(entries: EntryList) -> str:
    """Generate zipped text file w. all entries. Return file path."""

    # Change to static files dir
    old_cwd = os.getcwd()
    os.chdir(PROJECT.STATIC_FILES_PATH)

    # Generate full dictionary text
    txt = "\n".join([f"{e[0]} {e[1]}" for e in entries]).strip()

    # Write to file and zip it
    filename = f"{PROJECT.BASE_DATA_FILENAME}.txt"
    with open(filename, "w") as file:
        file.write(txt)
    zipfn = f"{filename}.zip"
    zip_file(filename, zipfn)

    # Restore previous CWD
    silently_remove(filename)
    os.chdir(old_cwd)

    return f"{PROJECT.STATIC_FILES_PATH}{zipfn}"


def generate_json(entries: EntryList) -> str:
    """Generate JSON dictionary in standard format. Return file path."""

    # Change to static files dir
    old_cwd = os.getcwd()
    os.chdir(PROJECT.STATIC_FILES_PATH)

    # Format the entries according to a standard dictionary format
    dictionary_data = {
        "metadata": {
            "title": PROJECT.NAME,
            "description": PROJECT.DESCRIPTION,
            "license": PROJECT.LICENSE,
            "author": PROJECT.EDITOR,
            "email": PROJECT.EMAIL,
            "website": PROJECT.BASE_URL,
            "source": PROJECT.REPO_URL,
            "version": PROJECT.VERSION,
            "date": datetime.datetime.now(datetime.UTC).isoformat(),
            "language": {"source": "en", "target": "is"},
        },
        "entries": [],
    }

    # Add each entry to the dictionary
    for entry in entries:
        (
            word,
            definition,
            syllables,
            ipa_uk,
            ipa_us,
            page_num,
            freq,
            synonyms,
            antonyms,
        ) = entry
        entry_data = {
            "word": word,
            "definition": definition,
            "syllables": syllables,
            "ipa_uk": ipa_uk,
            "ipa_us": ipa_us,
            "page_num": page_num,
            "frequency": freq,
            "synonyms": synonyms,
            "antonyms": antonyms,
        }
        dictionary_data["entries"].append(entry_data)

    # Write to file and zip it
    filename = f"{PROJECT.BASE_DATA_FILENAME}.json"
    with open(filename, "w", encoding="utf-8") as file:
        std_json.dump(dictionary_data, file, ensure_ascii=False, indent=2)

    zipfn = f"{filename}.zip"
    zip_file(filename, zipfn)

    # Restore previous CWD
    silently_remove(filename)
    os.chdir(old_cwd)

    return f"{PROJECT.STATIC_FILES_PATH}{zipfn}"


def main() -> None:
    """Generate all dictionary files."""
    heavy = sys.argv[1:] and sys.argv[1] == "--heavy"
    light = sys.argv[1:] and sys.argv[1] == "--light"

    nltk.download("wordnet")

    print("Reading entries...")
    entries = read_all_entries()
    print(f"{len(entries)} entries read")

    if not light:
        print("Generating text")
        generate_text(entries)

        print("Generating CSV")
        generate_csv(entries, unlink_csv=True)

        print("Generating JSON")
        generate_json(entries)

    # if heavy:
    #     print("Generating macOS Dictionary")
    #     from macos import generate_macos_dictionary

    #     generate_macos_dictionary(entries)

    if heavy:
        print("Generating PDF")
        dictionary = {
            e[0]: e[1]
            for e in entries  # if e[0].startswith("a")
        }
        from pdf import generate_pdf

        generate_pdf(dictionary, "static/files/ensk.is.pdf")

    print("Generating SQLite3 database")
    generate_database(entries)


if __name__ == "__main__":
    """Command line invocation."""
    main()
