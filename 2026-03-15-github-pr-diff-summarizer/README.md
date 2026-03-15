# PR Diff Summarizer

`pr_diff_summarizer.py` is a zero-dependency Python CLI that fetches a GitHub PR diff via `gh` and outputs a Markdown summary.

## Features

- Accepts either:
  - PR URL: `https://github.com/owner/repo/pull/123`
  - Repo + PR number: `owner/repo 123`
- Uses GitHub CLI:
  - `gh pr view --json title,url`
  - `gh pr diff`
- Parses unified diff to report:
  - File status: added / modified / deleted
  - Additions/deletions per file
  - Total additions/deletions
- Optional highlights:
  - Large files (`>500` changed lines by default)
  - Binary files
  - Suspicious patterns in added lines: `TODO`, `FIXME`, `console.log`
- Demo mode for offline testing from `sample_diff.txt`

## Requirements

- Python 3.9+
- `gh` CLI installed and authenticated (only for non-demo mode)

## Usage

### Demo mode (offline)

```bash
python3 pr_diff_summarizer.py --demo
```

### Real PR by URL

```bash
python3 pr_diff_summarizer.py https://github.com/owner/repo/pull/123
```

### Real PR by repo + number

```bash
python3 pr_diff_summarizer.py owner/repo 123
```

### Custom demo diff path

```bash
python3 pr_diff_summarizer.py --demo --demo-diff ./sample_diff.txt
```

### Change large-file threshold

```bash
python3 pr_diff_summarizer.py owner/repo 123 --large-threshold 800
```

## Verification

```bash
chmod +x verify.sh
./verify.sh
```

## Example output (truncated)

```markdown
# PR Diff Summary

## [Demo PR: Offline sample diff](https://github.com/example/repo/pull/123)

| File | Status | Additions | Deletions |
|---|---:|---:|---:|
| `src/app.js` | modified | 2 | 1 |
...
```