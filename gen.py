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


Generate SQLite database + other files from raw dictionary text files.


"""

import os
import sys
import csv
import shutil
import datetime
import subprocess

import sqlite_utils

from dict import read_pages, parse_line, page_for_word
from db import EnskDatabase, DB_FILENAME
from util import zip_file, read_json, silently_remove
from info import PROJECT_BASE_DATA_FILENAME, PROJECT_STATIC_FILES_PATH

EntryType = tuple[str, str, str, str, int]
EntryList = list[EntryType]


ENWORD_TO_IPA_UK = read_json("data/ipa/uk/en2ipa.json")
ENWORD_TO_IPA_US = read_json("data/ipa/us/en2ipa.json")


def ipa4entry(s: str, lang="uk") -> str | None:
    """Look up International Phonetic Alphabet spelling for word."""
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
    """Read all entries from dictionary text files and parse them."""
    r = read_pages()

    entries = []
    for line in r:
        wd = parse_line(line)
        w = wd[0]
        definition = wd[1]
        ipa_uk = ipa4entry(w, lang="uk") or ""
        ipa_us = ipa4entry(w, lang="us") or ""
        pn = page_for_word(w)
        entries.append(tuple([w, definition, ipa_uk, ipa_us, pn]))

    entries.sort(key=lambda d: d[0].lower())  # Sort alphabetically by word

    return entries


def delete_db() -> None:
    """Delete any pre-existing SQLite database file."""
    silently_remove(DB_FILENAME)


def add_entries_to_db(entries: EntryList) -> EnskDatabase:
    """Insert all entries into database."""
    db = EnskDatabase()
    for e in entries:
        db.add_entry(*e)

    db.conn().commit()

    return db


def add_metadata_to_db() -> EnskDatabase:
    """Add metadata to database."""
    db = EnskDatabase()
    db.add_metadata("name", "ensk.is")
    db.add_metadata("description", "Free and open English-Icelandic dictionary")
    db.add_metadata("license", "Public domain")
    db.add_metadata("website", "https://ensk.is")
    db.add_metadata("source", "https://github.com/sveinbjornt/ensk.is")
    db.add_metadata("editor", "Sveinbjorn Thordarson")
    db.add_metadata("editor_email", "sveinbjorn@sveinbjorn.org")
    db.add_metadata("generation_date", datetime.datetime.now(datetime.UTC).isoformat())
    return db


def generate_database(entries: EntryList) -> str:
    """Generate SQLite database and create a corresponding zip archive.
    Returns path to zip file."""

    # Remove pre-existing database file
    delete_db()

    # Create new db and add data
    db = add_metadata_to_db()
    db = add_entries_to_db(entries)
    sqlite_utils.Database(db.db_conn).table("dictionary").enable_fts(
        ("word", "definition")
    )
    db = optimize_db()

    # Zip it
    zipfn = f"{PROJECT_STATIC_FILES_PATH}{PROJECT_BASE_DATA_FILENAME}.db.zip"
    zip_file(DB_FILENAME, zipfn)

    return zipfn


def optimize_db() -> EnskDatabase:
    """Optimize database."""
    db = EnskDatabase()
    db.conn().cursor().execute(
        "CREATE INDEX idx_word ON dictionary(word COLLATE NOCASE)"
    )
    db.conn().cursor().execute("ANALYZE;")
    db.conn().cursor().execute("VACUUM;")
    db.conn().commit()
    return db


def generate_csv(entries: EntryList, unlink_csv: bool = False) -> str:
    """Generate zipped CSV file. Return file path."""
    fields = ["word", "definition", "ipa", "page_num"]

    # Change to static files dir
    old_cwd = os.getcwd()
    os.chdir(PROJECT_STATIC_FILES_PATH)

    # Write the CSV and zip it
    filename = f"{PROJECT_BASE_DATA_FILENAME}.csv"
    with open(filename, "w") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        csvwriter.writerows(entries)
    zipfn = f"{filename}.zip"
    zip_file(filename, zipfn)

    # Restore previous CWD
    # silently_remove(filename)
    os.chdir(old_cwd)

    return f"{PROJECT_STATIC_FILES_PATH}{zipfn}"


def generate_text(entries: EntryList) -> str:
    """Generate zipped text file w. all entries. Return file path."""

    # Change to static files dir
    old_cwd = os.getcwd()
    os.chdir(PROJECT_STATIC_FILES_PATH)

    # Generate full dictionary text
    txt = "\n".join([f"{e[0]} {e[1]}" for e in entries]).strip()

    # Write to file and zip it
    filename = f"{PROJECT_BASE_DATA_FILENAME}.txt"
    with open(filename, "w") as file:
        file.write(txt)
    zipfn = f"{filename}.zip"
    zip_file(filename, zipfn)

    # Restore previous CWD
    silently_remove(filename)
    os.chdir(old_cwd)

    return f"{PROJECT_STATIC_FILES_PATH}{zipfn}"


def generate_pdf(entries: EntryList) -> str:
    """Generate PDF. Return file path."""
    raise NotImplementedError


def generate_apple_dictionary(entries: EntryList, unlink_intermediates=True) -> str:
    """Generate Apple Dictionary file. Return file path."""

    # Delete any pre-existing Apple Dictionary files
    silently_remove(f"{PROJECT_STATIC_FILES_PATH}{PROJECT_BASE_DATA_FILENAME}.apple")
    silently_remove(
        f"{PROJECT_STATIC_FILES_PATH}{PROJECT_BASE_DATA_FILENAME}.dictionary"
    )

    print("Running pyglossary conversion to Apple Dictionary...")
    process = subprocess.Popen(
        [
            "pyglossary",
            f"{PROJECT_STATIC_FILES_PATH}/{PROJECT_BASE_DATA_FILENAME}.csv",
            "--read-format=Csv",
            f"{PROJECT_STATIC_FILES_PATH}/{PROJECT_BASE_DATA_FILENAME}.apple",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Print output as it comes
    for line in process.stdout:  # type: ignore
        print(line, end="")

    process.wait()
    if process.returncode != 0:
        print(f"pyglossary command failed with return code {process.returncode}")
        sys.exit(process.returncode)

    old_cwd = os.getcwd()

    # Change to the apple dictionary directory
    apple_dict_dir = f"{PROJECT_STATIC_FILES_PATH}{PROJECT_BASE_DATA_FILENAME}.apple"
    os.chdir(apple_dict_dir)
    print(f"Changed directory to: {os.getcwd()}")

    # Run make and stream output
    print("Running make...")
    process = subprocess.Popen(
        ["make"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )

    # Print output as it comes
    for line in process.stdout:  # type: ignore
        print(line, end="")

    process.wait()
    if process.returncode != 0:
        print(f"make command failed with return code {process.returncode}")
        sys.exit(process.returncode)

    os.chdir("..")  # Back to STATIC_FILES_PATH
    shutil.copytree(
        f"{PROJECT_BASE_DATA_FILENAME}.apple/objects/ensk_is_apple.dictionary",
        f"{PROJECT_BASE_DATA_FILENAME}.dictionary",
    )

    # Zip the dictionary
    zip_file(
        f"{PROJECT_BASE_DATA_FILENAME}.dictionary",
        f"{PROJECT_BASE_DATA_FILENAME}.dictionary.zip",
    )

    if unlink_intermediates:
        shutil.rmtree(f"{PROJECT_BASE_DATA_FILENAME}.apple")
        shutil.rmtree(f"{PROJECT_BASE_DATA_FILENAME}.dictionary")

    os.chdir(old_cwd)

    return f"{PROJECT_STATIC_FILES_PATH}{PROJECT_BASE_DATA_FILENAME}.dictionary.zip"


def main() -> None:
    print("Reading entries...")
    entries = read_all_entries()
    print(f"{len(entries)} entries read")

    print("Generating text")
    generate_text(entries)

    print("Generating CSV")
    generate_csv(entries, unlink_csv=True)

    # print("Generating Apple Dictionary")
    # generate_apple_dictionary(entries)

    # exit(0)

    print("Generating SQLite3 database")
    generate_database(entries)

    # print("Generating PDF")
    # generate_pdf(entries)


if __name__ == "__main__":
    """Command line invocation."""
    main()
