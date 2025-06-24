#!/usr/bin/env python3
"""
Find phonetic IPA spelling for words in the dictionary that don't have any.
"""

# ruff: noqa E402

import subprocess

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from db import EnskDatabase
from util import is_ascii, read_wordlist


SKIP = read_wordlist("ipa_ignore.txt")

entries = EnskDatabase().read_all_additions()

no_ipa = [e["word"] for e in entries if e["ipa_uk"] == ""]
not_ascii = [e for e in no_ipa if not is_ascii(e)]
with_whitespace = [e for e in no_ipa if " " in e]
not_ignored = [
    e
    for e in no_ipa
    if e not in SKIP and e not in not_ascii and e not in with_whitespace
]

print(f"Num w. no IPA: {len(no_ipa)}")
print(f"Ignoring {len(not_ascii)} non-ASCII words")
print(f"Ignoring {len(SKIP)} whitelisted words")
print(f"Ignoring {len(with_whitespace)} words with whitespace")
print(f"Fetching IPA for {not_ignored}")

for e in no_ipa:
    if " " in e or e in SKIP or not is_ascii(e):
        continue

    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ipa-cambridge.rb"
    )

    try:
        out = subprocess.check_output(["ruby", script_path, e])
        out = out.decode().strip()
    except Exception:
        continue

    if not out:
        print(f"SKIP: {e}")
        continue
    comp = out.split("\n")
    c = comp[0]

    s = c.split(" ")
    if len(s) > 1:
        c = s[-1]

    print(f'"{e}": "{str(c)}",')
