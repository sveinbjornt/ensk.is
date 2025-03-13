#!/usr/bin/env python3
"""

Ensk.is - Free and open English-Icelandic dictionary

Copyright (c) 2021-2025 Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or other
materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may
be used to endorse or promote products derived from this software without specific
prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.


Functionality related to generating spoken audio files for dictionary words.

"""

import os
import subprocess
from os.path import exists

from dict import read_all_words


_SPEECHSYNTH_CLT = "/usr/bin/say"  # Requires macOS

assert exists(_SPEECHSYNTH_CLT), "macOS speech synthesizer not found"


def synthesize_word(w: str, dest_folder=None, voice="Daniel") -> str | None:
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


def synthesize_all() -> list[str]:
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
