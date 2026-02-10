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


Check formatting and integrity of raw text dictionary entries.


"""

import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import re
import time

from dict import read_raw_pages, parse_line, read_all_words
from util import read_wordlist, read_json


IS_WORDS_WHITELIST = frozenset(read_wordlist("data/is.whitelist.txt"))

EN_WORDS_LIST = frozenset(read_wordlist("data/wordlists/words.txt"))
EN_WORDS_WHITELIST = frozenset(read_wordlist("data/en.whitelist.txt"))
EN_WORDS_LIST = EN_WORDS_LIST.union(EN_WORDS_WHITELIST)
CATEGORIES = frozenset(read_wordlist("data/catwords.txt"))
CATEGORIES_NOPERIOD = frozenset([c.rstrip(".") for c in CATEGORIES])

ALL_DICT_WORDS = frozenset(read_all_words())

bin = None  # Lazily initialized BÍN instance

warnings = 0  # Global counter for warnings


def warn(s: str, pn: int | str, ln: int):
    """Print warning message w. relevant file and line info."""
    print(f"{pn}:{ln} | {s}")
    global warnings
    warnings += 1


def strip_words_in_square_brackets(s: str) -> str:
    """Strip words in square brackets from string."""
    sn = re.sub(r"\[.+\]", "", s)
    sn = re.sub(r"%", "", sn)
    return sn


def check_punctuation(line: str, pn: str, ln: int):
    """Ensure that punctuation is used correctly in entry."""
    if line.strip() == "":
        warn("empty line", pn, ln)
    if "  " in line:
        warn("double spaces", pn, ln)
    if "{" in line or "}" in line:
        warn("curly brackets error", pn, ln)
    if "=" in line:
        warn("= in line", pn, ln)
    if " , " in line:
        warn("comma with spaces", pn, ln)
    if " ; " in line:
        warn("semicolon with spaces", pn, ln)
    if " . " in line:
        warn("period with spaces", pn, ln)
    if " : " in line:
        warn("colon with spaces", pn, ln)
    if "%%" in line:
        warn("double percentage", pn, ln)
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

    if line.endswith(","):
        warn("line ends with comma", pn, ln)

    # segm = line.split(";")
    # for s in segm:
    #     if not "." in s:
    #         continue
    #     if len(s.rstrip(".")) < 3:
    #         warn("short segment", pn, ln)


def check_for_invisible_chars(line: str, pn: str, ln: int):
    """Look for invisible characters in entry."""
    invisible_chars = [
        "\u200b",  # Zero-width space
        "\u200c",  # Zero-width non-joiner
        "\u200d",  # Zero-width joiner
        "\u2060",  # Word joiner
        "\ufeff",  # Zero-width no-break space
        "\u00ad",  # Soft hyphen
    ]
    for c in invisible_chars:
        if c in line:
            warn(f"found invisible character: {c}", pn, ln)


def check_spacing(line: str, pn: str, ln: int):
    """Look for malformed whitespace in entry."""
    if "\t" in line:
        warn("tab character", pn, ln)
    if "  " in line:
        warn("double spaces", pn, ln)


def check_category(line: str, pn: str, ln: int):
    """Make sure word has a category."""
    hascat = False
    hasdupcat = False
    for c in CATEGORIES:
        if f" {c} " in line:
            hascat = True
            break
        if line.count(f"{c} ") > 1:  # and c not in ("stytt", "sks"):
            hasdupcat = True
            break

    if hasdupcat:
        warn("duplicate category", pn, ln)

    if not hascat:
        warn("no category for word", pn, ln)


def check_bracket_use(line: str, pn: str, ln: int):
    """Make sure that brackets are used correctly."""
    lc = strip_words_in_square_brackets(line)

    if "~" in lc:
        warn("~ char outside brackets", pn, ln)


def check_intradict_refs(line: str, pn: str, ln: int):
    """Make sure all intra-dictionary references exist."""
    if "%[" not in line:
        return

    words_matched = re.findall(r"%\[(.+?)\]%", line)
    for w in words_matched:
        if w not in ALL_DICT_WORDS:
            warn(f"Intra-dictionary reference to non-existent word {w}", pn, ln)


def check_enword_def(line: str, pn: str, ln: int):
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


def check_icelandic_words(line: str, pn: str, ln: int):
    """Inspect all Icelandic words in definition, make sure that
    they are present in modern Icelandic vocabulary (BÍN)."""
    from islenska import Bin
    from tokenizer import tokenize, TOK

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
        if txt in CATEGORIES or txt in CATEGORIES_NOPERIOD:
            continue
        if txt in IS_WORDS_WHITELIST:
            continue

        not_in_bin = False

        res = bin.lookup(txt)
        if not res[1]:
            txt = txt.strip("-")
            res = bin.lookup(txt)
            if not res[1]:
                not_in_bin = True

        if not_in_bin:
            import httpx

            res = httpx.get(f"https://malid.is/api_proxy/othekkt/{txt}")
            if res.status_code == 200:
                res = res.json()
                flettur = res[0]["othekktlisti"]["flettur"]
                if len(flettur) != 0 and txt in flettur:
                    continue
                else:
                    warn(f"Icelandic word not found: '{txt}' ", pn, ln)
            time.sleep(1)


def check_unlinked_abbreviation_refs(line: str, pn: str, ln: int):
    """Check for unlinked abbreviation references to existing words."""
    regex = r"stytt. á \[(.+?)\]"
    if re.search(regex, line):
        words_matched = re.findall(regex, line)
        for w in words_matched:
            if w in ALL_DICT_WORDS:
                warn(f"Unlinked abbreviation reference to existing word: {w}", pn, ln)
    regex2 = r"sks. á \[(.+?)\]"
    if re.search(regex2, line):
        words_matched = re.findall(regex2, line)
        for w in words_matched:
            if w in ALL_DICT_WORDS:
                warn(f"Unlinked abbreviation reference to existing word: {w}", pn, ln)


def check_missing():
    """Check integrity of data/missing.txt file."""
    words = read_wordlist("data/missing.txt", unique=False)
    unique = list(set(words))

    if len(words) != len(unique):
        already = set()
        for w in words:
            if words.count(w) > 1 and w not in already:
                already.add(w)
                print(f"Duplicate word in data/missing.txt: {w}")

    for w in unique:
        if w in ALL_DICT_WORDS:
            print(f"Word in data/missing.txt is already in dictionary: {w}")


def check_ipa_ignore_words():
    """Check that all words in data/ipa_ignore.txt are present in the dictionary and UK IPA dictionary."""
    ipa_ignore_words = read_wordlist("data/ipa_ignore.txt")
    uk_ipa_dict = read_json("data/ipa/uk/en2ipa.json")

    for word in ipa_ignore_words:
        if word not in ALL_DICT_WORDS:
            warn(
                f"Word '{word}' in data/ipa_ignore.txt is not present in the dictionary.",
                "data/ipa_ignore.txt",
                0,
            )
        if word in uk_ipa_dict:
            warn(
                f"Word '{word}' in data/ipa_ignore.txt IS present in the UK IPA dictionary. Remove it from data/ipa_ignore.txt.",
                "data/ipa_ignore.txt",
                0,
            )


def main():
    r = read_raw_pages()

    for letter, lines in r.items():
        for ln, line in enumerate(lines):
            ln = ln + 1
            check_spacing(line, letter, ln)
            check_for_invisible_chars(line, letter, ln)
            check_punctuation(line, letter, ln)
            check_category(line, letter, ln)
            check_bracket_use(line, letter, ln)
            check_intradict_refs(line, letter, ln)
            check_unlinked_abbreviation_refs(line, letter, ln)
            # check_icelandic_words(line, letter, ln)
            # check_enword_def(line, letter, ln)

    check_missing()
    check_ipa_ignore_words()

    exit(warnings > 0)


if __name__ == "__main__":
    main()
