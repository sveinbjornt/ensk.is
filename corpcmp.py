#!/usr/bin/env python3

from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize

from nltk.stem import WordNetLemmatizer

from db import EnskDatabase

lemmatizer = WordNetLemmatizer()


with open("texts/ma.txt", "r") as f:
    corpus = f.read()

# Initialize database singleton
e = EnskDatabase()

# Read all dictionary entries into memory
res = e.read_all_entries()

dict_words = [e["word"].lower() for e in res]


words = word_tokenize(corpus)
ps = PorterStemmer()
for w in words:
    # rootWord = ps.stem(w)
    lemma = lemmatizer.lemmatize(w)
    if lemma not in dict_words and lemma.lower() not in dict_words:
        print(lemma)
