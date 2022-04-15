#!/usr/bin/env python3
"""

    Ensk.is - Free and open English-Icelandic dictionary
    
    Copyright (c) 2022, Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>
    All rights reserved.

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

"""

from typing import Optional

import os
import subprocess
from os.path import exists

from util import read_all_words


_SPEECHSYNTH_CLT = "/usr/bin/say"  # Requires macOS


def synthesize_word(w: str, dest_folder=None) -> Optional[str]:
    """Generate a speech-synthesised AIFF audio file from word.
    Returns path to output file."""
    assert dest_folder is not None
    if exists(f"{dest_folder}/{w}.mp3".replace(" ", "_")):
        return None
    args = [_SPEECHSYNTH_CLT]
    args.append("-r")
    args.append("89")
    # args.append("--file-format=WAVE")
    args.append("-o")
    fn = f"{w}.aiff".replace(" ", "_")
    outpath = f"{dest_folder}/{fn}"
    args.append(outpath)
    args.append(w)
    subprocess.run(args)
    return outpath


_LAME_CLT = "/usr/local/bin/lame"  # Requires LAME install


def aiff2mp3(infile_path: str, outfile_path: str = None):
    """Convert AIFF to MP3 using lame."""
    args = [_LAME_CLT]
    args.append(infile_path)
    subprocess.run(args)


_OUT_FOLDER = "static/audio/dict/"


def synthesize_all() -> None:
    """Read all dictionary words, speech-synthesize each word to
    AIFF using the macOS speech synthesizer, and then convert to MP3."""
    words = read_all_words()
    for w in words:
        aiff_path = synthesize_word(w, dest_folder=_OUT_FOLDER)
        if aiff_path:
            mp3_path = aiff2mp3(aiff_path)
            os.remove(aiff_path)


if __name__ == "__main__":
    """Command line invocation."""
    synthesize_all()
