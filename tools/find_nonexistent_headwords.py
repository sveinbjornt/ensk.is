#!/usr/bin/env python3
"""
Find and print all single-word dictionary headwords that are present in
neither WordNet nor the English word list in data/wordlists/words.txt.

Multi-word headwords (those containing spaces) are skipped. The lookup is
case-insensitive but otherwise exact, i.e. no lemmatization is performed.

Useful for spotting misspelled headwords.
"""

# ruff: noqa E402

import argparse
import inspect
import os
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


from nltk.corpus import wordnet as wn

from dict import parse_line, read_raw_pages
from util import read_wordlist

EN_WORDLIST_PATH = "data/wordlists/words.txt"


def wordnet_lemmas() -> frozenset[str]:
    """Return the set of all single-word WordNet lemma names, lowercased.
    Multi-word lemmas (joined by underscores in WordNet) are omitted."""
    lemmas: set[str] = set()
    for synset in wn.all_synsets():
        for lemma in synset.lemmas():  # type: ignore
            name = lemma.name()
            if "_" not in name:
                lemmas.add(name.lower())
    return frozenset(lemmas)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find single-word dictionary headwords present in neither "
        f"WordNet nor {EN_WORDLIST_PATH}."
    )
    parser.add_argument(
        "--add-only",
        action="store_true",
        help="only check headwords in data/dict/_add.txt",
    )
    args = parser.parse_args()

    known = wordnet_lemmas().union(w.lower() for w in read_wordlist(EN_WORDLIST_PATH))

    total = 0
    skipped = 0
    missing = 0
    for letter, lines in read_raw_pages().items():
        if args.add_only and letter != "_add":
            continue
        for ln, line in enumerate(lines, start=1):
            try:
                (word, _) = parse_line(line)
            except Exception as e:
                print(f"{letter}:{ln}: unparseable ({e})", file=sys.stderr)
                continue
            if " " in word:
                skipped += 1
                continue
            total += 1
            if word.lower() not in known:
                missing += 1
                print(f"{letter}:{ln} | {word}")

    print(
        f"{missing} of {total} single-word headwords not found in WordNet "
        "or word list "
        f"({skipped} multi-word headwords skipped).",
        file=sys.stderr,
    )

    return 0


if __name__ == "__main__":
    exit(main())
