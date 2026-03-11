# GitHub Issue to Obsidian

Simple Python CLI to fetch a GitHub issue via `gh` and write an Obsidian note.

## Requirements

- Python 3.8+
- GitHub CLI (`gh`) installed and authenticated
- No external Python dependencies

## Usage

```bash
python3 github_issue_to_obsidian.py --url https://github.com/owner/repo/issues/123
```

```bash
python3 github_issue_to_obsidian.py --repo owner/repo --issue 123
```

```bash
python3 github_issue_to_obsidian.py --url https://github.com/owner/repo/issues/123 --output-dir ~/obsidian-vault/inbox
```

```bash
python3 github_issue_to_obsidian.py --repo owner/repo --issue 123 --dry-run
```

## Output naming

`GitHub - owner-repo-#123 - title-slug.md`  
Slug is lowercase, spaces -> hyphens, non-alphanumeric removed, max 50 chars.

## Verification

```bash
chmod +x github_issue_to_obsidian.py verify.sh
./verify.sh
```

## Daily workflow

1. Run tool during issue triage.
2. Save to Obsidian inbox (`--output-dir ~/obsidian-vault/inbox`).
3. Add personal notes/tasks under imported content.
4. Re-run later to overwrite or auto-rename with timestamp.