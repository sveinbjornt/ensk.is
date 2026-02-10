#!/usr/bin/env python3

# ruff: noqa E402

import time
import random
import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import httpx

from util import read_wordlist


def main() -> int:
    # Read all lines from data/missing.txt
    words = read_wordlist("data/missing.txt")
    
    random.shuffle(words)

    for w in words:
        word = w.strip()
        if "(" in word:
            continue
        url = f"https://idord.arnastofnun.is/d/api/es/agg/dictionaries/?ord={word}"
        response = httpx.get(url)

        r: dict = response.json()
        if not r.get("results") or len(r["results"]) == 0:
            continue

        print(url)

        # Sleep for 1 second to avoid overloading the server
        time.sleep(1)

    return 0


if __name__ == "__main__":
    exit(main())
