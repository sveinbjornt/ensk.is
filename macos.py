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

from typing import Any

import os
import sys
import shutil
import datetime
import subprocess
from xml.sax.saxutils import escape

from util import zip_file
from info import PROJECT


DICT_DEV_KIT_PATH = "macos/Dictionary Development Kit"
TEMPLATES_DIR = "macos"
BUILD_DIR = "static/files/ensk.is.macos_dict_build"
DICT_BUNDLE_ID = "is.ensk.dictionary"


def clean_build_directory() -> None:
    """Remove and recreate the build directory."""
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)


def read_template(filename: str) -> str:
    """Read a template file from the templates directory."""
    template_path = os.path.join(TEMPLATES_DIR, filename)
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def simple_template_replace(template: str, context: dict) -> str:
    """Simple template replacement for {{variable}} patterns."""
    result = template
    for key, value in context.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


def escape_xml(text: str) -> str:
    """Escape special XML characters in text."""
    return escape(text, {'"': "&quot;", "'": "&apos;"})


def generate_xml_entry(
    word: str, definition: str, ipa_uk: str, ipa_us: str, entry_id: str
) -> str:
    """Generate a single XML entry for the dictionary using template."""
    template = read_template("entry.xml")

    # Prepare context for template
    context: dict[str, Any] = {
        "entry_id": entry_id.replace(" ", "_").replace("-", "_"),
        "word": escape_xml(word),
        "definition": escape_xml(definition),
    }

    # Handle lowercase index
    if word and word[0].isupper():
        context["#lowercase_index"] = True
        context["lowercase_word"] = escape_xml(word.lower())
    else:
        template = template.replace(
            '{{#lowercase_index}}<d:index d:value="{{lowercase_word}}"/>{{/lowercase_index}}',
            "",
        )

    # Handle pronunciation
    if ipa_uk or ipa_us:
        context["#has_pronunciation"] = True
        if ipa_uk:
            context["#ipa_uk"] = True
            context["ipa_uk"] = escape_xml(ipa_uk)
        else:
            template = template.replace(
                '{{#ipa_uk}}<span d:pr="UK_IPA">{{ipa_uk}}</span>{{/ipa_uk}}', ""
            )

        if ipa_us:
            context["#ipa_us"] = True
            context["ipa_us"] = escape_xml(ipa_us)
        else:
            template = template.replace(
                '{{#ipa_us}}<span d:pr="US_IPA">{{ipa_us}}</span>{{/ipa_us}}', ""
            )
    else:
        # Remove entire pronunciation section
        start = template.find("{{#has_pronunciation}}")
        end = template.find("{{/has_pronunciation}}") + len("{{/has_pronunciation}}")
        if start != -1 and end != -1:
            template = template[:start] + template[end:]

    # Clean up any conditional markers
    template = template.replace("{{#lowercase_index}}", "").replace(
        "{{/lowercase_index}}", ""
    )
    template = template.replace("{{#has_pronunciation}}", "").replace(
        "{{/has_pronunciation}}", ""
    )
    template = template.replace("{{#ipa_uk}}", "").replace("{{/ipa_uk}}", "")
    template = template.replace("{{#ipa_us}}", "").replace("{{/ipa_us}}", "")

    return simple_template_replace(template, context)


def generate_front_matter(num_entries: int) -> str:
    """Generate front matter using template."""
    template = read_template("front_matter.xml")

    context = {
        "short_name": PROJECT.NAME,
        "dict_name": f"{PROJECT.NAME} English-Icelandic Dictionary",
        "description": PROJECT.DESCRIPTION_EN,
        "num_entries": f"{num_entries:,}",
        "editor": PROJECT.EDITOR,
        "website": PROJECT.BASE_URL,
        "repo_url": PROJECT.REPO_URL,
        "license": PROJECT.LICENSE,
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
    }

    return simple_template_replace(template, context)


def generate_dictionary_xml(entries) -> str:
    """Generate the complete dictionary XML file."""
    # XML header and namespace declarations
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">',
    ]

    # Add front matter
    xml_parts.append(generate_front_matter(len(entries)))

    # Add all dictionary entries
    for i, entry in enumerate(entries):
        word, definition, ipa_uk, ipa_us, _ = entry
        entry_id = f"entry_{i:06d}"
        xml_parts.append(generate_xml_entry(word, definition, ipa_uk, ipa_us, entry_id))

    # Close the dictionary element
    xml_parts.append("</d:dictionary>")

    return "\n".join(xml_parts)


def generate_info_plist() -> str:
    """Generate the Info.plist file from template."""
    template = read_template("Info.plist.template")

    context = {
        "bundle_id": DICT_BUNDLE_ID,
        "short_name": PROJECT.NAME,
        "version": PROJECT.VERSION,
        "year": datetime.datetime.now().year,
        "editor": PROJECT.EDITOR,
        "license": PROJECT.LICENSE,
    }

    return simple_template_replace(template, context)


def generate_makefile() -> str:
    """Generate the Makefile from template."""
    template = read_template("Makefile.template")

    context = {
        "dict_name": f"{PROJECT.NAME} English-Icelandic Dictionary",
        "short_name": PROJECT.NAME,
        "dict_dev_kit_path": os.path.abspath(DICT_DEV_KIT_PATH),
    }

    return simple_template_replace(template, context)


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


def generate_macos_dictionary(entries, keep_build_files: bool = False) -> str:
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

    # Copy CSS file
    print("Copying CSS...")
    shutil.copy(os.path.join(TEMPLATES_DIR, "Dictionary.css"), BUILD_DIR)

    print("Generating Makefile...")
    makefile_content = generate_makefile()
    with open(os.path.join(BUILD_DIR, "Makefile"), "w", encoding="utf-8") as f:
        f.write(makefile_content)

    # Build the dictionary
    if not build_dictionary():
        raise Exception("Failed to build dictionary")

    # Copy the built dictionary to static files
    dict_bundle_path = os.path.join(BUILD_DIR, "objects", f"{PROJECT.NAME}.dictionary")
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
    # Import here to avoid circular imports when used as a module
    from gen import read_all_entries

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
