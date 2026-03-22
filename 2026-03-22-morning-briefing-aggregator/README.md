# Morning Briefing Aggregator

Runs existing nightly‑build tools and combines their outputs into a single markdown report.

## What it does

- **Daily Standup** – runs `standup.py` (from `2026-02-16-daily-standup`) with `--output markdown`
- **GitHub PR Status** – runs `gh_pr_status.py` (from `2026-02-19-github-pr-status`) with `--format markdown`
- **Rental Alerts** – runs `rental_finder.py` (from `2026-01-30`) with `--report` (or `--demo`)
- **Calendar** – optionally runs `gog calendar today --format=json` (if `gog` is installed)

If a tool fails (non‑zero exit, missing script, etc.) that section is skipped and a warning is printed.

## Usage

```bash
# Generate a full report (default output: briefing.md)
python3 morning_briefing.py

# Run in demo mode (rental_finder uses --demo)
python3 morning_briefing.py --demo

# Specify output file
python3 morning_briefing.py --output my_briefing.md
```

## Verification

```bash
python3 verify.py
```

The verification script runs the aggregator with `--demo` and checks that an output file is created and non‑empty.

## Integration ideas

- Add a cron job that runs the aggregator every morning and sends the markdown to Victor’s Telegram/Slack
- Pipe the output through `pandoc` to generate a PDF or HTML
- Extend with more nightly‑build tools (calendar‑conflict detector, GitHub daily PR digest, etc.)

## Dependencies

- Python 3 (stdlib only)
- The three nightly‑build tools must be present in their respective sibling directories
- `gog` CLI (optional, for calendar)

## Notes

- All paths are relative to the nightly‑builds root (`../`).
- The script is designed to fail gracefully; missing tools produce warnings, not crashes.
- Demo mode is only supported for `rental_finder.py`; other tools run normally.

## Example output

```
# Morning Briefing – 2026‑03‑22 09:00

## 📅 Daily Standup
…

## 🔁 GitHub PR Status
…

## 🏠 Rental Alerts
…

## 📅 Calendar
…

## ⚠️ Warnings
- Calendar skipped: gog calendar failed: command not found
```