"""
Ensk.is
Core utilities and shared data for routes
"""

from typing import Any
from functools import lru_cache
import re

from fastapi.responses import JSONResponse as FastAPIJSONResponse
from fastapi.templating import Jinja2Templates
import orjson

from db import EnskDatabase
from dict import read_wordlist
from info import PROJECT
from util import is_ascii


# Custom JSON response class that uses ultrafast orjson for serialization
class CustomJSONResponse(FastAPIJSONResponse):
    """JSON response using the high-performance orjson library for serialization."""

    def render(self, content: Any) -> bytes:
        return orjson.dumps(content)


JSONResponse = CustomJSONResponse

# Set up templates
templates = Jinja2Templates(directory="templates")
TemplateResponse = templates.TemplateResponse

# Initialize database singleton
edb = EnskDatabase(read_only=True)

# Read everything we want from the database into memory
entries = edb.read_all_entries()
num_entries = len(entries)

all_words = [e["word"] for e in entries]

original_entries = [e["word"] for e in edb.read_all_original()]
num_original_entries = len(original_entries)

additional_entries = [a["word"] for a in edb.read_all_additions()]
num_additional_entries = len(additional_entries)

nonascii_entries = [e["word"] for e in entries if not is_ascii(e["word"])]
num_nonascii_entries = len(nonascii_entries)

multiword_entries = [e["word"] for e in edb.read_all_with_multiple_words()]
num_multiword_entries = len(multiword_entries)

capitalized_entries = [e["word"] for e in edb.read_all_capitalized()]
num_capitalized_entries = len(capitalized_entries)

duplicate_entries = [e["word"] for e in edb.read_all_duplicates()]
num_duplicate_entries = len(duplicate_entries)

no_uk_ipa_entries = [e["word"] for e in edb.read_all_without_ipa(lang="uk")]
num_no_uk_ipa_entries = len(no_uk_ipa_entries)

no_us_ipa_entries = [e["word"] for e in edb.read_all_without_ipa(lang="us")]
num_no_us_ipa_entries = len(no_us_ipa_entries)

no_page_entries = [e["word"] for e in edb.read_all_with_no_page()]
num_no_page_entries = len(no_page_entries)

metadata = edb.read_metadata()

# Get all entries in each category and store in dict
CATEGORIES = read_wordlist("data/catwords.txt")
CAT2ENTRIES = {}
for c in CATEGORIES:
    cs = c.rstrip(".")
    CAT2ENTRIES[cs] = edb.read_all_in_wordcat(cs)

# To JSON configuration file?
CAT_TO_NAME = {
    "n.": "nafnorð",
    "nft.": "nafnorð (í fleirtölu)",
    "l.": "lýsingarorð",
    "s.": "sagnorð",
    "ao.": "atviksorð",
    "fsk.": "forskeyti",
    "st.": "samtenging",
    "gr.": "greinir",
    "fs.": "forsetning",
    "uh.": "upphrópun",
    "fn.": "fornafn",
    "stytt.": "stytting",
    "sks.": "skammstöfun",
}

SEARCH_CACHE_SIZE = 1000  # pages
SMALL_CACHE_SIZE = 100  # pages

KNOWN_MISSING_WORDS = read_wordlist("missing.txt")

DEFAULT_SEARCH_LIMIT = 50  # Default limit for search results


# Clear the database reference to free memory
# It will not be needed after this point
edb = None


def err_resp(msg: str) -> JSONResponse:
    """Return JSON error message."""
    return JSONResponse(content={"error": True, "errmsg": msg})


LINK_FORMAT_REGEX = re.compile(r"%\[(.+?)\]%")


def _format_item(item: dict[str, Any]) -> dict[str, Any]:
    """Format dictionary entry for HTML template use."""
    w = item["word"]
    x = item["definition"]

    # Replace ~ symbol with English word
    x = x.replace("~", w)

    # Replace %[word]% with link to intra-dictionary entry
    x = LINK_FORMAT_REGEX.sub(
        rf"<strong><em><a href='{PROJECT.BASE_URL}/item/\1'>\1</a></em></strong>", x
    )

    # Italicize English words
    x = x.replace("[", "<em>")
    x = x.replace("]", "</em>")

    # Phonetic spelling
    ipa_uk = item.get("ipa_uk", "")
    ipa_us = item.get("ipa_us", "")

    # Generate URLs to audio files
    audiofn = w.replace(" ", "_")
    audio_url_uk = f"{PROJECT.BASE_URL}/static/audio/dict/uk/{audiofn}.mp3"
    audio_url_us = f"{PROJECT.BASE_URL}/static/audio/dict/us/{audiofn}.mp3"

    # Original dictionary page
    p = item["page_num"]
    p_url = f"{PROJECT.BASE_URL}/page/{p}" if p > 0 else ""

    # Create item dict
    item = {
        "word": w,
        "def": x,
        "syllables": item.get("syllables", ""),
        "ipa_uk": ipa_uk,
        "ipa_us": ipa_us,
        "audio_uk": audio_url_uk,
        "audio_us": audio_url_us,
        "page_num": p,
        "page_url": p_url,
    }
    return item


def _results(
    q: str, exact_match: bool = False, limit: int = DEFAULT_SEARCH_LIMIT
) -> tuple[list, bool, bool]:
    """Return processed search results for a bareword text query."""
    if not q:
        return ([], False, False)

    equal = []
    swith = []
    ewith = []
    other = []

    ql = q.lower()
    exact_match_found = False

    # Collect all matching entries
    for k in entries:
        kl = k["word"].lower()

        if exact_match:
            # In exact match mode, only collect exact matches
            if ql == kl:
                equal.append(k)
                exact_match_found = True
        else:
            # In substring mode, categorize by match type
            if ql in kl:
                if kl == ql:
                    equal.append(k)
                    exact_match_found = True
                elif kl.startswith(ql):
                    swith.append(k)
                elif kl.endswith(ql):
                    ewith.append(k)
                else:
                    other.append(k)

    # Sort each category
    equal.sort(key=lambda d: d["word"].lower())
    swith.sort(key=lambda d: d["word"].lower())
    ewith.sort(key=lambda d: d["word"].lower())
    other.sort(key=lambda d: d["word"].lower())

    # Assemble results in priority order: exact, startswith, endswith, contains
    all_results = equal + swith + ewith + other

    # Apply limit if specified
    if limit > 0:
        limited_results = all_results[:limit]
        has_more = len(all_results) > limit
    else:
        limited_results = all_results
        has_more = False

    # If no results found, try removing trailing 's' from query
    # and search again since it might be a plural form
    if (
        not exact_match
        and len(limited_results) == 0
        and len(q) >= 3
        and q.endswith("s")
    ):
        return _results(q[:-1], exact_match=True, limit=limit)

    # Format final results
    formatted_results = [_format_item(item) for item in limited_results]

    return formatted_results, exact_match_found, has_more


@lru_cache(maxsize=SEARCH_CACHE_SIZE)
def cached_results(
    q: str, exact_match: bool = False, limit: int = DEFAULT_SEARCH_LIMIT
) -> tuple[list, bool, bool]:
    return _results(q, exact_match, limit)
