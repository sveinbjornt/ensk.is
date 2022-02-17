#!/usr/bin/env python3

import json
import time
import random

import requests
import pprint

data = None
with open("enis.json", "r") as f:
    data = json.load(f)
dictwords = list(data.keys())

# pprint.pprint(dictwords)


TRANSLATE_URL = "https://velthyding.is/translate/"

random.shuffle(dictwords)


# {"model":"","contents":["guild"],"sourceLanguageCode":"en","targetLanguageCode":"is"}

for w in dictwords:
    d = {"model":"","contents":[w],"sourceLanguageCode":"en","targetLanguageCode":"is"}
    # data_json = json.dumps(d)
    # requests.post()
    r = requests.post(TRANSLATE_URL, json=d)
    print(r.content)
    time.sleep(1)
