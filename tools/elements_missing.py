#!/usr/bin/env python3

# Find element names that are missing from the dictionary.

# ruff: noqa E402

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import periodictable

from routes.core import all_words
from routes.core import entries


def def_for_word(word: str):
    """Return the definition for a given word."""
    for e in entries:
        if e["word"].lower() == word.lower():
            # Found the entry, return its definition
            return e["definition"]


c = 0
for el in periodictable.elements:
    # print(el.name)
    # if el.name not in all_words:
    #     print(
    #         f"{el.name} n. {el.name} (frumefnið {el.symbol},  {el.number} í lotukerfinu)"
    #     )
    # else:
    #     print(f"{el.name}: {def_for_word(el.name)}")
    d = def_for_word(el.name)
    assert el.symbol in d, f"{el.symbol} not in {d}"
    assert str(el.number) in d
    c += 1

    # print("%s %s"%(el.symbol,el.name))
print(c)
