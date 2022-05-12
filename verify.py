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

"""

import re

from islenska import Bin
from tokenizer import tokenize

from util import read_pages, read_wordlist, parse_line

b = Bin()

r = read_pages()

IS_WORDS_WHITELIST = read_wordlist("data/is.whitelist.txt")

EN_WORDS_LIST = read_wordlist("data/wordlists/words.txt")
EN_WORDS_WHITELIST = read_wordlist("data/en.whitelist.txt")
EN_WORDS_LIST.extend(EN_WORDS_WHITELIST)

CATEGORIES = read_wordlist("data/catwords.txt")


def warn(s: str, pn: int, ln: int):
    print(f"{pn}:{ln} | {s}")


def check_punctuation(line: str, pn: int, ln: int):
    if line.strip() == "":
        warn("empty line", pn, ln)
    if "  " in line:
        warn("double spaces", pn, ln)
    if "{" in line or "}" in line:
        warn("curly brackets error", pn, ln)
    # if "sjá " in line:
    #     warn("'sjá' in line", pn, ln)
    if "=" in line:
        warn("= in line", pn, ln)
    if (
        line.endswith(" ")
        or line.endswith(";")
        or line.endswith(".")
        and not line.endswith("o.fl.")
        and not line.endswith("o.s.frv.")
    ):
        warn("line ends with non-alphabetic character", pn, ln)

    if line.count("[") != line.count("]"):
        warn("[] error", pn, ln)

    if line.count("(") != line.count(")"):
        warn("() error", pn, ln)


def check_spacing(line: str, pn: int, ln: int):
    if "\t" in line:
        warn("tab character", pn, ln)
    if "  " in line:
        warn("double spaces", pn, ln)


def strip_words_in_square_brackets(s: str) -> str:
    return re.sub(r"\[.+\]", "", s)


def check_bracket_use(line: str, pn: int, ln: int):
    lc = strip_words_in_square_brackets(line)

    if "~" in lc:
        print(line)
        warn("~ char outside brackets", pn, ln)


def check_phonetic_junk(s: str, pn: int, ln: int):
    comp = s.split()

    # if "'" in comp[0]:
    #     warn(f"PHON IN DEF: {comp[0]}", pn, ln)

    for c in comp[:3]:
        if c.startswith("(") and c.endswith(")"):
            warn(f"Phonetic junk {c}", pn, ln)

    # if len(comp) < 3:
    #     warn("Line has less than three components", pn, ln)
    # if comp[0] in CATEGORIES:
    #     warn("Missing word, first comp is category", pn, ln)
    # if comp[1] not in CATEGORIES and comp[2] not in CATEGORIES:
    #     warn("Category not in first three components", pn, ln)


def check_english_words(line: str, pn: int, ln: int):
    res = re.findall(r"\[([^\]]+)", line)
    s = " ".join([r.strip() for r in res])
    words = s.split()

    for entry in words:
        if not entry:
            continue
        for w in entry.split("/"):
            if w[0].isdigit() and w[-1].isdigit():
                continue
            if w.startswith("£"):
                continue
            w = re.sub(r"('s)$", "", w)
            w = (
                w.rstrip(",")
                .rstrip(")")
                .lstrip("(")
                .lstrip("'")
                .rstrip("'")
                .rstrip("-")
                .rstrip("!")
                .rstrip("?")
                .rstrip("—")
                .replace("(", "")
                .replace(")", "")
            )
            if "~" in w:
                continue
            if w not in EN_WORDS_LIST:
                wl = w.lower()
                if wl not in EN_WORDS_LIST:
                    warn(f"English Word: '{w}'", pn, ln)


def check_enword_def(line: str, pn: int, ln: int):
    (entry, definition) = parse_line(line)
    e = entry.strip()
    if "(" in e or ")" in e:
        warn(f"'{entry}' is fucked", pn, ln)
    if e not in EN_WORDS_LIST:
        warn(f"'{entry}' not in English word list", pn, ln)
        kr = e.replace("-", "")
        if kr in EN_WORDS_LIST:
            print(f"{e} --> {kr}")
        ks = e.replace("-", " ")
        if ks in EN_WORDS_LIST:
            print(f"{e} --> {ks}")
        kc = e[:1].upper() + e[1:]
        if kc in EN_WORDS_LIST:
            print(f"{e} --> {kc}")
        kd = e.replace(" ", "")
        if kd in EN_WORDS_LIST:
            print(f"{e} --> {kd}")


def check_icelandic_words(line: str, pn: int, ln: int):
    comp = line.split()
    if len(comp) < 3:
        warn("mangled formatting", pn, ln)
        return

    splidx = None
    try:
        if comp[1] in CATEGORIES:
            splidx = 1
        elif comp[2] in CATEGORIES:
            splidx = 2
        elif comp[3] in CATEGORIES:
            splidx = 3
        else:
            warn("no category set", pn, ln)
            return
    except Exception as e:
        warn(f"error parsing category etc.: {e}", pn, ln)
        return

    defcomp = comp[splidx + 1 :]
    defstr = strip_words_in_square_brackets(" ".join(defcomp))

    for t in tokenize(defstr):
        if t.kind != 6:
            continue

        txt = t.txt
        if txt in CATEGORIES:
            continue
        if txt in IS_WORDS_WHITELIST:
            continue

        res = b.lookup(txt)
        if not res[1]:
            txt = txt.strip("-").strip("-")
            res = b.lookup(txt)
            if not res[1]:
                warn(f"Icelandic Word: '{txt}' not found in BÍN", pn, ln)


def check_category(line: str, pn: int, ln: int):
    hascat = False
    for c in CATEGORIES:
        if f" {c} " in line:
            hascat = True
            break
    if not hascat:
        warn("no category for word", pn, ln)


for page_num, page in enumerate(r):
    for line_num, line in enumerate(page):
        pn = page_num + 1
        ln = line_num + 1
        # print(f"{pn}:{ln}| {line}")
        check_spacing(line, pn, ln)
        check_punctuation(line, pn, ln)
        # check_category(line, pn, ln)
        # check_bracket_use(line, pn, ln)
        # check_phonetic_junk(line, pn, ln)
        # check_icelandic_words(line, pn, ln)
        # check_english_words(line, pn, ln)
        # check_enword_def(line, pn, ln)
