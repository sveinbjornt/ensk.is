#!/usr/bin/env python3
#
# Sort all additions in _add.txt alphabetically
#

from dict import read_raw_pages, parse_line
from db import EnskDatabase

from pprint import pprint

e = EnskDatabase()


raw = read_raw_pages(fn="_add.txt")["_add"]

radd = []

raw = list(raw)

raw = sorted(raw, key=lambda x: x[0])

# pprint(raw)

for line in raw:
    print(line)
