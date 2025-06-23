#!/usr/bin/env python3

# ruff: noqa E402

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from routes.core import all_words, KNOWN_MISSING_WORDS
from dict import linked_synonyms_for_word


missing_synonyms = set()
for w in all_words:
    s = linked_synonyms_for_word(w, all_words)
    s = [
        syn["word"]
        for syn in s
        if syn["exists"] is False
        and " " not in syn["word"]
        and syn["word"] not in KNOWN_MISSING_WORDS
    ]
    missing_synonyms.update(s)

print("Missing synonyms:")
for w in sorted(missing_synonyms):
    print(w)
