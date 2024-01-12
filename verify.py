#!/usr/bin/env python3
"""

    Ensk.is - Free and open English-Icelandic dictionary

    Copyright (c) 2021-2024, Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>
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


    Check formatting and integrity of raw text dictionary entries.


"""


from typing import Union

import re

from islenska import Bin
from tokenizer import tokenize, TOK

from dict import read_raw_pages, parse_line, read_all_words
from util import read_wordlist


IS_WORDS_WHITELIST = read_wordlist("data/is.whitelist.txt")

EN_WORDS_LIST = read_wordlist("data/wordlists/words.txt")
EN_WORDS_WHITELIST = read_wordlist("data/en.whitelist.txt")
EN_WORDS_LIST.extend(EN_WORDS_WHITELIST)

CATEGORIES = read_wordlist("data/catwords.txt")

ALL_DICT_WORDS = read_all_words()

bin = None  # Lazily initialized BÍN instance

warnings = 0


def warn(s: str, pn: Union[int, str], ln: int):
    """Print warning message w. relevant file and line info."""
    print(f"{pn}:{ln} | {s}")
    global warnings
    warnings += 1


def strip_words_in_square_brackets(s: str) -> str:
    """Strip words in square brackets from string."""
    sn = re.sub(r"\[.+\]", "", s)
    sn = re.sub(r"%", "", sn)
    return sn


def check_punctuation(line: str, pn, ln: int):
    """Ensure that punctuation is used correctly in entry."""
    if line.strip() == "":
        warn("empty line", pn, ln)
    if "  " in line:
        warn("double spaces", pn, ln)
    if "{" in line or "}" in line:
        warn("curly brackets error", pn, ln)
    if "=" in line:
        warn("= in line", pn, ln)
    if (
        line.endswith(" ")
        or line.endswith(";")
        or line.endswith(".")
        and not line.endswith("o.fl.")
        and not line.endswith("o.s.frv.")
        and not line.endswith("o.þ.h.")
    ):
        warn("line ends with non-alphabetic character", pn, ln)

    if line.count("[") != line.count("]"):
        warn("[] error", pn, ln)

    if line.count("(") != line.count(")"):
        warn("() error", pn, ln)

    if line.count("%") % 2 != 0:
        warn("% error", pn, ln)

    if "[ " in line:
        warn("[ space error", pn, ln)
    if " ]" in line:
        warn("] space error", pn, ln)


def check_spacing(line: str, pn, ln: int):
    """Look for malformed whitespace in entry."""
    if "\t" in line:
        warn("tab character", pn, ln)
    if "  " in line:
        warn("double spaces", pn, ln)


def check_category(line: str, pn, ln: int):
    """Make sure word has a category."""
    hascat = False
    for c in CATEGORIES:
        if f" {c} " in line:
            hascat = True
            break
    if not hascat:
        warn("no category for word", pn, ln)


def check_bracket_use(line: str, pn, ln: int):
    """Make sure that brackets are used correctly."""
    lc = strip_words_in_square_brackets(line)

    if "~" in lc:
        warn("~ char outside brackets", pn, ln)


def check_intradict_refs(line: str, pn, ln: int):
    """Make sure all intra-dictionary references are valid, i.e. exist."""
    if "%[" not in line:
        return

    words_matched = re.findall(r"%\[(.+?)\]%", line)
    for w in words_matched:
        if w not in ALL_DICT_WORDS:
            warn(f"Intra-dictionary reference to non-existent word {w}", pn, ln)


def check_enword_def(line: str, pn, ln: int):
    """Check that English word is valid."""
    (entry, _) = parse_line(line)
    e = entry.strip()
    if "," in e:
        warn(f"Comma in entry: {e}", pn, ln)
    if "." in e:
        warn(f"Period in entry: {e}", pn, ln)
    if ";" in e:
        warn(f"Semicomma in entry: {e}", pn, ln)

    if "(" in e or ")" in e:
        warn(f"'{entry}' is fucked", pn, ln)

    if " " in e:
        words = e.split()
    else:
        words = [e]

    for w in words:
        e = w
        if e not in EN_WORDS_LIST:
            if e.lower() not in EN_WORDS_LIST and e.capitalize() not in EN_WORDS_LIST:
                warn(f"'{entry}' not in English word list", pn, ln)


def check_icelandic_words(line: str, pn, ln: int):
    """Inspect all Icelandic words in definition, make sure that they
    are present in modern Icelandic vocabulary (BÍN)."""
    (_, definition) = parse_line(line)

    # Strip all English words included in definition
    defstr = strip_words_in_square_brackets(definition)

    # Lazily instantiate BÍN
    global bin
    if not bin:
        bin = Bin()

    for t in tokenize(defstr):
        if t.kind != TOK.WORD:  # We're only interested in words
            continue

        txt = t.txt
        if txt in CATEGORIES:
            continue
        if txt in IS_WORDS_WHITELIST:
            continue

        res = bin.lookup(txt)
        if not res[1]:
            txt = txt.strip("-")
            res = bin.lookup(txt)
            if not res[1]:
                warn(f"Icelandic word not found in BÍN: '{txt}' ", pn, ln)
                # print(defstr)


def check_missing():
    """Check integrity of missing.txt file."""
    words = read_wordlist("missing.txt", unique=False)
    unique = list(set(words))
    # print(len(words))
    # print(len(unique))
    # print(words[-10:])
    # print(unique[-10:])

    if len(words) != len(unique):
        already = set()
        for w in words:
            if words.count(w) > 1 and w not in already:
                already.add(w)
                print(f"Duplicate word in missing.txt: {w}")
        exit(1)


def verify():
    """Main program function."""

    r = read_raw_pages()

    for letter, lines in r.items():
        for ln, line in enumerate(lines):
            ln = ln + 1
            check_spacing(line, letter, ln)
            check_punctuation(line, letter, ln)
            check_category(line, letter, ln)
            check_bracket_use(line, letter, ln)
            check_intradict_refs(line, letter, ln)
            # check_icelandic_words(line, letter, ln)
            # check_english_words(line, letter, ln)
            # check_enword_def(line, letter, ln)

    check_missing()

    exit(warnings > 0)


if __name__ == "__main__":
    verify()
