# GitHub Daily PR Digest

A Python CLI that generates a daily digest of GitHub Pull Request activity across configured repositories.

## Features

- Fetches PRs created, updated, merged, or closed in the last 24 hours (or any specified date)
- Lists PRs where you are requested for review
- Outputs clean Markdown, plain text, or JSON
- Supports demo mode with sample data (no API calls)
- Zero external dependencies (only Python standard library + `gh` CLI)
- Graceful error handling: skips repos where `gh` fails, warns about missing config

## Installation

1. Ensure you have the GitHub CLI (`gh`) installed and authenticated:
   ```bash
   gh auth status
   ```

2. Clone the nightly-builds repo (or copy the script anywhere).

3. Make the script executable:
   ```bash
   chmod +x github_daily_pr_digest.py
   ```

## Configuration

Create a config file `~/.github_daily_pr_digest/repos.txt` with one repository per line:

```
seneca-torres/nightly-builds
victorres11/baseball-scorecard
victorres11/pbp-analysis
```

Lines starting with `#` are ignored.

Alternatively, pass repositories directly via `--repos`.

## Usage

### Basic (today's activity, Markdown output)
```bash
./github_daily_pr_digest.py
```

### Specify a date
```bash
./github_daily_pr_digest.py --date 2026-03-18
```

### Use demo mode (no `gh` calls)
```bash
./github_daily_pr_digest.py --demo
```

### Output JSON
```bash
./github_daily_pr_digest.py --output json
```

### Override repos via command line
```bash
./github_daily_pr_digest.py --repos seneca-torres/nightly-builds victorres11/portfolio
```

### Use a custom repos file
```bash
./github_daily_pr_digest.py --repos-file /path/to/my_repos.txt
```

## Sample Output (Markdown)

```markdown
# GitHub PR Digest for 2026-03-19

**Total PRs:** 12

## New PRs (3)
- **[seneca-torres/nightly-builds#123](https://github.com/seneca-torres/nightly-builds/pull/123)** Sample PR
  - Author: @octocat | Status: open | Labels: `bug` | Assignees: @user1
  - Updated: 2026-03-19T10:00:00Z

## Merged PRs (2)
...
```

## Integration with Cron

Add a daily cron job to generate a digest and send it to Slack/Telegram:

```bash
0 9 * * * cd /path/to/nightly-builds/2026-03-19-github-daily-pr-digest && ./github_daily_pr_digest.py --output markdown | send-to-slack.sh
```

## Verification

Run the included verification script:

```bash
python3 verify.py
```

This will:
1. Run the tool in demo mode
2. Check that Markdown, text, and JSON outputs are generated without errors
3. Validate the structure of the JSON output

## Limitations

- Requires `gh` CLI installed and authenticated.
- Only works with repositories you have read access to.
- Date filtering uses GitHub's search window (may not include PRs updated exactly at midnight).
- Review requests are fetched for the current authenticated user only.

## License

MIT