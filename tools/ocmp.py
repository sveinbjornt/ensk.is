#!/usr/bin/env python3

# ruff: noqa E402

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


import json

from db import EnskDatabase

from util import read_wordlist

all_en = read_wordlist(
    "/Users/sveinbjorn/Projects/ensk.is/data/wordlists/450k_words.txt"
)


# Initialize database singleton
e = EnskDatabase()

# Read all dictionary entries into memory
res = e.read_all_entries()

dict_words = [e["word"].lower() for e in res]


with open("parsed_dictionary.json", "r") as f:
    parsed_dictionary = json.load(f)

parsed = [p["headword"].lower() for p in parsed_dictionary]

# print(len(parsed))
# print(len(dict_words))

# Print all headwords that are not in the dictionary
# for entry in parsed_dictionary:
#     hw = entry["headword"]

#     if " " in hw or len(hw) <= 2:
#         continue

#     hwlower = hw.lower()

#     if hw not in all_en:
#         continue

#     if hwlower not in dict_words:
#         print(hw)

# Print all words in the dictionary that are not in the parsed dictionary
# for w in dict_words:
#     if w not in parsed:
#         print(w)


missing = read_wordlist("missing.txt")

for w in missing:
    if w in parsed:
        print(w)
