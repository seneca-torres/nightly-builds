# Coach Follow-up Reminder

`coach_followup_reminder.py` is a small Python CLI that scans the coach CRM contacts directory and highlights contacts whose `next_followup` date is overdue or coming up soon.

## Purpose

The tool reads markdown contact files in `~/clawd/coach-crm/contacts`, parses their YAML frontmatter, and reports contacts that need attention now:

- **Overdue**: `next_followup` is before today.
- **Due soon**: `next_followup` is between today and the configured horizon, inclusive.

Contacts without a `next_followup` field are skipped. Malformed files are reported to stderr without stopping the scan.

## Requirements

- Python 3.9+
- No external dependencies

## Usage

```bash
python3 coach_followup_reminder.py
python3 coach_followup_reminder.py --days 14
python3 coach_followup_reminder.py --output-format markdown
python3 coach_followup_reminder.py --output-format json
python3 coach_followup_reminder.py --verbose
```

## Command-line options

- `--days N` sets the due-soon horizon in days. Default: `7`
- `--output-format {text,markdown,json}` selects the report format. Default: `text`
- `--verbose` prints each processed markdown file to stderr

## Output columns

The report includes these columns:

- `Name`
- `Role`
- `School`
- `Next Follow-up`
- `Status`
- `Days`

`Days` is negative for overdue contacts, `0` for contacts due today, and positive for future follow-ups inside the configured horizon.

## Example text output

```text
Name         Role              School            Next Follow-up  Status    Days
-----------  ----------------  ----------------  --------------  --------  ----
Dan Casey    Owner             OC Sports Performance  2026-02-07  overdue   -66
Alex Smith   Head Coach        Cedar High        2026-04-13      due soon  0
Jamie Reed   Recruiting Lead   Valley College    2026-04-18      due soon  5

Summary: 1 overdue, 2 due soon, 3 total
```

## Verification

Run the included verification script:

```bash
./verify.sh
```

The script creates temporary sample contact files under a temporary `HOME`, runs the CLI in multiple formats, and validates the output.
