#!/usr/bin/env python3

# Use Morfessor to segment words into morphemes.

# ruff: noqa E402

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from util import read_wordlist

import morfessor

model_file = os.path.join(currentdir, "morph.bin")
io = morfessor.MorfessorIO()
model = io.read_binary_model_file(model_file)

# word = input("Input word > ")
# for segmenting new words we use the viterbi_segment(compound) method
# print(model.viterbi_segment(word)[0])

wdlist = read_wordlist(os.path.join(parentdir, "data/wordlists/nltk_words.txt"))
# print(len(wdlist), "words in wordlist")

SEPARATOR = "·"

for word in wdlist:
    segments = model.viterbi_segment(word)[0]
    # if len(segments) > 1:
    #     print(f"{word} -> {' + '.join(segments)}")
    # else:
    #     print(f"{word} -> {segments[0]}")
    print(f"{word} -> {SEPARATOR.join(segments)}")
