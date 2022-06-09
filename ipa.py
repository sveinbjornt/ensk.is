#!/usr/bin/env

import subprocess

from db import EnskDatabase

entries = EnskDatabase().read_all_additions()

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
