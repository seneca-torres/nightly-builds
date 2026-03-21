# Rental Alert

`rental_alert.py` runs the existing `rental_finder.py` search, compares fresh results against a local cache, and reports only newly discovered listings.

## Files

- `rental_alert.py`: alert script
- `previous_listings.json`: local cache created/updated by the script
- Fresh search output is read from:
  - `/Users/vicmacmini/clawd/nightly-builds/2026-01-30/listings.json`

## Requirements

- Python 3.9+
- `rental_finder.py` dependencies (already used there): `requests`, `beautifulsoup4`

## Usage

Run in demo mode (default safety mode):

```bash
python rental_alert.py
```

Explicit demo mode:

```bash
python rental_alert.py --demo
```

Run real search mode (no `--demo` passed to `rental_finder.py`):

```bash
python rental_alert.py --real
```

Verbose diagnostics:

```bash
python rental_alert.py --verbose
python rental_alert.py --real --verbose
```

## Output

The script prints new listings in Markdown with:

- address
- price
- beds/baths
- link
- source
- listing date

At the end it prints a verification line:

```text
Verification: <N> new listings found.
```

## How it works

1. Runs `rental_finder.py --search` (plus `--demo` unless `--real` is used).
2. Loads prior cache from `previous_listings.json` (if present).
3. Loads fresh listings from `.../2026-01-30/listings.json`.
4. Compares by `link` URL.
5. Prints listings whose link is not already in cache.
6. Updates cache with merged listings so previously seen links are not re-reported next run.

## Nightly Build Integration

Example cron job (runs daily at 7:00 AM local time):

```cron
0 7 * * * cd /Users/vicmacmini/clawd/nightly-builds/2026-03-21-rental-alert && /usr/bin/python3 rental_alert.py --real >> rental_alert.log 2>&1
```

Common notification integration pattern:

1. Run `rental_alert.py --real`.
2. If verification count is greater than 0, send output to your notifier (email, Slack, Telegram, etc.).
3. Keep `previous_listings.json` persisted between runs.