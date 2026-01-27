#!/usr/bin/env python3
"""
Test ensk.is source dictionary file parsing
"""

import os
import pytest
import sys

# Add parent dir to path so we can import from there
basepath, _ = os.path.split(os.path.realpath(__file__))
src_path = os.path.join(basepath, "..")
sys.path.append(src_path)

from dict import parse_line  # noqa: E402


def test_parse_line_simple():
    line = "apple | n. epli"
    word, definition = parse_line(line)
    assert word == "apple"
    assert definition == "n. epli"


def test_parse_line_with_multiple_pipes():
    # Only the first pipe should be the separator
    line = "bitwise or | n. virkinn | (í forritun)"
    word, definition = parse_line(line)
    assert word == "bitwise or"
    assert definition == "n. virkinn | (í forritun)"


def test_parse_line_with_spaces():
    line = "  spaced out word  |   adj. utan við sig   "
    word, definition = parse_line(line)
    assert word == "spaced out word"
    assert definition == "adj. utan við sig"


def test_parse_line_missing_pipe():
    line = "invalid line n. no separator"
    with pytest.raises(Exception) as excinfo:
        parse_line(line)
    assert "Invalid format" in str(excinfo.value)


def test_parse_line_empty_definition():
    line = "word | "
    word, definition = parse_line(line)
    assert word == "word"
    assert definition == ""


def test_parse_line_unicode():
    line = "þjóð | n. nation"
    word, definition = parse_line(line)
    assert word == "þjóð"
    assert definition == "n. nation"
