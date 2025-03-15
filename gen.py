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
from info import PROJECT


EntryType = tuple[str, str, str, str, int]
EntryList = list[EntryType]


ENWORD_TO_IPA_UK = read_json("data/ipa/uk/en2ipa.json")
ENWORD_TO_IPA_US = read_json("data/ipa/us/en2ipa.json")


def ipa4entry(s: str, lang: str = "uk") -> str | None:
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


def generate_database(entries: EntryList) -> str:
    """Generate SQLite database and create a corresponding zip archive.
    Returns path to zip file."""

    # Remove pre-existing database file
    delete_db()

    # Create new db and add data
    add_metadata_to_db()
    add_entries_to_db(entries)
    optimize_db()

    # Zip it
    zipfn = f"{PROJECT.STATIC_FILES_PATH}{PROJECT.BASE_DATA_FILENAME}.db.zip"
    zip_file(DB_FILENAME, zipfn)

    return zipfn


def delete_db() -> None:
    """Delete any pre-existing SQLite database file."""
    silently_remove(DB_FILENAME)


def add_metadata_to_db() -> None:
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


def add_entries_to_db(entries: EntryList) -> None:
    """Insert all entries into database."""
    db = EnskDatabase()
    for e in entries:
        db.add_entry(*e)

    db.conn().commit()


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
    fields = ["word", "definition", "ipa_uk", "ipa_us", "page_num"]

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


def generate_pdf(entries: EntryList) -> str:
    """Generate PDF. Return file path."""
    raise NotImplementedError


def generate_apple_dictionary(
    entries: EntryList, unlink_intermediates: bool = True
) -> str:
    """Generate Apple Dictionary file. Return file path."""

    # Delete any pre-existing Apple Dictionary files
    silently_remove(f"{PROJECT.STATIC_FILES_PATH}{PROJECT.BASE_DATA_FILENAME}.apple")
    silently_remove(
        f"{PROJECT.STATIC_FILES_PATH}{PROJECT.BASE_DATA_FILENAME}.dictionary"
    )

    print("Running pyglossary conversion to Apple Dictionary...")
    process = subprocess.Popen(
        [
            "pyglossary",
            f"{PROJECT.STATIC_FILES_PATH}/{PROJECT.BASE_DATA_FILENAME}.csv",
            "--read-format=Csv",
            f"{PROJECT.STATIC_FILES_PATH}/{PROJECT.BASE_DATA_FILENAME}.apple",
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
    apple_dict_dir = f"{PROJECT.STATIC_FILES_PATH}{PROJECT.BASE_DATA_FILENAME}.apple"
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
    # Move the resulting dictionary bundle to the static files root
    shutil.copytree(
        f"{PROJECT.BASE_DATA_FILENAME}.apple/objects/ensk_is_apple.dictionary",
        f"{PROJECT.BASE_DATA_FILENAME}.dictionary",
    )

    # Zip it
    zip_file(
        f"{PROJECT.BASE_DATA_FILENAME}.dictionary",
        f"{PROJECT.BASE_DATA_FILENAME}.dictionary.zip",
    )

    if unlink_intermediates:
        silently_remove(f"{PROJECT.BASE_DATA_FILENAME}.apple")
        silently_remove(f"{PROJECT.BASE_DATA_FILENAME}.dictionary")

    os.chdir(old_cwd)

    return f"{PROJECT.STATIC_FILES_PATH}{PROJECT.BASE_DATA_FILENAME}.dictionary.zip"


from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, FrameBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import string
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def create_dictionary_pdf(dictionary_data, output_file, columns=2):

    pdfmetrics.registerFont(TTFont("EBGaramond", "fonts/EBGaramond.ttf"))
    # pdfmetrics.registerFont(TTFont("EBGaramond-Bold", "fonts/EBGaramond-Bold.ttf"))

    # Set up document
    page_width, page_height = A4
    margin = 2 * cm

    # Calculate column layout
    col_width = (page_width - 2*margin - (columns-1)*0.5*cm) / columns
    col_height = page_height - 2*margin
    
    # Create frames for each column (one frame per column)
    frames = []
    for i in range(columns):
        x = margin + i * (col_width + 0.5*cm)
        frame = Frame(x, margin, col_width, col_height, leftPadding=0, bottomPadding=0, 
                      rightPadding=0, topPadding=0, id=f'col{i}')
        frames.append(frame)
    
    # Create document template with frames
    doc = BaseDocTemplate(output_file, pagesize=A4)
    template = PageTemplate(id='columns', frames=frames)
    doc.addPageTemplates(template)
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,  # Center
        spaceAfter=20
    )
    
    # Section style for letters
    section_style = ParagraphStyle(
        'section',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=10,
        spaceAfter=5
    )
    
    # Entry style
    entry_style = ParagraphStyle(
        'entry',
        parent=styles['Normal'],
        leading=12,  # Tighter line spacing
        spaceBefore=4,
        spaceAfter=0,
        firstLineIndent=-0*cm,  # Hanging indent
        leftIndent=0*cm,
        fontName="EBGaramond"
    )
    
    # Create content
    content = []
    
    # Add title to the first column
    content.append(Paragraph("English-Icelandic Dictionary", title_style))
    
    # Group entries by first letter
    grouped_entries = {}
    for english, icelandic in dictionary_data.items():
        first_letter = english[0].upper()
        if first_letter not in grouped_entries:
            grouped_entries[first_letter] = []
        grouped_entries[first_letter].append((english, icelandic))
    
    # Process each letter
    for letter in string.ascii_uppercase:
        if letter in grouped_entries:
            # Add letter header
            content.append(Paragraph(letter, section_style))
            
            # Add entries
            for english, icelandic in grouped_entries[letter]:
                # Format like a real dictionary: bold headword followed by definition
                entry_text = f"<b>{english}</b> {icelandic}"
                content.append(Paragraph(entry_text, entry_style))
    
    # Build document
    doc.build(content)



def main() -> None:
    print("Reading entries...")
    entries = read_all_entries()
    print(f"{len(entries)} entries read")

    dictionary = {
        e[0]: e[1] for e in entries
    }

    # dictionary = dictionary[:1000]

    create_dictionary_pdf(dictionary, "english_icelandic_dictionary.pdf", columns=3)

    exit(0)

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
