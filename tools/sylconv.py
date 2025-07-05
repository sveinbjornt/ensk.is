#!/usr/bin/env python3

# Convert this list of syllable-separated words to JSON index format.
# https://github.com/gautesolheim/25000-syllabified-words-list
#

# ruff: noqa E402

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from util import read_wordlist


wdlist = read_wordlist(os.path.join(parentdir, "data/syllables/mhyph2.txt"))

SEPARATOR = "·"

out = {}
for w in wdlist:
    org = w.replace("¥", "").strip()
    if not org:
        continue
    fixed = w.replace("¥", SEPARATOR).strip()
    out[org] = fixed

import json

print(json.dumps(out, ensure_ascii=False, indent=2))
