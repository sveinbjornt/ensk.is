# TODO list for ensk.is

* [ ] Finish deduplicating the entire corpus
* [ ] Resolve multiple word categories
* [ ] Fuzzy suggestions, matches ("Did you mean X, Y or Z?")
* [ ] Use parallel corpora for finding parallel example usage in text
* [ ] Do lookup of English word cats for each entry (e.g. via WordNet or Webster) and see if there is the appropriate correspondence
* [ ] Write more tests, extend verify.py
* [ ] Find IPA phonetic spelling for *all* words via Wiktionary and other sources
* [ ] Add ensk.is data to Wiktionary
* [ ] Feedback mechanism for missing words
* [ ] Add step to verify.py: check that adjectives are always defined using the masculine
* [ ] If no result found, lemmatize word and try again? Be smart?
* [ ] Smarter handling of -ize vs. -ise variants (e.g. "utilize" vs. "utilise")
* [ ] Support pseudo-regex search using * character
* [ ] Show number of matching results + pagination for large result sets
* [ ] Improve JSON distribution format
* [ ] Add gender for Icelandic noun definitions via BinPackage?
* [ ] Fix "fs. & ao." issue
* [ ] Map word forms to headwords (e.g., "running" -> "run", "better" -> "good", etc.)
* [ ] Add viðskeyti cat (vsk.) e.g. -genic
* [ ] Advanced search
* [ ] Expand ~ headword abbreviation before inserting into DB
* [ ] Fix PDF formatting issue with "-" and soft hyphen
