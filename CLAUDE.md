# CLAUDE.md

## Project

ensk.is is a free, open English-Icelandic dictionary web app (https://ensk.is). Based on Geir T. Zoëga's 1896 dictionary, extended with modern entries.

## Tech Stack

Python 3.12, FastAPI, Jinja2, SQLite, Uvicorn. Linted with ruff, type-checked with pyright.

## Source of Truth

Dictionary data lives in plain text files under `data/dict/` (one file per letter: a.txt–z.txt). Modern additions go in `data/dict/_add.txt`. All generated artifacts (SQLite DB, JSON, CSV, PDF) are derived from these files.

### Entry format

```
WORD CATEGORY. definition in Icelandic
```

Categories: `n.` (noun), `s.` (verb/sögn), `l.` (adjective/lýsingarorð), `ao.` (adverb/atviksorð), `fs.` (preposition/forsetning), `gr.` (article/greinir), `st.` (conjunction/samtenging). Multiple meanings separated by `;`. Bracketed text `[like this]` denotes usage examples or clarification.

## Build & Run

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify dictionary source files (syntax/integrity checks)
python gen/verify.py

# Generate dictionary data (SQLite DB, JSON, CSV, etc.)
python gen/gen.py

# Run the web app
uvicorn app:app --host localhost --port 8000

# Run tests
python -m pytest
```

No Makefile — commands are run directly.

## CI Pipeline (GitHub Actions)

Runs on every push/PR. Steps in order:
1. `ruff check *.py routes/*.py gen/*.py tests/*.py`
2. `curlylint templates/*.html`
3. `pyright *.py routes/*.py gen/*.py tests/*.py`
4. `python gen/verify.py`
5. `python gen/gen.py`
6. `python -m pytest`

## Code Style

- Ruff with Black defaults: 88 char lines, 4-space indent, double quotes
- Target: Python 3.12
- Config in `.ruff.toml`

## Project Layout

```
app.py              FastAPI app factory, middleware, CSP headers
dict.py             Dictionary parsing, definition unpacking
db.py               SQLite database singleton and queries
util.py             Shared utilities
settings.py         Configuration (pydantic-settings, reads .env)

routes/
  api.py            REST API: /api/search, /api/item, /api/suggest, /api/metadata
  web.py            HTML pages: /, /item/{word}, /about, /files, /stats, etc.
  core.py           Shared route logic, caching, DB init
  static.py         Static file serving

gen/
  gen.py            Main generator: text files → SQLite + exports
  verify.py         Dictionary syntax and integrity validation
  audio.py          Speech synthesis (macOS only, uses `say`)
  macos.py          Apple Dictionary bundle generation
  pdf/              PDF export

data/
  dict/             Dictionary source text files (a.txt–z.txt, _add.txt)
  wordlists/        English word lists for validation
  ipa/              IPA pronunciation data (uk/, us/)
  freq/             Word frequency data
  syllables/        Syllable breakdowns

templates/          Jinja2 HTML templates
static/             CSS, JS, images, fonts, audio, generated files
tests/              pytest tests (test_dict.py, test_routes.py, test_util.py)
tools/              Analysis scripts (IPA, syllables, frequency, duplicates, etc.)
```

## Key Patterns

- The `data/dict/` text files are canonical. Edit those, then regenerate with `gen/gen.py`.
- `_add.txt` contains all modern additions (not in Zoëga's original). New entries go here unless they are corrections to existing entries in a letter file.
- Letter files (a.txt–z.txt) are sorted alphabetically, one entry per line.
- `gen/verify.py` should pass before `gen/gen.py` is run.
- The web app opens `dict.db` in read-only mode. Regenerate the DB to pick up text file changes.

## Deployment

`build_deploy.sh` runs gen.py + audio.py, then rsyncs to `root@ensk.is:/www/ensk.is/html/`.
