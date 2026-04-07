# GitHub PR Status Dashboard

A lightweight CLI tool that lists open pull requests across a set of GitHub repositories and displays them as a markdown table (or plain text) with PR number, title, author, status checks, and link.

## Purpose

Victor often works across multiple repositories (nightly-builds, portfolio, coach-database, one-play-a-day-app, football-data-adhoc). This tool provides a quick overview of all open PRs, their status, and helps track what needs review or merge.

## Usage

```
python3 pr_status.py [OPTIONS]
```

### Options

- `--repos` – Comma-separated list of repositories in `owner/name` format (default: `seneca-torres/nightly-builds,victorres11/portfolio,victorres11/coach-database,victorres11/one-play-a-day-app,victorres11/football-data-adhoc`)
- `--format` – Output format: `markdown` (default) or `plain`
- `--help` – Show help message

### Examples

**Default (markdown table):**
```bash
python3 pr_status.py
```

**Custom repo list (plain text):**
```bash
python3 pr_status.py --repos victorres11/portfolio,seneca-torres/nightly-builds --format plain
```

## Output Example

Markdown table:
| # | Title | Author | Status | Link |
|---|-------|--------|--------|------|
| 42 | nightly: add github pr status dashboard | seneca-torres | ✅ All checks passed | [#42](https://github.com/seneca-torres/nightly-builds/pull/42) |

Plain text (tab-separated):
```
#	Title	Author	Status	Link
42	nightly: add github pr status dashboard	seneca-torres	✅ All checks passed	https://github.com/seneca-torres/nightly-builds/pull/42
```

## Installation

1. Ensure `gh` CLI is installed and authenticated (`gh auth login`).
2. Clone the nightly-builds repo or copy the script to your workspace.
3. Run with Python 3.8+.

No additional Python dependencies required.

## How It Works

1. For each repository, the script calls `gh pr list --json number,title,author,url,statusCheckRollup`.
2. The `statusCheckRollup` field is parsed to produce a concise status string:
   - `✅ All checks passed`
   - `⚠️ Some checks failing`
   - `⏳ Checks pending`
   - `❌ No checks / unknown`
3. Results are aggregated and printed in the chosen format.

## Error Handling

- If a repository does not exist or the user lacks permissions, it is skipped with a warning.
- If `gh` CLI is not available, the script exits with an error.
- Invalid JSON output from `gh` is caught and reported.

## Future Enhancements

- Add support for filtering by label, assignee, or draft status.
- Include CI/CD run details (e.g., “build failing”, “deploy pending”).
- Cache results for faster repeated runs.
- Integrate with nightly-builds pipeline to auto-post PR status updates to Telegram.

## License

MIT