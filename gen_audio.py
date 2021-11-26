#!/usr/bin/env python3

import json
import os
import subprocess


data = None
with open("enis.json", "r") as f:
    data = json.load(f)
dictwords = data.keys()


for w in dictwords:
    args = ["/usr/bin/say"]
    args.append("-r")
    args.append("89")
    # args.append("--file-format=WAVE")
    args.append("-o")
    fn = f"{w}.aiff".replace(" ", "_")
    folder = "/Users/sveinbjorn/projects/ensk.is/static/audio/enis1932/"
    path = folder + fn
    args.append(path)
    args.append(w)
    print(args)
    subprocess.run(args)
