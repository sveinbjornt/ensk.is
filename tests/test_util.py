#!/usr/bin/env python3
"""

Ensk.is - Free and open English-Icelandic dictionary

Copyright (c) 2025 Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>

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

Tests for ensk.is utility functions.

"""

import os
import sys
import shutil
import tempfile
import zipfile

# Add parent dir to path so we can import from there
basepath, _ = os.path.split(os.path.realpath(__file__))
src_path = os.path.join(basepath, "..")
sys.path.append(src_path)

import util  # noqa: E402


def test_is_ascii() -> None:
    """Test is_ascii function."""
    assert util.is_ascii("Hello world") is True
    assert util.is_ascii("Halló heimur") is False
    assert util.is_ascii("12345!@#$%") is True
    assert util.is_ascii("café") is False
    assert util.is_ascii("") is True
    assert util.is_ascii(" ") is True
    assert util.is_ascii("\n") is True
    assert util.is_ascii("\t") is True
    assert util.is_ascii("Það") is False


def test_read_json() -> None:
    """Test read_json function."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        f.write('{"key1": "value1", "key2": "value2"}')
        fname = f.name

    try:
        data = util.read_json(fname)
        assert isinstance(data, dict)
        assert len(data) == 2
        assert data["key1"] == "value1"
        assert data["key2"] == "value2"
    finally:
        os.unlink(fname)


def test_sing_or_plur() -> None:
    """Test sing_or_plur function."""
    assert util.sing_or_plur("1") is True
    assert util.sing_or_plur(1) is True
    assert util.sing_or_plur("21") is True
    assert util.sing_or_plur(21) is True
    assert util.sing_or_plur("11") is False
    assert util.sing_or_plur(11) is False
    assert util.sing_or_plur("2") is False
    assert util.sing_or_plur(2) is False
    assert util.sing_or_plur("0") is False


def test_perc() -> None:
    """Test perc function."""
    assert util.perc(50, 100) == "50.0%"
    assert util.perc(25, 100) == "25.0%"
    assert util.perc(33, 100) == "33.0%"
    assert util.perc(33, 100, icelandic=True) == "33,0%"
    assert util.perc(66.6, 100) == "66.6%"
    assert util.perc(66.6, 100, icelandic=True) == "66,6%"


def test_read_wordlist() -> None:
    """Test read_wordlist function."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("word1\nword2\n# Comment\n\nword3  extra\nword2\n")
        fname = f.name

    try:
        # Test with unique=False
        words = util.read_wordlist(fname)
        assert len(words) == 4
        assert words.count("word2") == 2
    finally:
        os.unlink(fname)


def test_human_size() -> None:
    """Test human_size function."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        # Create a file of exactly 1024 bytes
        f.write(b"x" * 1024)
        fname = f.name

    try:
        assert util.human_size(fname) == "1 KB"

        # Test icelandic version
        assert util.icelandic_human_size(fname) == "1 KB"

        # Modify file to be exactly 2048 bytes
        with open(fname, "wb") as f:
            f.write(b"x" * 2048)

        assert util.human_size(fname) == "2 KB"

        # Modify file to be exactly 1MB + 100KB
        with open(fname, "wb") as f:
            f.write(b"x" * (1024 * 1024 + 102400))

        assert util.human_size(fname) == "1.1 MB"
        assert util.icelandic_human_size(fname) == "1,1 MB"
    finally:
        os.unlink(fname)


def test_silently_remove() -> None:
    """Test silently_remove function."""
    # Test with a file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        file_path = f.name

    assert os.path.exists(file_path)
    util.silently_remove(file_path)
    assert not os.path.exists(file_path)

    # Test with a directory
    dir_path = tempfile.mkdtemp()
    assert os.path.exists(dir_path)
    util.silently_remove(dir_path)
    assert not os.path.exists(dir_path)

    # Test with non-existent path
    util.silently_remove("non_existent_path")  # Should not raise an exception


def test_archive_directory() -> None:
    """Test archive_directory function."""
    # Create a temporary directory with some files
    temp_dir = tempfile.mkdtemp()
    try:
        # Create some files in the temp directory
        for i in range(3):
            file_path = os.path.join(temp_dir, f"file{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"Content for file {i}")

        # Test archiving the directory
        archive_path = util.archive_directory(temp_dir)
        try:
            # Check that the archive was created
            assert os.path.exists(archive_path)
            assert archive_path.endswith(".zip")

            # Verify it's a valid zip file
            assert zipfile.is_zipfile(archive_path)

            # Check the contents of the zip file
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                file_list = zip_ref.namelist()
                dir_name = os.path.basename(temp_dir)

                # Zip should contain the dir name and the 3 files
                assert f"{dir_name}/" in file_list
                for i in range(3):
                    assert f"{dir_name}/file{i}.txt" in file_list
        finally:
            # Clean up the created archive
            util.silently_remove(archive_path)
    finally:
        # Clean up the temp directory
        shutil.rmtree(temp_dir)


def test_zip_file() -> None:
    """Test zip_file function."""
    # Test zipping a file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Test content")
        source_path = f.name

    zip_path = f"{source_path}.zip"

    try:
        # Test zipping a file
        util.zip_file(source_path, zip_path)

        # Check that zip file was created
        assert os.path.exists(zip_path)
        assert zipfile.is_zipfile(zip_path)

        # Check the contents
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            file_list = zip_ref.namelist()
            # The path stored in the zip has the leading slash removed
            assert source_path.lstrip("/") in file_list

        # Test overwrite parameter
        # First, create a new zip at the same path
        with open(zip_path, "w") as f:
            f.write("This should be overwritten")

        # Overwrite should work by default
        util.zip_file(source_path, zip_path)
        assert zipfile.is_zipfile(zip_path)  # Still a valid zip

        # Test with overwrite=False (should raise FileExistsError)
        try:
            util.zip_file(source_path, zip_path, overwrite=False)
            assert False, "Should have raised FileExistsError"
        except FileExistsError:
            pass  # Expected exception
    finally:
        # Clean up
        util.silently_remove(source_path)
        util.silently_remove(zip_path)
