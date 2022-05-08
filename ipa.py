#!/usr/bin/env

import requests
import bs4
import subprocess
import re

from db import EnskDatabase

CAM_URL = "https://dictionary.cambridge.org/dictionary/english/aberrancy"

entries = EnskDatabase().read_all_entries()

no_ipa = [e["word"] for e in entries if e["ipa_uk"] == ""]

print(f"Num w. no IPA: {len(no_ipa)}")

for e in no_ipa:
    if " " in e:
        continue

    try:
        out = subprocess.check_output(["ruby", "ipa-cambridge.rb", e])
        out = out.decode().strip()
    except Exception as e:
        continue

    if not out:
        continue
    comp = out.split("\n")
    c = comp[0]

    s = c.split(" ")
    if len(s) > 1:
        c = s[-1]

    print(e + ": " + str(c) + ",")

    # url = CAM_URL + e
    # print(url)
    # r = requests.get(url)
    # print(r.text)
