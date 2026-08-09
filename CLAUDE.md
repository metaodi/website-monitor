# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A GitHub Action-driven website monitor. CSV files in `csv/` list websites/RSS feeds to watch (with a CSS selector or feed fields per entry). A scheduled workflow extracts text from each site, diffs it against the last known version stored in `texts/`, and sends a Telegram notification when it changes. Every change is also appended to `notifications.jsonl`, which is rendered into a static site + RSS feed published via GitHub Pages.

## Commands

```bash
uv sync --locked --all-extras --dev   # install dependencies (uv is the package manager, see pyproject.toml/uv.lock)
uv run pytest tests/ -v               # run the full test suite
uv run pytest tests/test_utils.py -v  # run a single test file
uv run pytest tests/test_website_hash.py::TestNormalizeText::test_double_newlines_collapsed -v  # single test

uv run python monitor.py -u <url> -s <css-selector> [-w <seconds>] [--verbose] [--no-verify]  # ad-hoc local watch loop
uv run python lib/website_hash.py -u <url> -s <selector> -t static|dynamic|rss --verbose       # extract+hash one entry, as used by CI
```

There is no linter/formatter configured (no ruff/flake8/black config in `pyproject.toml`). `setup.sh` / `requirements.txt` are stale — the project now uses `uv` exclusively (`.python-version` pins 3.11; `pyproject.toml` requires `>=3.8`).

## Architecture

### Two independent "checker" code paths — use the CI one as the reference

- **`lib/website_hash.py`** is the actual extraction engine used in production. It exposes `get_website_text(url, selector, verify, dl_type)` / `get_website_hash(...)`, dispatching on `dl_type`:
  - `static` → `lib/download.py:download()` (requests) → BeautifulSoup `.select(selector)`
  - `dynamic` → `lib/download.py:download_with_selenium()` (headless Chrome, waits for the selector) → BeautifulSoup
  - `rss` → `lib/download.py:download_rss()` (feedparser); `selector` is a comma-separated list of entry fields (e.g. `title,link`) instead of a CSS selector
  - Extracted strings are deduped, sorted, and joined with `\n` — order-independent, so reordering elements on a page does not trigger a false-positive diff.
- **`lib/check_website.py`** is a legacy, SQLite-driven, all-in-one standalone script (loops over a `website` DB table, diffs against `texts/`, sends Telegram messages itself). It is **not invoked by any workflow** — `check_websites.yml` reimplements the same steps inline instead (see below). It's kept only because `tests/test_check_website.py` still exercises its pure helper functions (extracted via source parsing, since the module has import-time side effects). Don't extend this file for new features; extend `website_hash.py` and the reusable workflow.

### CI pipeline (the real "checker")

`.github/workflows/check_websites.yml` is a **reusable workflow** (`workflow_call`) parameterized by `csv-path` and `check-all`. Per-site workflows (`thalwil.yml`, `rueschlikon.yml`, `job_websites.yml`, `bezirk_horgen.yml`, `test.yml`) each call it on their own cron schedule with their own CSV and Telegram secrets, sharing the `check-websites` concurrency group so they never overlap.

Flow inside `check_websites.yml`:
1. **`build-matrix`** job: `workflow/matrix.sh <csv>` imports the CSV into a throwaway SQLite DB (`workflow/populate_database.sh`) and runs `workflow/build_matrix.py` to emit a GitHub Actions matrix (one entry per active row, or all rows if `check-all`/`--all`).
2. **`notify`** job (matrix, `max-parallel: 5`): for each site, optionally brings up WireGuard (if `proxy == yes`, using the `WIREGUARD_CONFIG` secret) to reach geo-restricted sites, runs `lib/website_hash.py` to fetch+hash+save text to `text/<safe_label>.txt`, diffs it against the committed `texts/<safe_label>.txt`, posts a Telegram message on change, writes a JSON line to `notifications/<safe_label>.jsonl`, and uploads everything as a `output-<safe_label>` artifact. Filenames are derived via `lib/utils.py:sanitize_label_for_filename()` (also exposed as the `workflow/sanitize_label.py` CLI for use in shell steps).
3. **`update_hashes`** job (runs once, after all matrix jobs): downloads all `output-*` artifacts, replays hash/error-count updates into the SQLite DB (`workflow/update_hash.py`, `workflow/increase_error_count.py` via `workflow/update_from_artifacts.sh`), copies new text into `texts/`, appends new notification lines to `notifications.jsonl`, re-exports the DB back to the CSV (`workflow/export_database_to_csv.sh`, sorted by label), and commits+pushes everything back to the branch — then triggers `pages.yml` if anything changed.

`pages.yml` regenerates the static site whenever `notifications.jsonl` or `workflow/generate_site.py` changes on `main`: it runs `generate_site.py` (builds `index.html` + a per-CSV-source `index-<source>.html` + `feed.xml` from `notifications.jsonl`) and deploys the `docs/` output to GitHub Pages.

`pytest.yml` runs the test suite on any push/PR touching `tests/`, `lib/`, or `pyproject.toml`.

### The `texts/` directory is the source of truth for "did it change"

Each monitored entry has a `texts/<safe_label>.txt` file (extracted, normalized text) committed to git. Comparing against this file — not the CSV's `hash` column — is how changes are detected; the `hash` column is only kept for backward compatibility. A `texts/<safe_label>_notify_url.txt` sidecar holds the URL to link to in notifications (relevant for RSS, where the notification link is the feed's channel link, not the feed URL itself). Because `texts/` is committed, `git log`/`git diff` on a text file is the change history for that site.

### CSV schema (`csv/*.csv`)

`label,active,error_count,url,selector,type,proxy,hash` — see README.md for full field semantics. `type` is one of `static` / `dynamic` / `rss`. Each CSV file corresponds to one scheduled workflow and one Telegram chat.

### Tests (`tests/`)

Tests target `lib/` only (mirrors the `pytest.yml` path trigger). `tests/conftest.py` puts `lib/` on `sys.path` so tests `import website_hash`, `import download`, `import utils` directly (not as a package) — new test files should follow the same pattern. HTML/RSS fixtures live in `tests/fixtures/`; `responses` mocks HTTP in `test_download.py`, and a `mock_download` fixture patches `website_hash.dl` for `test_website_hash.py`. `download.py`'s AIA certificate-chain-completion logic (for servers with incomplete cert chains) has its own in-memory cert-chain fixture (`cert_chain`) in `conftest.py`.
