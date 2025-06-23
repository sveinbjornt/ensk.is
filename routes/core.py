"""
Core utilities and shared data for routes.
"""

from typing import Any
from functools import lru_cache

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
additions = [a["word"] for a in edb.read_all_additions()]
num_additions = len(additions)
nonascii = [e["word"] for e in entries if not is_ascii(e["word"])]
num_nonascii = len(nonascii)
multiword = [e["word"] for e in entries if " " in e["word"]]
num_multiword = len(multiword)
metadata = edb.read_metadata()

CATEGORIES = read_wordlist("data/catwords.txt")
KNOWN_MISSING_WORDS = read_wordlist("missing.txt")

SEARCH_CACHE_SIZE = 1000  # pages
SMALL_CACHE_SIZE = 100  # pages

# Get all entries in each category and store in dict
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


def err_resp(msg: str) -> JSONResponse:
    """Return JSON error message."""
    return JSONResponse(content={"error": True, "errmsg": msg})


def _format_item(item: dict[str, Any]) -> dict[str, Any]:
    """Format dictionary entry for HTML template use."""
    w = item["word"]
    x = item["definition"]

    # Replace ~ symbol with English word
    x = x.replace("~", w)

    # Replace %[word]% with link to intra-dictionary entry
    import re

    rx = re.compile(r"%\[(.+?)\]%")
    x = rx.sub(
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


def _results(q: str, exact_match: bool = False) -> tuple[list, bool]:
    """Return processed search results for a bareword textual query."""
    if not q:
        return [], False

    equal = []
    swith = []
    ewith = []
    other = []

    ql = q.lower()
    for k in entries:
        kl = k["word"].lower()
        if (exact_match and ql == kl) or (
            not exact_match and ql.lower() in k["word"].lower()
        ):
            item = _format_item(k)
            lw = item["word"].lower()
            lq = q.lower()
            if lw == lq:
                equal.append(item)
            elif lw.startswith(lq):
                swith.append(item)
            elif lw.endswith(lq):
                ewith.append(item)
            else:
                other.append(item)

    exact_match_found: bool = len(equal) > 0

    equal.sort(key=lambda d: d["word"].lower())
    swith.sort(key=lambda d: d["word"].lower())
    ewith.sort(key=lambda d: d["word"].lower())
    other.sort(key=lambda d: d["word"].lower())

    results = [*equal, *swith, *ewith, *other]

    # If no results found, try removing trailing 's' from query
    # and search again since it might be a plural form
    if len(results) == 0 and exact_match is False and len(q) >= 3 and q.endswith("s"):
        return _results(q[:-1], exact_match=True)

    return results, exact_match_found


@lru_cache(maxsize=SEARCH_CACHE_SIZE)
def cached_results(q: str, exact_match: bool = False):
    return _results(q, exact_match)
