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


Dictionary database singleton.


"""

import os
import logging
import sqlite3
from pathlib import Path

from dict import CATEGORIES

DB_FILENAME = "dict.db"
CACHED_STATEMENTS = 1024
CACHE_SIZE_KB = 1024 * 32  # 32 MB


class EnskDatabase:
    _instance = None

    def __init__(self, read_only: bool = False):
        """Initialize the database."""
        self.db_conn = None
        self.read_only = read_only

    def __new__(cls, read_only: bool = False):
        """Singleton pattern."""
        if cls._instance is None:
            logging.info("Instantiating database")
            cls._instance = super().__new__(cls)

            basepath, _ = os.path.split(os.path.realpath(__file__))
            cls._dbpath = os.path.join(basepath, DB_FILENAME)
            cls.read_only = read_only
            # Create database file and schema if no DB file exists
            if not Path(cls._dbpath).is_file():
                cls._instance._create()
        return cls._instance

    def _create(self) -> None:
        """Create database file and generate database schema."""
        logging.info(f"Creating database {self._dbpath}")

        # Create database file
        conn = sqlite3.connect(self._dbpath)

        # Create dictionary table
        create_dictionary_table_sql = """
            CREATE TABLE dictionary (
                id INTEGER UNIQUE PRIMARY KEY NOT NULL,
                word TEXT,
                definition TEXT,
                syllables TEXT,
                ipa_uk TEXT,
                ipa_us TEXT,
                page_num INTEGER,
                freq INTEGER,
                synonyms TEXT,
                antonyms TEXT
            );
        """
        conn.cursor().execute(create_dictionary_table_sql)

        # Create metadata table
        create_metadata_table_sql = """
            CREATE TABLE metadata (
                key TEXT UNIQUE PRIMARY KEY NOT NULL,
                value TEXT
            );
        """
        conn.cursor().execute(create_metadata_table_sql)

    def reinstantiate(self, read_only: bool = False) -> "EnskDatabase":
        """Reinstantiate database."""
        EnskDatabase._instance = None
        return EnskDatabase.__new__(EnskDatabase, read_only=read_only)

    def conn(self) -> sqlite3.Connection:
        """Open database connection lazily."""
        if not self.db_conn:
            # Open database file via URI
            db_uri = f"file:{self._dbpath}"
            if self.read_only:
                db_uri += "?mode=ro"

            logging.info(f"Opening database connection at {db_uri}")
            self.db_conn = sqlite3.connect(
                db_uri,
                uri=True,
                check_same_thread=(self.read_only is False),
                cached_statements=CACHED_STATEMENTS,
            )

            # Set cache size
            self.db_conn.cursor().execute(f"PRAGMA cache_size = -{CACHE_SIZE_KB}")

            # Return rows as key-value dicts
            self.db_conn.row_factory = lambda c, r: dict(
                zip([col[0] for col in c.description], r)
            )

        return self.db_conn

    def add_entry(
        self,
        w: str,
        definition: str,
        syllables: str,
        ipa_uk: str,
        ipa_us: str,
        page_num: int,
        freq: int,
        synonyms: str,
        antonyms: str,
        commit: bool = False,  # Whether to commit changes to database immediately
    ) -> None:
        """Add a single entry to the dictionary."""
        conn = self.conn()
        conn.cursor().execute(
            "INSERT INTO dictionary (word, definition, syllables, ipa_uk, ipa_us, page_num, freq, synonyms, antonyms) VALUES (?,?,?,?,?,?,?,?,?)",
            [
                w,
                definition,
                syllables,
                ipa_uk,
                ipa_us,
                page_num,
                freq,
                synonyms,
                antonyms,
            ],
        )
        if commit:
            conn.commit()

    def add_metadata(self, key: str, value: str) -> None:
        """Add a single metadata entry to the database."""
        conn = self.conn()
        conn.cursor().execute(
            "INSERT INTO metadata (key, value) VALUES (?,?)", [key, value]
        )
        conn.commit()

    def read_metadata(self) -> dict[str, str]:
        """Read all metadata entries from the database."""
        selected = self.conn().cursor().execute("SELECT * FROM metadata")
        res = self._consume(selected, order=False)
        return {row["key"]: row["value"] for row in res}

    def _consume(self, cursor: sqlite3.Cursor, order: bool = True) -> list[dict]:
        """Consume cursor and return list of rows."""
        res = list(cursor)  # Consume generator into list
        if order:
            res.sort(key=lambda x: x["word"].lower())
        return res

    def read_all_entries(self) -> list[dict]:
        """Read and return all entries."""
        selected = self.conn().cursor().execute("SELECT * FROM dictionary")
        return self._consume(selected)

    def read_all_original(self) -> list[dict]:
        """Read and return all original entries from the dictionary."""
        selected = (
            self.conn().cursor().execute("SELECT * FROM dictionary WHERE page_num!=0")
        )
        return self._consume(selected)

    def read_all_additions(self) -> list[dict]:
        """Read and return all entries not present in the original dictionary."""
        selected = (
            self.conn().cursor().execute("SELECT * FROM dictionary WHERE page_num=0")
        )
        return self._consume(selected)

    def read_all_duplicates(self) -> list[dict]:
        """Read and return all duplicate (i.e. same word) entries present in the dictionary
        as a dict keyed by word."""
        selected = (
            self.conn()
            .cursor()
            .execute(
                "SELECT *, COUNT(*) FROM dictionary GROUP BY lower(word) HAVING COUNT(*) > 1"
            )
        )
        return self._consume(selected)

    def read_all_without_ipa(self, lang: str = "uk") -> list[dict]:
        """Read and return all entries without IPA."""
        assert lang in ["uk", "us"]
        ipa_col = "ipa_" + lang
        selected = (
            self.conn()
            .cursor()
            .execute("SELECT * FROM dictionary WHERE ?=''", [ipa_col])
        )
        return self._consume(selected)

    def read_all_with_no_page(self) -> list[dict]:
        """Read and return all entries without IPA."""
        selected = (
            self.conn().cursor().execute("SELECT * FROM dictionary WHERE page_num=0")
        )
        return self._consume(selected)

    def read_all_capitalized(self) -> list[dict]:
        """Read and return all entries with capitalized words."""
        selected = (
            self.conn()
            .cursor()
            .execute("SELECT * FROM dictionary WHERE word GLOB '[A-Z]*'")
        )
        return self._consume(selected)

    def read_all_with_multiple_words(self) -> list[dict]:
        """Read and return all entries consisting of multiple words."""
        selected = (
            self.conn()
            .cursor()
            .execute("SELECT * FROM dictionary WHERE word LIKE '% %'")
        )
        return self._consume(selected)

    def read_all_in_wordcat(self, cat: str) -> list[dict]:
        """Read all entries in a given word category."""

        # Return empty list if category is not valid
        if cat + "." not in CATEGORIES:
            return []

        selected = (
            self.conn()
            .cursor()
            .execute(
                "SELECT * FROM dictionary WHERE definition LIKE ?",
                [f"%{cat}. %"],
            )
        )
        return self._consume(selected)
