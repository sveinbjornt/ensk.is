#!/usr/bin/env python3

import json
import os
import subprocess


data = None
with open("enis.json", "r") as f:
    data = json.load(f)
dictwords = data.keys()


_SPEECHSYNTH_CLT = "/usr/bin/say"


def synthesize_word(w: str, dest_folder=None) -> str:
    """Generate a speech-synthesised AIFF audio file from word.
    Returns path to output file."""
    args = [_SPEECHSYNTH_CLT]
    args.append("-r")
    args.append("89")
    # args.append("--file-format=WAVE")
    args.append("-o")
    fn = f"{w}.aiff".replace(" ", "_")
    outpath = f"{dest_folder}/{fn}"
    args.append(outpath)
    args.append(w)
    print(args)
    subprocess.run(args)
    return outpath


_LAME_CLT = "/usr/local/bin/lame"


def aiff2mp3(infile_path: str, outfile_path: str = None) -> str:
    """Convert AIFF to MP3 using lame. Returns output file path."""
    args = [_LAME_CLT]
    args.append(infile_path)
    print(args)
    subprocess.run(args)


_OUT_FOLDER = "/Users/sveinbjorn/projects/ensk.is/static/audio/enis1932/"

for w in dictwords:
    aiff_path = synthesize_word(w, dest_folder=_OUT_FOLDER)
    mp3_path = aiff2mp3(aiff_path)
