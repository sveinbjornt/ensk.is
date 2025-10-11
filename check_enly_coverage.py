import json
import os
import sys

# Add the project root to the Python path to import dict.py
# This assumes the script is run from the project root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dict


def check_enly_coverage():
    enly_file_path = "enly.json"  # Assuming enly.json is in the repository root

    try:
        with open(enly_file_path, "r", encoding="utf-8") as f:
            enly_data = json.load(f)
    except FileNotFoundError:
        print(
            f"Error: {enly_file_path} not found. Please ensure it's in the repository root."
        )
        return
    except json.JSONDecodeError:
        print(
            f"Error: Could not decode JSON from {enly_file_path}. Please check file format."
        )
        return

    # Extract headwords from enly.json and convert to lowercase for comparison
    enly_headwords = set(key.lower() for key in enly_data.keys())

    # Get all headwords from the dictionary using dict.py and convert to lowercase
    dictionary_headwords = set(word.lower() for word in dict.read_all_words())

    missing_headwords = []
    for headword in enly_headwords:
        if headword not in dictionary_headwords:
            missing_headwords.append(headword)

    if missing_headwords:
        print("The following headwords from enly.json are NOT found in the dictionary:")
        for word in sorted(missing_headwords):
            print(f"{word} {enly_data.get(word)}")
    else:
        print("All headwords from enly.json are found in the dictionary.")


if __name__ == "__main__":
    check_enly_coverage()
