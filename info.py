#!/usr/bin/env python3
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


Shared information and constants for the Ensk.is project

"""

import dataclasses
from enum import StrEnum


class PROJECT(StrEnum):
    NAME = "Ensk.is"
    DESCRIPTION = "Opin og frjáls ensk-íslensk orðabók"
    VERSION = "1.0"
    LICENSE = "Public domain"
    EDITOR = "Sveinbjorn Thordarson"
    EMAIL = "sveinbjorn@sveinbjorn.org"
    BASE_URL = "https://ensk.is"
    BASE_DATA_FILENAME = "ensk.is"
    STATIC_FILES_PATH = "static/files/"
    REPO_URL = "https://github.com/sveinbjornt/ensk.is"
