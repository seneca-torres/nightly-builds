# Broadcaster Notes Entity Extractor 🎙️🏈

A prototype pipeline for converting broadcaster notes (Google Docs, plain text) into Obsidian-ready markdown with auto‑detected entities: **coach names**, **school names**, **dates**, and **roles**.

## The Problem

Broadcasters maintain years of notes on coaches and schools across hundreds of Google Docs. Those notes become unwieldy — coaches move between schools, connections are buried, and searching is slow.

## This Solution

1. **Entity detection** – scans plain‑text notes for known coach names (from CFBD staff data), school names (FBS list), dates, and role phrases.
2. **Obsidian‑ready output** – produces a markdown file with YAML frontmatter (`tags`, `mentions`, `dates`) and inline backlinks `[[coach name]]`, `[[school name]]`.
3. **Mentions table** – lists each detected entity with context lines for quick review.

## Installation

No external dependencies beyond Python 3. The script uses only standard libraries.

```bash
# Just clone the repo and run
cd nightly-builds/2026-02-26-coaching-staff-dashboard
python3 extract.py --input notes.txt --output notes.md
```

## Usage

```bash
# Basic extraction with inline backlinks (default)
python3 extract.py --input notes.txt --output notes.md

# Disable inline backlinks (output only summary)
python3 extract.py --input notes.txt --output notes.md --no-inline

# Use your own coach/school lists (edit COACHES, SCHOOLS, ROLES in extract.py)
```

## Example

**Input (`notes.txt`):**
```
Talked to Ryan Grubb about Alabama's offense. He's been OC since 2024-01-19.
Also chatted with Kalen DeBoer, head coach at Alabama.
Meeting with Nick Saban next week (March 3, 2025) to discuss his new role at Texas.
```

**Output (`notes.md`):**
```markdown
---
source: "notes.txt"
coaches:
  - "Nick Saban"
  - "Ryan Grubb"
  - "Kalen DeBoer"
schools:
  - "Alabama"
  - "Texas"
dates:
  - "2024-01-19"
  - "March 3, 2025"
roles:
  - "Head Coach"
---

# Extracted Entities

## Original Text with Backlinks

```
Talked to [[Ryan Grubb]] about [[Alabama]]'s offense. He's been OC since 2024-01-19.
Also chatted with [[Kalen DeBoer]], [[Head Coach]] at [[Alabama]].
Meeting with [[Nick Saban]] next week (March 3, 2025) to discuss his new role at [[Texas]].
```

## Coaches
- Nick Saban
- Ryan Grubb
- Kalen DeBoer

## Schools
- Alabama
- Texas

## Dates
- 2024-01-19
- March 3, 2025

## Roles
- Head Coach

## Backlinks
- [[Alabama]]
- [[Head Coach]]
- [[Kalen DeBoer]]
- [[Nick Saban]]
- [[Ryan Grubb]]
- [[Texas]]
```

## Entity Lists

- **Coaches**: static list of 12 prominent FBS coaches (Saban, Smart, DeBoer, etc.) defined in `extract.py`. Edit `COACHES` variable to add more.
- **Schools**: static list of 12 FBS schools (Alabama, Georgia, Clemson, etc.) defined in `SCHOOLS` variable.
- **Roles**: 10 common coaching roles (Head Coach, Offensive Coordinator, etc.) defined in `ROLES` variable.
- **Dates**: ISO‑like patterns (`YYYY‑MM‑DD`, `MM/DD/YYYY`, `Month DD, YYYY`).

## Next Steps

This is a prototype. Future versions could:

- Integrate Google Docs API for direct import.
- Add fuzzy matching for misspelled names.
- Use CFBD API for real‑time staff lookups.
- Generate a network graph of coach–school relationships.
- Deploy as a web service for broadcasters.

## Credits

Built as part of the **Nightly Builds** “Surprise Me” series.  
Coach data from the [College Football Data API](https://api.collegefootballdata.com).