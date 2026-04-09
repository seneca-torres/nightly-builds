## What this does

Adds a Python CLI that finds free time slots in Google Calendar using the `gog` CLI.

- Fetches upcoming events via `gog calendar list --json`
- Filters out all‑day events (they don't block hours)
- Finds gaps between events within configurable working hours (default 9am–5pm)
- Outputs free slots with start/end times and duration

## How to test

```bash
cd 2026-03-13-github-projects-sync
python3 calendar_free_slots.py --demo
```

Demo mode uses a mock event (10:00–11:30 today) and shows free slots around it.

For real usage, ensure `gog` is installed and authenticated, then:

```bash
python3 calendar_free_slots.py --days 2 --start 08:00 --end 18:00
```

## Verification

Run `./verify.sh` to confirm the tool works (checks demo mode, invalid time handling, and help text).

## Notes

- All‑day events are ignored.
- Timezone handling is basic (uses local system time).
- No external Python dependencies (standard library only).

Built as a Nightly “Surprise Me” Build (2026‑03‑13).