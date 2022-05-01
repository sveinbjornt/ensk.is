#!/usr/bin/env python3






from country_list import countries_for_language
from pprint import pprint

countries = dict(countries_for_language("EN"))

for iso, name in countries.items():
    print(name)