#!/usr/bin/env python3

# Use pyhyphen to hyphenate words in a wordlist.

# ruff: noqa E402

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from util import read_wordlist


import hyphen as H

h = H.Hyphenator("en_US")

wdlist = read_wordlist(os.path.join(parentdir, "data/wordlists/nltk_words.txt"))
# print(len(wdlist), "words in wordlist")

SEPARATOR = "·"

hyphenations = {}

for word in wdlist:
    syllables = h.syllables(word)
    s = SEPARATOR.join(syllables)
    if not s:
        continue
    # print(f"{word}: {s}")
    hyphenations[word] = s

import json

print(json.dumps(hyphenations, indent=2, ensure_ascii=False))
