#!/usr/bin/env python3
"""
Finds all synonyms for words in the dictionary and prints out those
that are not themselves in the dictionary.
"""

import inspect
import os
import sys

import nltk

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from dict import read_all_words, synonyms_for_word  # noqa: E402


def main():
    """
    Get all synonyms for every word in the dictionary,
    and then check whether the dictionary contains all the synonyms.
    If not, print those synonyms to stdout.
    """
    nltk.download("wordnet")

    from util import read_wordlist

    ignore_words = set(read_wordlist("data/missing.txt"))

    all_words = read_all_words()
    word_set = set(all_words)

    missing_synonyms = set()

    for word in all_words:
        synonyms = synonyms_for_word(word)
        for synonym in synonyms:
            if (
                " " not in synonym
                and synonym not in word_set
                and synonym not in ignore_words
            ):
                missing_synonyms.add(synonym)

    for missing in sorted(list(missing_synonyms)):
        print(missing)


if __name__ == "__main__":
    main()
