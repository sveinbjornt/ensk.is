#!/usr/bin/env python3
"""

Ensk.is - Free and open English-Icelandic dictionary

Copyright (c) 2021-2025, Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or other
materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may
be used to endorse or promote products derived from this software without specific
prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.


Generate macOS dictionary from raw dictionary text files.


"""

import os
import sys
import shutil
import datetime
import subprocess
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from pathlib import Path

from util import zip_file, silently_remove, read_json
from info import PROJECT
from dict import read_pages, parse_line, page_for_word

# Type alias matching gen.py
EntryType = tuple[str, str, str, str, int]
EntryList = list[EntryType]

# Load IPA data
ENWORD_TO_IPA_UK = read_json("data/ipa/uk/en2ipa.json")
ENWORD_TO_IPA_US = read_json("data/ipa/us/en2ipa.json")

DICT_DEV_KIT_PATH = "Dictionary Development Kit"
BUILD_DIR = "static/files/ensk.is.macos_dict_build"
DICT_BUNDLE_ID = "is.ensk.dictionary"
DICT_NAME = "Ensk.is English-Icelandic Dictionary"
DICT_SHORT_NAME = "Ensk.is"


def ipa4entry(s: str, lang: str = "uk") -> str | None:
    """Look up International Phonetic Alphabet spelling for word."""
    assert lang in ["uk", "us"]
    if lang == "uk":
        word2ipa = ENWORD_TO_IPA_UK
    else:
        word2ipa = ENWORD_TO_IPA_US
    ipa = word2ipa.get(s)
    if not ipa and " " in s:
        # It's a multi-word entry
        wipa = s.split()
        ipa4words = []
        # Look up each individual word and assemble
        for wp in wipa:
            lookup = word2ipa.get(wp)
            if not lookup:
                lookup = word2ipa.get(wp.lower())
            if not lookup:
                lookup = word2ipa.get(wp.capitalize())
            if not lookup:
                break
            else:
                lookup = lookup.lstrip("/").rstrip("/")
                ipa4words.append(lookup)
        if len(ipa4words) == len(wipa):
            ipa = " ".join(ipa4words)
            ipa = f"/{ipa}/"
    return ipa


def read_all_entries() -> EntryList:
    """Read all entries from dictionary text files and parse them."""
    r = read_pages()

    entries = []
    for line in r:
        wd = parse_line(line)
        w = wd[0]
        definition = wd[1]
        ipa_uk = ipa4entry(w, lang="uk") or ""
        ipa_us = ipa4entry(w, lang="us") or ""
        pn = page_for_word(w)
        entries.append(tuple([w, definition, ipa_uk, ipa_us, pn]))

    entries.sort(key=lambda d: d[0].lower())  # Sort alphabetically by word

    return entries


def clean_build_directory() -> None:
    """Remove and recreate the build directory."""
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)


def escape_xml(text: str) -> str:
    """Escape special XML characters in text."""
    return escape(text, {'"': "&quot;", "'": "&apos;"})


def generate_xml_entry(
    word: str, definition: str, ipa_uk: str, ipa_us: str, entry_id: str
) -> str:
    """Generate a single XML entry for the dictionary."""
    # Create a unique ID for the entry
    safe_id = entry_id.replace(" ", "_").replace("-", "_")

    # Build the XML entry
    entry_parts = [f'<d:entry id="{safe_id}" d:title="{escape_xml(word)}">']

    # Add index values
    entry_parts.append(f'    <d:index d:value="{escape_xml(word)}"/>')

    # Add lowercase variant if word starts with capital
    if word and word[0].isupper():
        entry_parts.append(f'    <d:index d:value="{escape_xml(word.lower())}"/>')

    # Add the main heading
    entry_parts.append(f"    <h1>{escape_xml(word)}</h1>")

    # Add pronunciation if available
    if ipa_uk or ipa_us:
        entry_parts.append('    <span class="syntax">')
        if ipa_uk:
            entry_parts.append(
                f'        <span d:pr="UK_IPA">{escape_xml(ipa_uk)}</span>'
            )
        if ipa_us:
            entry_parts.append(
                f'        <span d:pr="US_IPA">{escape_xml(ipa_us)}</span>'
            )
        entry_parts.append("    </span>")

    # Add the definition
    entry_parts.append(f"    <p>{escape_xml(definition)}</p>")

    entry_parts.append("</d:entry>")

    return "\n".join(entry_parts)


def generate_dictionary_xml(entries: EntryList) -> str:
    """Generate the complete dictionary XML file."""

    # XML header and namespace declarations
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">',
    ]

    # Add front matter entry
    xml_parts.append(f'''<d:entry id="front_matter" d:title="About {DICT_SHORT_NAME}">
    <h1><b>{DICT_NAME}</b></h1>
    <h2>About This Dictionary</h2>
    <div>
        <p>{PROJECT.DESCRIPTION_EN}</p>
        <p>This dictionary contains {len(entries):,} entries.</p>
        <br/>
        <p><b>Editor:</b> {PROJECT.EDITOR}</p>
        <p><b>Website:</b> <a href="{PROJECT.BASE_URL}">{PROJECT.BASE_URL}</a></p>
        <p><b>Source:</b> <a href="{PROJECT.REPO_URL}">{PROJECT.REPO_URL}</a></p>
        <p><b>License:</b> {PROJECT.LICENSE}</p>
        <p><b>Generated:</b> {datetime.datetime.now().strftime("%Y-%m-%d")}</p>
    </div>
</d:entry>''')

    # Add all dictionary entries
    for i, entry in enumerate(entries):
        word, definition, ipa_uk, ipa_us, _ = entry
        entry_id = f"entry_{i:06d}"
        xml_parts.append(generate_xml_entry(word, definition, ipa_uk, ipa_us, entry_id))

    # Close the dictionary element
    xml_parts.append("</d:dictionary>")

    return "\n".join(xml_parts)


def generate_info_plist() -> str:
    """Generate the Info.plist file for the dictionary."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleIdentifier</key>
    <string>{DICT_BUNDLE_ID}</string>
    <key>CFBundleName</key>
    <string>{DICT_SHORT_NAME}</string>
    <key>CFBundleShortVersionString</key>
    <string>{PROJECT.VERSION}</string>
    <key>DCSDictionaryCopyright</key>
    <string>Copyright © {datetime.datetime.now().year} {PROJECT.EDITOR}. {PROJECT.LICENSE}.</string>
    <key>DCSDictionaryManufacturerName</key>
    <string>{PROJECT.EDITOR}</string>
    <key>DCSDictionaryFrontMatterReferenceID</key>
    <string>front_matter</string>
    <key>DCSDictionaryUseSystemAppearance</key>
    <true/>
</dict>
</plist>"""


def generate_css() -> str:
    """Generate the CSS file for the dictionary."""
    return """@charset "UTF-8";
@namespace d url(http://www.apple.com/DTDs/DictionaryService-1.0.rng);

d|entry {
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif;
}

h1 {
    font-size: 150%;
    font-weight: bold;
    margin-bottom: 0.5em;
}

h2 {
    font-size: 125%;
    font-weight: bold;
    margin-top: 1em;
    margin-bottom: 0.5em;
}

.syntax {
    display: block;
    font-size: 90%;
    margin: 0.5em 0;
    color: #666;
}

span[d|pr="UK_IPA"]:before {
    content: "UK: ";
    font-weight: bold;
}

span[d|pr="US_IPA"]:before {
    content: "US: ";
    font-weight: bold;
}

span[d|pr="UK_IPA"], span[d|pr="US_IPA"] {
    margin-right: 1em;
}

p {
    margin: 0.5em 0;
}

a {
    color: #007AFF;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}
"""


def generate_makefile() -> str:
    """Generate the Makefile for building the dictionary."""
    dict_dev_kit_abs = os.path.abspath(DICT_DEV_KIT_PATH)
    return f'''#
# Makefile for {DICT_NAME}
#

DICT_NAME = "{DICT_SHORT_NAME}"
DICT_SRC_PATH = Dictionary.xml
CSS_PATH = Dictionary.css
PLIST_PATH = Info.plist

DICT_BUILD_OPTS =

DICT_BUILD_TOOL_DIR = "{dict_dev_kit_abs}"
DICT_BUILD_TOOL_BIN = "$(DICT_BUILD_TOOL_DIR)/bin"

DICT_DEV_KIT_OBJ_DIR = ./objects
export DICT_DEV_KIT_OBJ_DIR

DESTINATION_FOLDER = ~/Library/Dictionaries
RM = /bin/rm

all:
	"$(DICT_BUILD_TOOL_BIN)/build_dict.sh" $(DICT_BUILD_OPTS) $(DICT_NAME) $(DICT_SRC_PATH) $(CSS_PATH) $(PLIST_PATH)
	echo "Done."

install:
	echo "Installing into $(DESTINATION_FOLDER)".
	mkdir -p $(DESTINATION_FOLDER)
	ditto --noextattr --norsrc $(DICT_DEV_KIT_OBJ_DIR)/$(DICT_NAME).dictionary $(DESTINATION_FOLDER)/$(DICT_NAME).dictionary
	touch $(DESTINATION_FOLDER)
	echo "Done."
	echo "To test the new dictionary, try Dictionary.app."

clean:
	$(RM) -rf $(DICT_DEV_KIT_OBJ_DIR)
'''


def build_dictionary() -> bool:
    """Build the dictionary using the Dictionary Development Kit."""
    old_cwd = os.getcwd()
    os.chdir(BUILD_DIR)

    try:
        # Run make
        print("Building dictionary with make...")
        process = subprocess.Popen(
            ["make"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Print output as it comes
        for line in process.stdout:  # type: ignore
            print(line, end="")

        process.wait()

        if process.returncode != 0:
            print(f"make command failed with return code {process.returncode}")
            return False

        return True

    finally:
        os.chdir(old_cwd)


def generate_macos_dictionary(
    entries: EntryList, keep_build_files: bool = False
) -> str:
    """Generate macOS dictionary file. Return file path to the zip file."""

    print(f"Generating macOS dictionary with {len(entries)} entries...")

    # Clean and create build directory
    clean_build_directory()

    # Generate all required files
    print("Generating dictionary XML...")
    xml_content = generate_dictionary_xml(entries)
    with open(os.path.join(BUILD_DIR, "Dictionary.xml"), "w", encoding="utf-8") as f:
        f.write(xml_content)

    print("Generating Info.plist...")
    plist_content = generate_info_plist()
    with open(os.path.join(BUILD_DIR, "Info.plist"), "w", encoding="utf-8") as f:
        f.write(plist_content)

    print("Generating CSS...")
    css_content = generate_css()
    with open(os.path.join(BUILD_DIR, "Dictionary.css"), "w", encoding="utf-8") as f:
        f.write(css_content)

    print("Generating Makefile...")
    makefile_content = generate_makefile()
    with open(os.path.join(BUILD_DIR, "Makefile"), "w", encoding="utf-8") as f:
        f.write(makefile_content)

    # Build the dictionary
    if not build_dictionary():
        raise Exception("Failed to build dictionary")

    # Copy the built dictionary to static files
    dict_bundle_path = os.path.join(
        BUILD_DIR, "objects", f"{DICT_SHORT_NAME}.dictionary"
    )
    target_path = f"{PROJECT.STATIC_FILES_PATH}{PROJECT.BASE_DATA_FILENAME}.dictionary"

    if os.path.exists(target_path):
        shutil.rmtree(target_path)

    shutil.copytree(dict_bundle_path, target_path)

    # Zip the dictionary bundle
    print("Creating zip archive...")
    old_cwd = os.getcwd()
    os.chdir(PROJECT.STATIC_FILES_PATH)

    zip_filename = f"{PROJECT.BASE_DATA_FILENAME}.dictionary.zip"
    zip_file(f"{PROJECT.BASE_DATA_FILENAME}.dictionary", zip_filename)

    os.chdir(old_cwd)

    # Clean up
    if not keep_build_files:
        shutil.rmtree(BUILD_DIR)
        shutil.rmtree(target_path)

    return f"{PROJECT.STATIC_FILES_PATH}{zip_filename}"


def main() -> None:
    """Main function for testing the macOS dictionary generation."""
    print("Reading dictionary entries...")
    entries = read_all_entries()
    print(f"Found {len(entries)} entries")

    try:
        zip_path = generate_macos_dictionary(entries)
        print(f"Successfully generated macOS dictionary: {zip_path}")
    except Exception as e:
        print(f"Error generating dictionary: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
