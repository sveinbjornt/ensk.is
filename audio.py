#!/usr/bin/env python3
"""
    Functionality related to generating audio files for dictionary words.
"""

from typing import Optional, List

import os
import subprocess
from os.path import exists

from dict import read_all_words


_SPEECHSYNTH_CLT = "/usr/bin/say"  # Requires macOS


def synthesize_word(w: str, dest_folder=None, voice="Daniel") -> Optional[str]:
    """Generate a speech-synthesised AIFF audio file from word.
    Returns path to output file. Only works on macOS."""
    assert dest_folder is not None
    assert voice in ["Daniel", "Alex"]  # Daniel for UK English, Alex for US English

    subfolder = "uk" if voice == "Daniel" else "us"

    f = w.replace(" ", "_")

    if exists(f"{dest_folder}/{subfolder}/{f}.mp3"):
        # This word has already been synthesised
        return None

    cmd = [_SPEECHSYNTH_CLT]
    cmd.append("-v")
    cmd.append(voice)
    # cmd.append("-r")
    # cmd.append("89")
    # cmd.append("--file-format=WAVE")
    cmd.append("-o")
    fn = f"{f}.aiff"

    # TODO: assert exists subfolder path

    outpath = f"{dest_folder}/{subfolder}/{fn}"
    cmd.append(outpath)
    cmd.append(w)
    subprocess.run(cmd)
    return outpath


# Requires LAME installed: brew install lame
_LAME_CLT = "/usr/local/bin/lame"


def aiff2mp3(infile_path: str) -> None:
    """Convert AIFF to MP3 using lame."""
    args = [_LAME_CLT]
    args.append(infile_path)
    subprocess.run(args)


_OUT_FOLDER = "static/audio/dict/"


def synthesize_all() -> List[str]:
    """Read all dictionary words, speech-synthesize each word to
    AIFF using the macOS speech synthesizer, and then convert to MP3."""
    words = read_all_words()
    mp3_paths = list()
    for w in words:
        aiff_path = synthesize_word(w, dest_folder=_OUT_FOLDER)
        if aiff_path:
            mp3_path = aiff2mp3(aiff_path)
            os.remove(aiff_path)
            mp3_paths.append(mp3_path)
        aiff_path = synthesize_word(w, dest_folder=_OUT_FOLDER, voice="Alex")
        if aiff_path:
            mp3_path = aiff2mp3(aiff_path)
            os.remove(aiff_path)
            mp3_paths.append(mp3_path)
    return mp3_paths


if __name__ == "__main__":
    """Command line invocation."""
    synthesize_all()
