#!/usr/bin/env python3
#
# Print all non-ASCII words in dictionary
#

from db import EnskDatabase
from util import is_ascii
from pprint import pprint

entries = EnskDatabase().read_all_additions()

not_ascii = [e["word"] for e in entries if not is_ascii(e["word"])]

pprint(not_ascii)
