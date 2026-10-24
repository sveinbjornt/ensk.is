#!/usr/bin/env python3
"""
Find and print all dictionary entries that share an identical definition,
i.e. everything following the headword, including the word category.

Useful for spotting copy-paste errors, redundant synonym pairs and
entries that might be better expressed as cross-references.
"""

# ruff: noqa E402

import argparse
import inspect
import os
import sys
from collections import defaultdict

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


from dict import parse_line, startswith_category

DICT_PATH = "data/dict"
TXT_SUFFIX = ".txt"
REF_MARKER = "sjá %["

# (word, definition, filename, line number)
Entry = tuple[str, str, str, int]


def read_entries() -> list[Entry]:
    """Read all dictionary source files and parse each line into its
    headword and definition, retaining file and line number."""
    entries: list[Entry] = []

    for fn in sorted(os.listdir(DICT_PATH)):
        if not fn.endswith(TXT_SUFFIX):
            continue
        path = os.path.join(DICT_PATH, fn)
        if not os.path.isfile(path):
            continue

        with open(path, "r") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.rstrip("\n")
                stripped = line.strip()
                # Skip empty lines and comments
                if not stripped or stripped.startswith("#"):
                    continue
                try:
                    word, definition = parse_line(line)
                except Exception as e:
                    print(f"{fn}:{lineno}: unparseable ({e})", file=sys.stderr)
                    continue
                entries.append((word, definition, fn, lineno))

    return entries


def strip_category(definition: str) -> str:
    """Return a definition with its leading word category removed."""
    cat = startswith_category(definition)
    if cat is None:
        return definition.strip()
    return definition[cat[1] :].strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find dictionary entries with identical definitions."
    )
    parser.add_argument(
        "--ignore-category",
        action="store_true",
        help="compare definitions without their leading word category",
    )
    parser.add_argument(
        "--skip-refs",
        action="store_true",
        help="ignore cross-reference entries (those containing 'sjá %%[...]%%')",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=2,
        metavar="N",
        help="only report definitions shared by at least N entries (default: 2)",
    )
    args = parser.parse_args()

    entries = read_entries()

    groups: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        definition = entry[1]
        if args.skip_refs and REF_MARKER in definition:
            continue
        key = strip_category(definition) if args.ignore_category else definition
        groups[key].append(entry)

    considered = sum(len(v) for v in groups.values())
    dupes = {k: v for k, v in groups.items() if len(v) >= args.min_count}

    # Largest groups first, then alphabetically by definition
    for key in sorted(dupes, key=lambda k: (-len(dupes[k]), k.lower())):
        members = sorted(dupes[key], key=lambda e: e[0].lower())
        print(f"{key}  [{len(members)}]")
        for word, _, fn, lineno in members:
            print(f"    {word}  ({fn}:{lineno})")
        print()

    affected = sum(len(v) for v in dupes.values())
    print(
        f"{len(dupes)} duplicated definitions covering {affected} entries "
        f"(of {considered} considered, {len(entries)} total).",
        file=sys.stderr,
    )

    return 0


if __name__ == "__main__":
    exit(main())
