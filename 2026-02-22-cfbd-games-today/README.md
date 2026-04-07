# CFBD Games Today

Simple Python CLI that fetches today's college football games from the College Football Data (CFBD) API and prints a formatted table.

## Requirements

- Python 3.9+
- Optional: `requests` (falls back to the standard library if missing)
- CFBD API key (free registration at CollegeFootballData.com)

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests
```

`requests` is optional. If you skip it, the script uses `urllib`.

## Usage

```bash
export CFBD_API_KEY="your_key_here"
python cfbd_games_today.py
```

Use cached sample data for a quick demo:

```bash
python cfbd_games_today.py --demo
```

The script determines today's date in the America/Phoenix timezone and pulls games for the current year. It uses a simple heuristic to pick `regular` vs `postseason` (mid-December through January).

If you don't have a key yet, register for free at CollegeFootballData.com and set it via the `CFBD_API_KEY` environment variable. You can always run with `--demo` to use cached sample data without authentication.

## Example output

```
start_time  away_team   home_team  TV    status
----------  ----------  ---------  ----  ---------
6:30 PM     Ohio State  Michigan   ABC   scheduled
7:00 PM     Alabama     Georgia    ESPN  final
```

## Notes

- Games are filtered by matching the `start_date` calendar day to today (timezone ignored for the match).
- Status is normalized to: `scheduled`, `in-progress`, or `final`.
- If no games are found, the script prints a friendly message and exits.
