#!/usr/bin/python3

# ruff: noqa E402

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from gen.gen import read_all_entries

fpath = os.path.join(currentdir, "english_icelandic_dictionary.txt")
with open(fpath, "r", encoding="utf-8") as f:
    lines = f.readlines()
lines = [line.strip() for line in lines if line.strip() and not line.startswith("#")]

ent = read_all_entries()
entries = {}
for e in ent:
    entries[e[0]] = e[1]

# for e in entries:
#     print(f"{e} {entries[e]}")

keys = list(entries.keys())

for line in lines:
    (word, dfn) = line.split(":", 1)
    # print(f"{word} {dfn}")
    wdefs = [d.strip().lower() for d in dfn.split(";") if d.strip()]
    # if word in keys:
    #     # print(word)
    #     # print(wdefs)
    #     for d in wdefs:
    #         if d not in entries[word].lower():
    #             print(line)
    #             break
    if word not in keys and " " not in word:
        print(line)
