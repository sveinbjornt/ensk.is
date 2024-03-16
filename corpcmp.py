#!/usr/bin/env python3
#
# Read a text file and print all words that are not in the dictionary
# (and not in the missing list). This is useful for finding words that
# are missing from the dictionary.
# TODO: Work directly on epubs instead of text files
#

import re

from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize

from nltk.stem import WordNetLemmatizer

from db import EnskDatabase

from util import read_wordlist

lemmatizer = WordNetLemmatizer()

missing = read_wordlist("missing.txt")

with open("texts/quine.txt", "r") as f:
    corpus = f.read()

# Initialize database singleton
e = EnskDatabase()

# Read all dictionary entries into memory
res = e.read_all_entries()

dict_words = [e["word"].lower() for e in res]


words = word_tokenize(corpus)
ps = PorterStemmer()
for w in words:
    w = re.sub(r"\d+$", "", w)
    if w.endswith("."):
        w = w[:-1]
    if w.endswith("…"):
        w = w[:-1]
    if w.endswith("ing") or w.endswith("ed"):
        continue
    if w.endswith("s"):
        n = w[:-1]
        if n in dict_words or n.lower() in dict_words:
            continue

    lemma = lemmatizer.lemmatize(w)
    llow = lemma.lower()
    if (
        lemma not in dict_words
        and llow not in dict_words
        and lemma not in missing
        and llow not in missing
    ):
        print(lemma)
