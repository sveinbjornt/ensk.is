#!/usr/bin/env python3

from db import EnskDatabase
from util import is_ascii
from pprint import pprint

entries = EnskDatabase().read_all_additions()

# no_ipa = [e["word"] for e in entries if e["ipa_uk"] == ""]
not_ascii = [e["word"] for e in entries if not is_ascii(e["word"])]

pprint(not_ascii)
