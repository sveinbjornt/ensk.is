# TODO list for ensk.is

* [ ] Add more words
* [ ] Case-sensitive DB entries
* [ ] Finish deduplicating the database
* [ ] Resolve multiple word categories
* [ ] Fuzzy suggestions, matches ("Did you mean X, Y or Z?")
* [ ] Use paralell corpora for finding parallel example usage
* [ ] Do lookup of English word cats for each entry (e.g. via WordNet or Webster) and see if there is the appropriate correspondence
* [ ] Write more tests, extend verify.py
* [ ] Rm IPA data from the DB file made available for download
* [ ] Find IPA phonetic spelling for *all* words via Wiktionary
* [ ] Add this corpus's data to Wiktionary
* [ ] Feedback mechanism for missing words
* [ ] Separate exact match from partial matches visually
* [ ] Mobile app? Packaged Web Application with local fallback?
* [ ] Add step to verify.py: check that adjectives are always defined using the masculine
* [ ] If no result found, lemmatize word and try again? Be smart?
* [ ] Dark mode (will require cookies :/)
* [ ] Support search for strings shorter than 3 chars, but only deliver exact results
* [ ] Support regex search using * character
* [ ] Show number of matching results
* [ ] Hyphenation for Icelandic words in PDF generation
* [ ] Hyphenation-data for English words in PDF generation
* [ ] Improve JSON format
* [ ] Add gender for Icelandic noun definitions via BinPackage
