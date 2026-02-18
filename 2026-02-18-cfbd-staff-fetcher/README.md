# CFBD Staff Fetcher 🏈

A Python CLI that pulls college football coaching staff data from the [College Football Data API](https://api.collegefootballdata.com) and exports clean reports ready for Obsidian, spreadsheets, or JSON pipelines.

This is the first seed for Victor's **Coaching Registry** idea — a searchable database of FBS/FCS coaching staffs, career histories, and scheme associations.

## Installation

Requires Python 3 and `requests`:

```bash
pip install requests
```

## Usage

> **Note:** `--demo` is a global flag — place it before the subcommand.

```bash
# List coaching staff for a school/year
python3 cfbd_staff.py staff --school 'Alabama' --year 2024

# Look up a coach's career history by name (fuzzy search)
python3 cfbd_staff.py history --coach 'Nick Saban'

# Export to Obsidian-ready Markdown (YAML frontmatter + tables)
python3 cfbd_staff.py export --school 'Alabama' --year 2024 --format markdown

# Export to CSV (flat per coach-season row)
python3 cfbd_staff.py export --school 'Alabama' --year 2024 --format csv --output staff.csv

# Export to JSON
python3 cfbd_staff.py export --school 'Texas' --year 2024 --format json

# Save markdown directly to your Obsidian vault
python3 cfbd_staff.py export --school 'Alabama' --year 2024 --format markdown \
  --output ~/obsidian-vault/Coaches/alabama-2024-staff.md
```

### Offline / demo mode

```bash
python3 cfbd_staff.py --demo staff
python3 cfbd_staff.py --demo history --coach "Grubb"
python3 cfbd_staff.py --demo export --school "Alabama" --year 2024 --format markdown
```

## Sample output

```
Kalen DeBoer — Head Coach (Hire Date: 2024-01-12)
Ryan Grubb — Offensive Coordinator (Hire Date: 2024-01-19)
Kane Wommack — Defensive Coordinator (Hire Date: 2024-02-01)
```

Markdown export produces Obsidian-ready output:

```markdown
---
tags: [football, coaching-staff, alabama, 2024]
school: Alabama
year: 2024
---
# Alabama Coaching Staff 2024

| Coach | Role | Hire Date |
| --- | --- | --- |
| Kalen DeBoer | Head Coach | 2024-01-12 |
...
```

## Running tests

```bash
python3 -m unittest test_cfbd_staff.py -v
```

5 tests, all passing, zero network calls.

## CFBD API attribution

Data provided by the [College Football Data API](https://api.collegefootballdata.com).
Free for basic queries (no API key required). Some endpoints may require registration.
