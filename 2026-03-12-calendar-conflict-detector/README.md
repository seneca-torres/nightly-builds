# Calendar Conflict Detector

Simple Python CLI that checks Victor's Google Calendar for:
- Overlapping meetings.
- Back-to-back meetings with too little break time.

It uses `gog` (`gog calendar list --days N`) and falls back to demo/mock events when `gog` is missing or fails.

## Requirements

- Python 3.9+
- `gog` CLI configured for Victor's Google account (for real calendar data)

No third-party Python packages are required.

## Installation

1. Clone this repository.
2. Make scripts executable:

```bash
chmod +x calendar_conflict_detector.py verify.sh
```

## Usage

### Basic run (real calendar via `gog`)

```bash
./calendar_conflict_detector.py
```

### Custom window and break threshold

```bash
./calendar_conflict_detector.py --days 14 --min-break 10
```

### Force demo mode

```bash
./calendar_conflict_detector.py --demo
```

### Run verification

```bash
./verify.sh
```

## Output format

The tool prints a markdown table with columns:
- `Type`
- `Events`
- `Conflict Details`
- `Suggested Action`

Example:

```markdown
| Type | Events | Conflict Details | Suggested Action |
| --- | --- | --- | --- |
| Overlap | Daily Standup <-> Product Sync | Overlap window: 2026-03-13 09:20 PDT to 2026-03-13 09:30 PDT (10 min) | Reschedule one event or shorten both meetings. |
| Back-to-back | Product Sync -> 1:1 Coaching | Gap is 0 min between 2026-03-13 10:00 PDT and 2026-03-13 10:00 PDT | Insert at least 5 min buffer or move one meeting. |
```

## Error handling

- If `gog` is not installed, the tool warns and automatically uses demo mode.
- If `gog` fails (for example, auth issues), the tool prints the error and uses demo mode.
- If no events are returned, the tool exits successfully and prints a table row indicating no events.
- Invalid event rows are skipped with warnings, without crashing the script.

## Cron integration (daily alert)

Run every weekday at 7:30 AM and append output to a log:

```cron
30 7 * * 1-5 cd /Users/vicmacmini/clawd/nightly-builds/2026-03-12-calendar-conflict-detector && ./calendar_conflict_detector.py --days 7 --min-break 5 >> calendar_conflicts.log 2>&1
```

If you prefer email alerts from cron, configure local mail and use command output directly.
