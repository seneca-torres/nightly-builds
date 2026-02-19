# standup.py - Daily Standup Summary for Victor

A tiny, dependency-free Python CLI that compiles Victor’s daily standup from three local sources: memory notes, git activity, and cron job runs. It’s built to be fast and predictable for morning briefings.

## What it does (and why)
- **Memory highlights** from yesterday’s daily note in `~/clawd/memory/daily/`
- **Git activity** across all repos in `~/clawd/` for the same day
- **Cron jobs** that ran yesterday from `~/.clawdbot/cron_runs/`
- **Active projects** inferred from repo names and memory mentions

This gives Victor a single, clean summary without needing external services or heavy setup.

## Requirements
- Python 3.8+ (stdlib only)
- `git` available in PATH

## Installation
No install needed. Just run the script:

```bash
./standup.py
```

Optionally make it runnable anywhere:

```bash
ln -s /path/to/standup.py ~/bin/standup
```

## Usage
```bash
./standup.py
```

```bash
./standup.py --date 2026-02-15
```

```bash
./standup.py --output text
```

```bash
./standup.py --output json
```

```bash
./standup.py --verbose
```

### Options
- `--date YYYY-MM-DD` - target day (defaults to yesterday)
- `--output text|markdown|json` - output format (default: markdown)
- `--verbose` - include full commit messages and full memory content

## Sample output (markdown)
```markdown
# Daily Standup - 2026-02-15

## 📝 Memory Highlights
- Finished refactor of onboarding flow
- Followed up with support on billing issue
- Drafted roadmap notes for Q2

## 💻 Git Activity
- **web-dashboard** (2 commits)
  - Victor: Fix token refresh edge case
  - Victor: Add billing webhooks docs

## 🤖 Cron Jobs
- nightly_backup - success (2026-02-15T02:00:01)
- metrics_rollup - success (2026-02-15T03:15:44)

## 🎯 Active Projects
- web-dashboard
- roadmap
```

## Morning workflow integration
A simple way to integrate this into Victor’s morning routine:

1. Add to shell profile for quick access:
   ```bash
   alias standup='~/clawd/nightly-builds/2026-02-16-daily-standup/standup.py'
   ```
2. Run it with a coffee:
   ```bash
   standup
   ```
3. Paste the markdown into Slack/Notion/Email as the daily briefing.

## Notes
- Memory file path is fixed to `~/clawd/memory/daily/YYYY-MM-DD.md`.
- Git scanning walks all repos under `~/clawd/` and uses `git log` for the date window.
- Cron parsing scans `~/.clawdbot/cron_runs/*.jsonl` and matches runs by date.
