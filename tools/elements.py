#!/usr/bin/env python3

# ruff: noqa E402

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import re

from routes.core import entries
from dict import synonyms_for_word

matches = [e for e in entries if "(frumefni)" in e["definition"]]

for e in matches:
    w = e["word"]
    defn = e["definition"]
    syn = synonyms_for_word(w)
    # print(w, ":", syn)
    if not syn:
        continue

    # print(w)
    atomic_number = None
    periodic_name = None
    # print(syn)
    for s in syn:
        # print(f"[synonym] {s}")
        rx = re.compile(rf"atomic number (\d+)", re.IGNORECASE)
        m = rx.search(s)
        if m:
            atomic_number = m.group(1)
            # print(f"{atomic_number}")
        if len(s) == 2 and s[0].isupper() and s[1].islower():
            # print(s)
            periodic_name = s

    # print(f"{w}: {atomic_number}, {periodic_name}")

    if atomic_number and periodic_name:
        d = defn.replace(
            " (frumefni)",
            f" (frumefnið {periodic_name},  {atomic_number} í lotukerfinu)",
        )
        print(f"{w} {d}")

    # print(f"[word]")
