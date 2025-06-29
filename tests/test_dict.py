#!/usr/bin/env python3
"""
Tests for ensk.is dictionary parsing functions.
"""

import os
import sys
import pytest

# Add parent dir to path so we can import from there
basepath, _ = os.path.split(os.path.realpath(__file__))
src_path = os.path.join(basepath, "..")
sys.path.append(src_path)

from dict import parse_line, unpack_definition, startswith_category

# Mock the CATEGORIES constant so we don't have to read the file
import dict as dict_module
dict_module.CATEGORIES = ["lo.", "so.", "fs.", "uh."]


def test_parse_line():
    """Test the parse_line function."""
    line1 = "word lo. definition"
    word1, def1 = parse_line(line1)
    assert word1 == "word"
    assert def1 == "lo. definition"

    line2 = "multi word so. another definition"
    word2, def2 = parse_line(line2)
    assert word2 == "multi word"
    assert def2 == "so. another definition"

    line3 = "  extra   space  fs.  and definition  "
    word3, def3 = parse_line(line3)
    assert word3 == "extra space"
    assert def3 == "fs. and definition"

    with pytest.raises(Exception):
        parse_line("no category here")


def test_startswith_category():
    """Test the startswith_category function."""
    assert startswith_category("lo. definition") == ("lo.", 3)
    assert startswith_category("  so. definition") == ("so.", 5)
    assert startswith_category("fs. definition") == ("fs.", 3)
    assert startswith_category("uh. definition") == ("uh.", 3)
    assert startswith_category("no category") is None


def test_unpack_definition():
    """Test the unpack_definition function."""
    def1 = "lo. def1; def2"
    unpacked1 = unpack_definition(def1)
    assert unpacked1 == {"lo.": ["def1", "def2"]}

    def2 = "so. def1; lo. def2; def3"
    unpacked2 = unpack_definition(def2)
    assert unpacked2 == {"so.": ["def1"], "lo.": ["def2", "def3"]}

    def3 = "fs. def1"
    unpacked3 = unpack_definition(def3)
    assert unpacked3 == {"fs.": ["def1"]}

