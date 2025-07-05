#!/usr/bin/env python3

# Use eng-syl NN to syllabify words in a wordlist.
# https://github.com/timo-liu/eng-syl
#

# ruff: noqa E402

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from util import read_wordlist


wdlist = read_wordlist(os.path.join(parentdir, "data/wordlists/nltk_words.txt"))
# print(len(wdlist), "words in wordlist")

SEPARATOR = "·"

from eng_syl.syllabify import Syllabel

syllabler = Syllabel()

# syllabler.syllabify("chomsky")

syllables = {}

for word in wdlist:
    syllables = syllabler.syllabify(word, return_list=True)
    s = SEPARATOR.join(syllables)
    if not s:
        continue
    print(f"{word}: {s}")
    # syllables[word] = s

import json

print(json.dumps(syllables, indent=2, ensure_ascii=False))
