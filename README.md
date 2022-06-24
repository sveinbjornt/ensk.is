[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Python 3.7](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Build](https://github.com/sveinbjornt/ensk.is/actions/workflows/python-app.yml/badge.svg)]()

# ensk.is

<img src="static/img/favicon-96x96.png" style="float:right; margin-left:20px;" align="right">

**A free and open English-Icelandic dictionary**

This repository contains the data files and software for
[ensk.is](https://ensk.is), a free and open public domain
online English-Icelandic dictionary.

## Background

The author of the original dictionary, Geir T. Zoega (1857-1928),
was an English language teacher and later rector at the Learned
School of Reykjavík in the years 1883-1927. The first edition was
published in 1896. The digitised, extended and sanitised version
presented here is based on the
[much-improved 1932 edition](https://baekur.is/bok/000132498/0/2/Ensk-islenzk_ordabok)
edited by Þorsteinn Þorsteinsson.

The current incarnation of the dictionary has been heavily edited,
updated and fixed in accordance with modern Icelandic orthography.
Many additions have been made to bring the vocabulary into the 21st
century. Various errors in the original text have also been corrected.

The raw dictionary text files are stored [here](data/dict/).

Additions can be viewed [here](data/dict/_add.txt).

## Download

You can download the dictionary in the following formats:

* [⇩ SQLite3 database](https://ensk.is/static/files/ensk_dict.db.zip)
* [⇩ CSV document](https://ensk.is/static/files/ensk_dict.csv.zip)
* [⇩ Plain text](https://ensk.is/static/files/ensk_dict.txt.zip)

## Deployment

The ensk.is web application is implemented using the
[FastAPI](https://fastapi.tiangolo.com/) Python web framework.
To deploy it, you need to set up a Python virtual
environment (3.7+) and install dependencies:

```
$ virtualenv -p /path/to/python3 venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

To build the dictionary data files from plain text source files,
run the following command:

```
$ python gen.py
```

Run the web application via [`uvicorn`](https://www.uvicorn.org/):

```
$ uvicorn app:app --reload
```

## Development

All new dictionary entries should be appended to [ta/dict/_add.txt](data/dict/_add.txt).

To verify the syntax and references of all entries, you can run:

```
$ python verify.py
```

## Dictionary License

This dictionary is in the public domain within all countries where permitted.

The authors waive copyright and related rights in the work worldwide
through the CC0 1.0 Universal public domain dedication.

The person who associated a work with this deed has dedicated the work
to the public domain by waiving all of his or her rights to the work
worldwide under copyright law, including all related and neighboring
rights, to the extent allowed by law.

You can copy, modify, distribute and perform the work, even for
commercial purposes, all without asking permission.

In no way are the patent or trademark rights of any person affected by
CC0, nor are the rights that other persons may have in the work or in
how the work is used, such as publicity or privacy rights.

Unless expressly stated otherwise, the person who associated a work
with this deed makes no warranties about the work, and disclaims
liability for all uses of the work, to the fullest extent permitted by
applicable law. When using or citing the work, you should not imply
endorsement by the author or the affirmer.

## Source license

Copyright (c) 2021-2022 Sveinbjorn Thordarson &lt;<a href="mailto:sveinbjorn@sveinbjorn.org">sveinbjorn@sveinbjorn.org</a>&gt;
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
