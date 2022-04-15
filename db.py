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


    Dictionary database singleton.


"""


from typing import List, Dict

import logging
import sqlite3
from pathlib import Path


DB_FILENAME = "dict.db"


class EnskDatabase(object):
    _instance = None
    _dbname = DB_FILENAME

    def __init__(self):
        self.db_conn = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            print("Instantiating database")
            cls._instance = super(EnskDatabase, cls).__new__(cls)
            # Create database file and schema if no DB file exists
            if not Path(cls._dbname).is_file():
                cls._instance.create()

        return cls._instance

    def conn(self, read_only: bool = False) -> sqlite3.Connection:
        """Open database connection lazily."""
        if not self.db_conn:
            # Open database file in read-only mode via URI
            db_uri = f"file:{self._dbname}"
            if read_only:
                db_uri += "?mode=ro"
            print(f"Opening database connection at {db_uri}")
            self.db_conn = sqlite3.connect(db_uri, uri=True, check_same_thread=False)

            # Return rows as key-value dicts
            self.db_conn.row_factory = lambda c, r: dict(
                zip([col[0] for col in c.description], r)
            )

        return self.db_conn

    def create(self) -> None:
        """Create database file and generate database schema."""
        print(f"Creating database {self._dbname}")

        # Create database file
        conn = sqlite3.connect(self._dbname)

        # Create table
        create_table_sql = """
            CREATE TABLE dictionary (
                id INTEGER UNIQUE PRIMARY KEY NOT NULL,
                word TEXT,
                definition TEXT,
                ipa TEXT,
                page_num INTEGER
            );
        """

        conn.cursor().execute(create_table_sql)

    def add_entry(self, w: str, definition: str, ipa: str, page_num: int) -> None:
        """Add a single entry to the dictionary."""
        conn = self.conn()
        conn.cursor().execute(
            "INSERT INTO dictionary (word, definition, ipa, page_num) VALUES (?,?,?,?)",
            [w, definition, ipa, page_num],
        )
        conn.commit()

    def read_all_entries(self) -> List[Dict]:
        """Read and return all entries for word query."""
        conn = self.conn()
        sql = conn.cursor().execute("SELECT * FROM dictionary")
        return list(sql)  # Consume generator into list
