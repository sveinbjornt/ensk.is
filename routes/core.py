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
    has_more = False
    exact_match_found = False

    # For unlimited results, collect everything
    if limit <= 0:
        for k in entries:
            kl = k["word"].lower()
            if (exact_match and ql == kl) or (not exact_match and ql in kl):
                if kl == ql:
                    equal.append(k)
                    exact_match_found = True
                elif kl.startswith(ql):
                    swith.append(k)
                elif kl.endswith(ql):
                    ewith.append(k)
                else:
                    other.append(k)
    else:
        # Optimized single-pass collection with early termination
        max_exact = 2  # Dictionary constraint: max 2 exact matches
        collected_exact = 0
        base_buffer = 15  # Buffer to ensure proper sorting within categories

        # Track if we need to continue looking for exact matches
        need_exact = True

        for k in entries:
            kl = k["word"].lower()

            # For exact_match mode, only check exact equality
            if exact_match:
                if ql == kl:
                    equal.append(k)
                    exact_match_found = True
                    collected_exact += 1
                    if collected_exact >= max_exact:
                        break
            else:
                # For substring matching
                if ql in kl:
                    if kl == ql and collected_exact < max_exact:
                        equal.append(k)
                        exact_match_found = True
                        collected_exact += 1
                        if collected_exact >= max_exact:
                            need_exact = False
                    elif kl.startswith(ql):
                        swith.append(k)
                    elif kl.endswith(ql):
                        ewith.append(k)
                    else:
                        other.append(k)

                    # Don't check for early termination until we've found all exact matches
                    # or we've gone through enough entries that exact matches are unlikely
                    if (
                        not need_exact
                        or len(equal) + len(swith) + len(ewith) + len(other) > 100
                    ):
                        # Calculate total collected so far
                        total = len(equal) + len(swith) + len(ewith) + len(other)

                        # Determine if we can stop based on priority order
                        if len(equal) >= limit:
                            # We have enough exact matches
                            has_more = True
                            break

                        # Calculate remaining slots after exact matches
                        remaining = limit - len(equal)

                        if len(swith) >= remaining + base_buffer:
                            # We have enough startswith matches (with buffer)
                            has_more = len(ewith) > 0 or len(other) > 0
                            break
                        elif len(swith) + len(ewith) >= remaining + base_buffer:
                            # We have enough startswith + endswith matches
                            has_more = len(other) > 0
                            # Continue a bit more to ensure proper sorting
                            if len(swith) + len(ewith) >= remaining + base_buffer * 2:
                                break
                        elif total >= limit + base_buffer * 2:
                            # We have enough total results with extra buffer
                            has_more = True
                            break

    # Sort raw entries (cheaper than sorting formatted items)
    equal.sort(key=lambda d: d["word"].lower())
    swith.sort(key=lambda d: d["word"].lower())
    ewith.sort(key=lambda d: d["word"].lower())
    other.sort(key=lambda d: d["word"].lower())

    # Combine results in priority order
    results = []

    # Always include all exact matches (max 2)
    for e in equal:
        results.append(_format_item(e))

    if limit > 0:
        # Fill remaining slots in priority order
        remaining = limit - len(results)

        # Add startswith matches
        for e in swith[:remaining]:
            results.append(_format_item(e))

        # Add endswith matches
        remaining = limit - len(results)
        for e in ewith[:remaining]:
            results.append(_format_item(e))

        # Add other (contains) matches
        remaining = limit - len(results)
        for e in other[:remaining]:
            results.append(_format_item(e))

        # Final check for has_more flag
        if not has_more:
            total_available = len(equal) + len(swith) + len(ewith) + len(other)
            has_more = total_available > limit
    else:
        # No limit - format all results
        for e in swith:
            results.append(_format_item(e))
        for e in ewith:
            results.append(_format_item(e))
        for e in other:
            results.append(_format_item(e))

    # If no results found, try removing trailing 's' from query
    # and search again since it might be a plural form
    if len(results) == 0 and not exact_match and len(q) >= 3 and q.endswith("s"):
        return _results(q[:-1], exact_match=True, limit=limit)

    return results[:limit] if limit > 0 else results, exact_match_found, has_more


@lru_cache(maxsize=SEARCH_CACHE_SIZE)
def cached_results(
    q: str, exact_match: bool = False, limit: int = DEFAULT_SEARCH_LIMIT
) -> tuple[list, bool, bool]:
    return _results(q, exact_match, limit)
