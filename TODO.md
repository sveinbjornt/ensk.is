# TODO list for ensk.is

* [ ] Case-sensitive DB entries
* [ ] Finish deduplicating the entire corpus
* [ ] Improve performance of search (indexing?)
* [ ] Resolve multiple word categories
* [ ] Fuzzy suggestions, matches ("Did you mean X, Y or Z?")
* [ ] Use paralell corpora for finding parallel example usage
* [ ] Do lookup of English word cats for each entry (e.g. via WordNet or Webster) and see if there is the appropriate correspondence
* [ ] Write more tests, extend verify.py
* [ ] Find IPA phonetic spelling for *all* words via Wiktionary
* [ ] Add data to Wiktionary
* [ ] Feedback mechanism for missing words
* [ ] Separate exact match from partial matches visually
* [ ] Mobile app? Packaged Web Application with local fallback?
* [ ] Add step to verify.py: check that adjectives are always defined using the masculine
* [ ] If no result found, lemmatize word and try again? Be smart?
* [ ] Support regex search using * character
* [ ] Show number of matching results + pagination for large result sets
* [ ] Hyphenation for Icelandic words in PDF generation
* [ ] Improve JSON format
* [ ] Add gender for Icelandic noun definitions via BinPackage?
* [ ] Fix "fs. & ao." issue
* [ ] Adjective validation: should always be in masculine case. Use BÍN.
* [ ] "Ertu kannski að leita að íslensk-enskri orðabók?" efst til hægri
* [ ] Look up every entry in Merriam-Webster to validate headwords and POS tags
* [ ] Map word forms to headwords (e.g., "running" -> "run", "utilise" -> "utilize", etc.)
