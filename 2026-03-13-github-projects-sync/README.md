# Calendar Free Slots Finder 🌤️

A Python CLI that finds free time slots in your Google Calendar using the `gog` CLI.

## What It Does

- Fetches your upcoming calendar events via `gog calendar list --json`
- Filters out all‑day events (they don't block time slots)
- Looks for gaps between events within configured working hours (default 9am–5pm)
- Outputs a list of free slots with start/end times and duration

## Usage

```bash
python3 calendar_free_slots.py [--days N] [--start HH:MM] [--end HH:MM] [--demo]
```

### Options

- `--days` – number of days to look ahead (default: 2)
- `--start` – start of working hours in 24‑hour format (default: 09:00)
- `--end` – end of working hours (default: 17:00)
- `--demo` – run with mock data instead of calling `gog` (useful for testing)

### Examples

```bash
# Default: next 2 days, 9am–5pm
python3 calendar_free_slots.py

# Look 5 days ahead, 8am–6pm
python3 calendar_free_slots.py --days 5 --start 08:00 --end 18:00

# Demo mode (no gog required)
python3 calendar_free_slots.py --demo
```

## How It Works

1. Calls `gog calendar list --json` and parses the JSON response.
2. Extracts start/end times from each event (ignores all‑day events).
3. For each day in the requested range, sorts events and finds gaps between them that fall within the working‑hour window.
4. Prints each free slot with its date, start/end time, and duration.

## Dependencies

- Python 3.8+
- [`gog` CLI](https://github.com/victorres11/gog) installed and authenticated (for real usage)

No extra Python packages are required (standard library only).

## Verification

Run the verification script to confirm the tool works:

```bash
./verify.sh
```

The verification script will:
1. Run the tool in demo mode (should produce free slots)
2. Run the tool with a simple gog call (should not crash)
3. Check that the output format is as expected

## Notes

- All‑day events are ignored because they don't block specific hours.
- Events that partially overlap the working‑hour window are clipped to the window.
- The tool currently uses local timezone (the same as the `gog` output). Timezone handling is basic; ensure your system clock matches your calendar's timezone.

## Future Improvements

- Add timezone awareness
- Support for multiple calendars
- Option to exclude lunch breaks or other recurring blocks
- Interactive mode to pick a slot and create a new event

---

Built as part of the Nightly “Surprise Me” Build (2026‑03‑13).