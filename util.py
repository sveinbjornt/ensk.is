"""

Ensk.is - Free and open English-Icelandic dictionary

Copyright (c) 2021-2025, Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>
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

from typing import Any

import os
import asyncio
from pathlib import Path
import zipfile
import shutil
from os.path import exists
from cachetools.keys import hashkey
from collections import OrderedDict
from functools import wraps

import orjson as json


def read_wordlist(fn: str, unique: bool = True) -> list[str]:
    """Read a file containing one word per line.
    Return all words as a list of unique words."""
    words = []

    with open(fn, "r") as file:
        file_contents = file.read()
        lines = file_contents.split("\n")
        for line in lines:
            ln = line.strip().replace("  ", " ")
            if not ln:  # Skip empty lines
                continue
            if ln.startswith("#"):  # Skip comments
                continue
            words.append(ln)

    return words


def read_json(inpath: str) -> dict[str, Any]:
    """Read and parse json file. Assumes dict (object)."""
    with open(inpath, "r") as f:
        return json.loads(f.read())


def archive_directory(directory_path: str) -> str:
    """Create a zip archive of a directory."""
    # Get the absolute path to ensure correct directory handling
    abs_path = os.path.abspath(directory_path)

    # Get parent directory and directory name
    parent_dir = os.path.dirname(abs_path)
    dir_name = os.path.basename(abs_path)

    # Set the base name for the archive (will be the output filename without extension)
    base_name = os.path.join(os.path.dirname(abs_path), dir_name)

    # Create the archive
    archive_path = shutil.make_archive(
        base_name=base_name,  # Output name (without extension)
        format="zip",  # Archive format
        root_dir=parent_dir,  # The root directory to start archiving from
        base_dir=dir_name,  # The directory to archive (relative to root_dir)
    )

    return archive_path


def zip_file(inpath: str, outpath: str, overwrite: bool = True) -> None:
    """Zip a given file, overwrite to destination path."""
    if exists(outpath):
        if overwrite:
            os.remove(outpath)
        else:
            raise FileExistsError(f"File {outpath} already exists")
    if Path(inpath).is_dir():
        archive_directory(inpath)
    else:
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


def perc(a: int | float, b: int | float, icelandic: bool = False) -> str:
    """Calculate percentage of a/b and return as string."""
    s = f"{(100 * (a / b)):.1f}%"
    if icelandic:
        return s.replace(".", ",")  # Icelandic decimal separator
    return s


def is_ascii(s: str) -> bool:
    """Check if string is ASCII"""
    return all(ord(c) < 128 for c in s)


def sing_or_plur(s: str | int) -> bool:
    """Check if a number is singular or plural in Icelandic."""
    return str(s).endswith("1") and not str(s).endswith("11")


def silently_remove(path: str) -> None:
    """Silently remove file or directory."""
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except Exception:
        pass


def cache_response(maxsize=None):
    """Decorator that caches responses from FastAPI async functions with optional size limit.

    Args:
        maxsize: Maximum number of entries to keep in cache. None means unlimited.
    """

    # For direct @cache_response use (without parentheses)
    if callable(maxsize):
        func = maxsize
        maxsize = None
        cache = OrderedDict()
        lock = asyncio.Lock()

        @wraps(func)
        async def direct_wrapper(*args, **kwargs):
            key = hashkey(*args, **kwargs)

            async with lock:
                if key in cache:
                    # Move the key to the end to mark it as recently used
                    value = cache.pop(key)
                    cache[key] = value
                    return value

                # Key not in cache, call the function
                result = await func(*args, **kwargs)  # type: ignore
                cache[key] = result
                return result

        return direct_wrapper

    # For @cache_response(100) use with parameters
    def decorator(func):
        cache = OrderedDict()
        lock = asyncio.Lock()

        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = hashkey(*args, **kwargs)

            async with lock:
                if key in cache:
                    # Move the key to the end to mark it as recently used
                    value = cache.pop(key)
                    cache[key] = value
                    return value

                # Key not in cache, call the function
                result = await func(*args, **kwargs)
                cache[key] = result

                # If we've exceeded the maxsize, remove least recently used item
                if maxsize is not None and len(cache) > maxsize:
                    cache.popitem(
                        last=False
                    )  # Remove the first item (least recently used)

                return result

        return wrapper

    return decorator
