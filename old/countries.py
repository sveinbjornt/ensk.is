#!/usr/bin/env python3


from country_list import countries_for_language
from pprint import pprint
from db import EnskDatabase

countries_en = dict(countries_for_language("EN"))
countries_is = dict(countries_for_language("IS"))

e = EnskDatabase()

# Read all dictionary entries into memory
res = e.read_all_entries()
entries = [x["word"] for x in res]

# print(entries)

for iso, name in countries_en.items():
    if name not in entries:
        print(f"{name} n. {countries_is.get(iso)}")
