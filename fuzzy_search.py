#!/usr/bin/env python3

import sys

from rapidfuzz import process, fuzz

from dict import read_all_words

words = read_all_words()

r = process.extract(sys.argv[1], words, scorer=fuzz.WRatio, limit=10)
print(r)
