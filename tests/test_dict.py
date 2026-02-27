#!/usr/bin/env python3
"""
Tests for ensk.is dictionary source file parsing functions.
"""

import os
import sys

import pytest

# Add parent dir to path so we can import from there
basepath, _ = os.path.split(os.path.realpath(__file__))
src_path = os.path.join(basepath, "..")
sys.path.append(src_path)

from dict import (  # noqa: E402
    SYLLABLES_SEPARATOR,
    is_not_name,
    parse_line,
    startswith_category,
    syllables_for_word,
    unpack_definition,
)

# parse_line tests


def test_parse_line_simple_noun() -> None:
    """Test parsing a simple noun entry."""
    word, definition = parse_line("cat n. köttur")
    assert word == "cat"
    assert definition == "n. köttur"


def test_parse_line_simple_verb() -> None:
    """Test parsing a simple verb entry."""
    word, definition = parse_line("run s. hlaupa")
    assert word == "run"
    assert definition == "s. hlaupa"


def test_parse_line_simple_adjective() -> None:
    """Test parsing a simple adjective entry."""
    word, definition = parse_line("quick l. fljótur, skjótur")
    assert word == "quick"
    assert definition == "l. fljótur, skjótur"


def test_parse_line_multi_word_entry() -> None:
    """Test parsing a multi-word entry."""
    word, definition = parse_line("ice cream n. rjómís")
    assert word == "ice cream"
    assert definition == "n. rjómís"


def test_parse_line_complex_definition() -> None:
    """Test parsing an entry with a complex definition."""
    word, definition = parse_line(
        "flower n. blóm, blómstur; blómi; s. blómgast, blómstra"
    )
    assert word == "flower"
    assert definition == "n. blóm, blómstur; blómi; s. blómgast, blómstra"


def test_parse_line_no_category_raises() -> None:
    """Test that a line with no category raises an exception."""
    with pytest.raises(Exception, match="No cat found"):
        parse_line("notaword withoutcategory")


def test_parse_line_parenthetical_raises() -> None:
    """Test that a line with leftover phonetic data raises an exception."""
    with pytest.raises(Exception, match="Invalid entry"):
        parse_line("(junk) n. something")


def test_parse_line_bom_stripped() -> None:
    """Test that BOM characters are stripped from the word."""
    word, definition = parse_line("\ufeffcat n. köttur")
    assert word == "cat"


# unpack_definition tests


def test_unpack_definition_single_category() -> None:
    """Test unpacking a definition with a single category."""
    result = unpack_definition("n. köttur, kisa")
    assert "n." in result
    assert result["n."] == ["köttur, kisa"]


def test_unpack_definition_multiple_categories() -> None:
    """Test unpacking a definition with multiple categories separated by ;"""
    result = unpack_definition("n. blóm, blómstur; s. blómgast")
    assert "n." in result
    assert "s." in result
    assert result["n."] == ["blóm, blómstur"]
    assert result["s."] == ["blómgast"]


def test_unpack_definition_multiple_meanings_same_category() -> None:
    """Test unpacking a definition with multiple meanings in the same category."""
    result = unpack_definition("n. hundur; köttur; fugl")
    assert "n." in result
    assert len(result["n."]) == 3


# def test_unpack_definition_no_leading_category() -> None:
#     """Test unpacking a definition that doesn't start with a category."""
#     result = unpack_definition("some text without category")
#     assert None in result
#     assert result[None] == ["some text without category"]


# startswith_category tests


def test_startswith_category_match() -> None:
    """Test that a known category is detected."""
    result = startswith_category("n. something")
    assert result is not None
    cat, idx = result
    assert cat == "n."


def test_startswith_category_no_match() -> None:
    """Test that an unknown category returns None."""
    result = startswith_category("xyz. something")
    assert result is None


def test_startswith_category_with_leading_space() -> None:
    """Test that leading whitespace is handled."""
    result = startswith_category("  l. something")
    assert result is not None
    cat, _ = result
    assert cat == "l."


# is_not_name tests


def test_is_not_name_regular_word() -> None:
    """Test that regular words pass the filter."""
    assert is_not_name("happy") is True
    assert is_not_name("run fast") is True


def test_is_not_name_proper_name() -> None:
    """Test that proper names are filtered out."""
    assert is_not_name("George Washington") is False


def test_is_not_name_single_capitalized() -> None:
    """Test that single capitalized words pass the filter."""
    assert is_not_name("English") is True


# syllables_for_word tests


def test_syllables_for_word_empty() -> None:
    """Test that empty string returns empty string."""
    assert syllables_for_word("") == ""


def test_syllables_for_word_lookup_hit() -> None:
    """Test that a word in the syllables lookup returns the stored value."""
    result = syllables_for_word("cat")
    assert isinstance(result, str)
    assert len(result) > 0


def test_syllables_for_word_multi_word() -> None:
    """Test that a multi-word phrase assembles syllables from individual words."""
    # "ice cream" - both "ice" and "cream" should be in the lookup
    result = syllables_for_word("ice cream")
    assert isinstance(result, str)
    if result:
        assert SYLLABLES_SEPARATOR in result


def test_syllables_for_word_nltk_fallback() -> None:
    """Test that an unknown word falls back to NLTK syllable tokenizer."""
    result = syllables_for_word("supercalifragilistic")
    assert isinstance(result, str)
    assert len(result) > 0
    assert SYLLABLES_SEPARATOR in result


def test_syllables_for_word_known_multisyllable() -> None:
    """Test a known multi-syllable word from the lookup."""
    result = syllables_for_word("vindictive")
    assert isinstance(result, str)
    assert SYLLABLES_SEPARATOR in result
