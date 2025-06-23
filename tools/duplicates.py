#!/usr/bin/env python3
"""
Find and print out all duplicate word-key entries in the dictionary
for comparison and evaluation purposes.
"""

# ruff: noqa E402

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


from db import EnskDatabase


def main() -> int:
    db = EnskDatabase()

    entries = [e["word"] for e in db.read_all_duplicates()]
    additions = [e["word"] for e in db.read_all_additions()]

    for w in entries:
        if w.lower() in additions or w in additions:
            print(f"IN ADDITIONS: {w}")
        else:
            print(f"{w}")

    return 0


if __name__ == "__main__":
    exit(main())
