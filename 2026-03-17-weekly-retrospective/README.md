# Weekly Retrospective CLI

`weekly_retrospective.py` generates a weekly retrospective markdown report from timestamped entries in daily markdown notes.

It scans files in `~/clawd/memory/daily` by default, extracts lines like:

- `[HH:MM] 🔀 PR #5 in one-play-a-day`
- `[HH:MM] 📋 Decision: ...`
- `[HH:MM] ✅ Deployment: ...`
- `[HH:MM] 💡 Suggestion: ...`

It categorizes entries, deduplicates repeated text across days (keeping the earliest), and produces a report with:

- Summary counts by category
- Chronological events
- Decisions
- PRs
- Deployments
- Suggestions
- TODOs

## Usage

Default: last 7 days, output to stdout:

```bash
python3 weekly_retrospective.py
```

Custom number of days:

```bash
python3 weekly_retrospective.py --days 14
```

Custom date range:

```bash
python3 weekly_retrospective.py --start 2026-03-10 --end 2026-03-17
```

Write output to a file:

```bash
python3 weekly_retrospective.py --output retrospective.md
```

Verbose mode (shows processed files and counts on stderr):

```bash
python3 weekly_retrospective.py --verbose
```

Run with generated sample data:

```bash
python3 weekly_retrospective.py --demo
```

## Verification

Run:

```bash
./verify.sh
```

This executes the CLI with `--demo` and succeeds only if it exits with code `0`.
