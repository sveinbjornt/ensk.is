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

import os
from collections import defaultdict
from typing import Any
import orjson as json

from util import read_wordlist


CATEGORIES = frozenset(read_wordlist("data/catwords.txt"))

TXT_SUFFIX = ".txt"


def read_raw_pages(fn: str | None = None) -> dict[str, list]:
    """Read all text files in the data/dict directory,
    return as an alphabetically indexed dict of lines."""
    base_path = "data/dict/"
    files = sorted(os.listdir(base_path))
    result = defaultdict(lambda: [])

    for file in files:
        if fn and file != fn:
            continue
        fp = os.path.join(base_path, file)
        if not os.path.isfile(fp):
            continue
        if not file.endswith(TXT_SUFFIX):
            continue

        with open(fp, "r") as f:
            file_contents = f.read()
        lines = file_contents.split("\n")

        for ln in lines:
            # Skip all empty lines and comments
            lns = ln.strip()
            if not lns or lns.startswith("#"):
                continue
            keyname = file[: -len(TXT_SUFFIX)]
            result[keyname].append(ln)

    return result


def read_pages() -> list[str]:
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
        w, _ = parse_line(line)
        words.append(w)
    words.sort(key=lambda x: x.lower())
    return words


def parse_line(s: str) -> tuple[str, str]:
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


def unpack_definition(s: str) -> dict[str, list[str]]:
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


WORD_TO_HYPHENATION = None


def hyphenation_for_word(w: str) -> str:
    """Look up the hyphenation for a given word in the dictionary."""
    global WORD_TO_HYPHENATION
    if not WORD_TO_HYPHENATION:
        with open("data/hyph/hyphenations.json", "r") as file:
            WORD_TO_HYPHENATION = json.loads(file.read())
    return WORD_TO_HYPHENATION.get(w, "")


SYLLABLES_SEPARATOR = "·"
SYLLABLES_LOOKUP = None
syllable_tokenizer = None


def syllables_for_word(w: str) -> str:
    """Tokenize a word into syllables."""
    if not w:
        return ""

    # First, try to look up the word in the syllables lookup
    global SYLLABLES_LOOKUP
    if not SYLLABLES_LOOKUP:
        with open("data/syllables/syllables.json", "r") as file:
            SYLLABLES_LOOKUP = json.loads(file.read())

    s = SYLLABLES_LOOKUP.get(w)
    if s:
        return s

    # If the word is not found in the lookup, check if it's a multi-word
    # phrase and look up each word separately
    split_word = w.split()
    if len(split_word) > 1:
        syl4wds = [SYLLABLES_LOOKUP.get(s) for s in split_word]
        if all(syl4wds):
            return SYLLABLES_SEPARATOR.join(syl4wds)

    # If not found, use the NLTK syllable tokenizer
    from nltk.tokenize import SyllableTokenizer

    global syllable_tokenizer
    if syllable_tokenizer is None:
        syllable_tokenizer = SyllableTokenizer()

    tokens = []
    for subw in split_word:
        t = syllable_tokenizer.tokenize(subw)
        tokens.extend(t)

    if not tokens:
        return ""

    return SYLLABLES_SEPARATOR.join(tokens)


def synonyms_for_word(w: str) -> list[str]:
    """Look up synonyms for a given word in the dictionary."""
    if not w:
        return []

    from itertools import chain

    try:
        from nltk.corpus import wordnet as wn
    except Exception:
        return []

    s = wn.synsets(w)
    synonyms = set(chain.from_iterable([wd.lemma_names() for wd in s if wd]))
    synonyms.discard(w)  # Remove the word itself
    synonyms = list(synonyms)
    synonyms.sort(key=lambda x: x.lower())
    synonyms = [syn.replace("_", " ") for syn in synonyms if len(syn) > 1]

    def is_not_name(syn: str) -> bool:
        """Check if a synonym is a name (i.e. starts with a capital letter)."""
        return not (
            " " in syn
            and syn[0].isupper()
            and syn[1].islower()
            and syn.split()[1][0].isupper()
        )

    final: list[str] = list(filter(is_not_name, synonyms))

    return final


def linked_synonyms_for_word(w: str, wordlist: list[str]) -> list[dict[str, Any]]:
    """Look up synonyms for a given word in the dictionary,
    and return them as a list of HTML links."""
    synonyms = synonyms_for_word(w)
    if not synonyms:
        return []

    ls = []
    for syn in synonyms:
        ls.append(
            {
                "word": syn,
                "exists": syn in wordlist or syn.lower() in wordlist,
            }
        )
    return ls


FREQ_MAP = None
FREQ_DESC = {
    -1: "",
    0: "mjög algengt",
    1: "algengt",
    2: "almennt",
    3: "óalgengt",
    4: "sjaldgæft",
    5: "mjög sjaldgæft",
}


def freq_for_word(w: str) -> int:
    """Look up the frequency of a word in the dictionary."""
    if not w:
        return -1

    # Lazy-load the frequency map from JSON file
    global FREQ_MAP
    if not FREQ_MAP:
        with open("data/freq/frequency.json", "r") as file:
            FREQ_MAP = json.loads(file.read())

    freq = FREQ_MAP.get(w)
    if freq is None:
        freq = FREQ_MAP.get(w.lower(), -1)

    if freq is None:
        return -1


DEFAULT_MISSING_COLOR = "#FFF"  # Default color for missing frequency

FREQ_COLOR = {
    0: "#228B22",
    1: "#32CD32",
    2: "#DAA520",
    3: "#FFA500",
    4: "#FF6347",
    5: "#B22222",
}


def color_for_freq(freq: int) -> str:
    """Return a color for a given frequency."""
    if freq < 0 or freq > 5:
        return DEFAULT_MISSING_COLOR  # Black for out of range
    return FREQ_COLOR.get(freq, DEFAULT_MISSING_COLOR)  # Default to black if not found
