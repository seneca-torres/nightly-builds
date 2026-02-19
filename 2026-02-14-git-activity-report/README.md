# Git Activity Report

A simple, production-ready Python CLI that scans `~/clawd` for Git repositories and generates a weekly activity report. It summarizes total commits, per-repository counts, commits grouped by day, author stats, and commit messages with timestamps.

## What it does

- Scans a root directory for Git repositories (default: `~/clawd`).
- Collects commits from the past N days (default: 7).
- Generates a report with totals, breakdowns, daily grouping, author stats, and commit messages.
- Outputs to the console or a file.
- Supports text, markdown, and JSON output formats.

## Installation

No external dependencies. Uses only the Python standard library.

- Requires Python 3.9+.
- Requires `git` available on your PATH.

Optional: make the script executable.

```bash
chmod +x git_activity_report.py
```

## Usage

Scan all repos under `~/clawd` for the past 7 days:

```bash
./git_activity_report.py
```

Specify a custom time window and markdown output:

```bash
./git_activity_report.py --days 14 --format markdown
```

Write to a file:

```bash
./git_activity_report.py --output /tmp/report.txt
```

Limit to specific repos (by name or path):

```bash
./git_activity_report.py --repos repo-one,repo-two
./git_activity_report.py --repos ~/clawd/repo-one,/path/to/other-repo
```

Scan a different root:

```bash
./git_activity_report.py --root ~/src
```

Get JSON output:

```bash
./git_activity_report.py --format json
```

## Sample output (text)

```
Git Activity Report
====================
Root: /Users/yourname/clawd
Days: 7
Since: 2026-02-07T12:00:00+00:00
Generated: 2026-02-14T12:00:00+00:00

Total commits: 5

By repository:
- repo-one: 3 commits
- repo-two: 2 commits

Commits by day:
- 2026-02-13 (2 commits)
  [2026-02-13T09:14:12+00:00] repo-one - Fix parsing edge case (Alice)
  [2026-02-13T15:02:55+00:00] repo-two - Add README (Bob)
- 2026-02-12 (3 commits)
  [2026-02-12T08:44:10+00:00] repo-one - Refactor report builder (Alice)
  [2026-02-12T11:33:27+00:00] repo-one - Add JSON output (Alice)
  [2026-02-12T17:20:03+00:00] repo-two - Update config defaults (Bob)

Author stats:
- Alice <alice@example.com>: 3
- Bob <bob@example.com>: 2
```

## Edge cases handled

- Non-git directories are skipped or flagged when explicitly listed.
- Empty repositories or no commits in the timeframe produce a clear message.
- Missing repos listed in `--repos` are reported as warnings.
- Errors from `git` commands are captured per-repository and do not stop the report.

## Notes

- Commit timestamps are based on the authored date.
- The root scan avoids descending into common large directories (like `node_modules`).
