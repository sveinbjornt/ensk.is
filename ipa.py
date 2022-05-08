#!/usr/bin/env

import requests
import bs4

from db import EnskDatabase

CAM_URL = "https://dictionary.cambridge.org/dictionary/english/"

entries = EnskDatabase().read_all_entries()

no_ipa = [e["word"] for e in entries if e["ipa"] == ""]

for e in no_ipa:
    url = CAM_URL + e
    print(url)
    r = requests.get(url)
    print(r.text)
