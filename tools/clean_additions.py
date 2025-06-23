#!/usr/bin/env python3

# Find all words in the database that are considered
# additions but are not in the _add.txt file. This
# lets us discover which words present in the original
# dictionary lack a page number due to changes.

# ruff: noqa E402

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


from dict import read_raw_pages, parse_line
from db import EnskDatabase

e = EnskDatabase()

add = [x["word"] for x in e.read_all_additions()]

raw = read_raw_pages(fn="_add.txt")["_add"]

radd = []

for line in raw:
    w, d = parse_line(line)
    radd.append(w)


for a in add:
    if a not in radd:
        print(a)
