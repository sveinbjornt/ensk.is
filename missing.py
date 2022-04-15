#!/usr/bin/env python3


from db import EnskDatabase
from pprint import pprint
from util import read_wordlist

# Initialize database singleton
e = EnskDatabase()

# Read all dictionary entries into memory
res = e.read_all_entries()

dict_words = [e["word"] for e in res]


top10k = read_wordlist("data/wordlists/google-10000-english-usa.txt")

for t in top10k:
    if t not in dict_words:
        print(t)