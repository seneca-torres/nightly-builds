# Calendar Duration Analyzer

`calendar_duration_analyzer.py` is a lightweight Python CLI tool that analyzes Google Calendar event durations and shows how workday time is spent.

## Features
- Uses `gog` CLI to fetch events.
- `--date YYYY-MM-DD` (default: today).
- `--days N` for multi-day analysis.
- Handles timed events, multi-day events (split by day), and optional all-day inclusion.
- Computes:
  - Total meeting time
  - Free time in workday window
  - Number of meetings
  - Average and longest meeting
  - Hourly distribution
- Outputs:
  - Text summary
  - ASCII workday timeline (`█` meeting, `░` free)
  - Simple ASCII pie visualization
- Optional JSON output via `--json`
- `--demo` mode (no `gog` dependency needed)

## Usage

Run with live calendar data:
```bash
python3 calendar_duration_analyzer.py
```

Specific date and range:
```bash
python3 calendar_duration_analyzer.py --date 2026-03-18 --days 3
```

Custom workday:
```bash
python3 calendar_duration_analyzer.py --start 8 --end 18
```

Include all-day events:
```bash
python3 calendar_duration_analyzer.py --include-all-day
```

JSON output:
```bash
python3 calendar_duration_analyzer.py --json
```

Demo mode:
```bash
python3 calendar_duration_analyzer.py --demo
```

## Verify
```bash
python3 verify.py
```

## Notes
- Tool uses `gog calendar events --from ... --to ... --json --results-only`.
- If `gog` is unavailable or authentication fails, the tool falls back to demo events.