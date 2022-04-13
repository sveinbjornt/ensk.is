# ensk.is

<img src="static/img/favicon-96x96.png" style="float:right; margin-left:20px;" align="right">

**A free and open English-Icelandic dictionary**

This repository contains the data files and software for
[ensk.is](https://ensk.is), a free and open public domain
online English-Icelandic dictionary.

## Background

The author of the original dictionary, Geir T. Zoega (1857-1928),
served as an English teacher and later rector at the Learned
School of Reykjavík in the years 1883-1927. The first edition was
published in 1896. The digitised and sanitised version presented
here is based on the much-improved 1932 edition edited by Þorsteinn
Þorsteinsson.

The current version has been heavily edited, updated and fixed in
accordance with modern Icelandic orthography. Many errors in the
original text have also been corrected.

The raw dictionary text files are stored [here](data/dict/).

## Deployment

Set up Python virtual environment and install dependencies:

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

Run the web application via `gunicorn`:

```
$ gunicorn app:app -w 1 -k uvicorn.workers.UvicornWorker -b "127.0.0.1:8080"
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
