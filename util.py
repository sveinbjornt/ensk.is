"""

    Ensk.is - Free and open English-Icelandic dictionary

    Copyright (c) 2021-2024, Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>
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


    Various utility functions.


"""

import os
import zipfile
from os.path import exists

import orjson as json


def read_wordlist(fn: str, unique: bool = True) -> list[str]:
    """Read a file containing one word per line.
    Return all words as a list of unique words."""
    words = []

    with open(fn, "r") as file:
        file_contents = file.read()
        lines = file_contents.split("\n")
        for line in lines:
            line = line.strip().replace("  ", " ")
            if not line:  # Skip empty lines
                continue
            if line.startswith("#"):  # Skip comments
                continue
            words.append(line)

    return list(set(words)) if unique else words


def read_json(inpath: str) -> dict[str, str]:
    """Read and parse json file."""
    with open(inpath, "r") as f:
        return json.loads(f.read())


def zip_file(inpath: str, outpath: str, overwrite: bool = True) -> None:
    """Zip a given file, overwrite to destination path."""
    if exists(outpath):
        if overwrite:
            os.remove(outpath)
        else:
            raise FileExistsError(f"File {outpath} already exists")
    with zipfile.ZipFile(outpath, "w", compression=zipfile.ZIP_DEFLATED) as zip_f:
        zip_f.write(inpath)


def human_size(path: str) -> str:
    """Convert byte size to human readable string."""
    size = os.stat(path).st_size
    for x in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0 and x != "KB" and x != "B":
            return f"{size:.1f} {x}"
        elif size < 1024.0:
            return f"{size:.0f} {x}"
        size /= 1024.0
    return f"{size:.1f} TB"


def icelandic_human_size(path: str) -> str:
    """Convert byte size to human readable string in Icelandic."""
    s = human_size(path)
    return s.replace(".", ",")


def perc(a, b, icelandic=False) -> str:
    """Calculate percentage of a/b and return as string."""
    s = f"{100 * a / b:.1f}%"
    if icelandic:
        return s.replace(".", ",")  # Icelandic decimal separator
    return s


def is_ascii(s) -> bool:
    """Check if string is ASCII"""
    return all(ord(c) < 128 for c in s)
