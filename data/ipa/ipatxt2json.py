#!/usr/bin/env python3

import sys
import csv
import json

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 conv.py <filename>")
        sys.exit(1)

    d = dict()
    with open(sys.argv[1]) as file:
        tsv_file = csv.reader(file, delimiter="\t")
        for e in tsv_file:
            d[e[0]] = e[1]
        print(json.dumps(d))
