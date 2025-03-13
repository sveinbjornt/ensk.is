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

Tests for ensk.is

"""

# NB: This test needs to run after all the other tests and
# should be kept at the bottom of the source file.
# def test_db() -> None:
#     """Test database wrapper."""
#     # We only run these tests in CI environment
#     if not in_ci_env():
#         return

#     from db import EnskDatabase

# # Delete any pre-existing database file
# delete_db()

# # Reinstantiate DB wrapper
# e = EnskDatabase().reinstantiate()

# # The database is initially empty, so we should get no results
# entries = e.read_all_entries()
# assert len(entries) == 0
# entries = e.read_all_additions()
# assert len(entries) == 0
# # entries = e.read_all_duplicates()
# # assert len(entries) == 0

# # Add an entry
# e.add_entry("cat", "n. köttur", "", "", 0)

# # Make sure there's only a single entry now
# entries = e.read_all_entries()
# assert len(entries) == 1
# entries = e.read_all_additions()
# assert len(entries) == 1
