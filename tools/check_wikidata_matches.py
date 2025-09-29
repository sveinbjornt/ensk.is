#!/usr/bin/env python3
"""
This script reads the is-en-wiki-map-wikidata.csv file and checks for each
English-Icelandic word pair whether the Icelandic word is present in the
dictionary definition of the English word. If not, it prints the pair.
"""

import csv
import sys
import os

# Add the project root to the Python path to allow importing from other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dict import read_pages, parse_line
from util import is_ascii


def create_dictionary_map():
    """
    Reads the dictionary pages and creates a map from
    lowercase English words to their definitions.
    """
    dictionary_map = {}
    pages = read_pages()
    for line in pages:
        try:
            word, definition = parse_line(line)
            dictionary_map[word.lower()] = definition.lower()
        except Exception as e:
            # Ignore lines that can't be parsed
            # print(f"Skipping line: {line} - {e}")
            pass
    return dictionary_map


def main():
    """
    Main function to execute the script logic.
    """
    dictionary = create_dictionary_map()

    try:
        with open("is-en-wiki-map-wikidata.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row

            for row in reader:
                is_title, en_title = row
                if not is_ascii(en_title):
                    continue
                if " " in en_title:
                    continue
                if ":" in en_title:
                    continue

                en_title_lower = en_title.lower()
                is_title_lower = is_title.lower()

                if en_title_lower == is_title_lower:
                    continue

                if en_title_lower not in dictionary:
                    print(f"{en_title_lower} - {is_title_lower}")
                    # definition = dictionary[en_title_lower]
                    # if is_title_lower not in definition:
                    #     print(f"'{en_title}' ({is_title})")

    except FileNotFoundError:
        print("Error: is-en-wiki-map-wikidata.csv not found.")
        print("Please run tools/wiki_lang_map_wikidata.py first.")
        sys.exit(1)


if __name__ == "__main__":
    main()
