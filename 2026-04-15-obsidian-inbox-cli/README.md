# Obsidian Inbox CLI

A lightweight Python CLI tool to append notes to Victor's Obsidian inbox (`~/obsidian-vault/0 - Inbox/append-note.md`).

## Purpose

Quickly capture thoughts, tasks, or reminders directly into Obsidian without opening the app. Useful for terminal‑first workflows and automation.

## Features

- **Three input methods**: command‑line argument, stdin, or interactive prompt.
- **Tag support**: Add `#tags` via `--tag` flag (multiple allowed).
- **Atomic writes**: Uses temporary file + rename to avoid corruption.
- **Preserves frontmatter**: Keeps existing YAML frontmatter intact.
- **Zero dependencies**: Standard library only.
- **Timezone‑aware timestamps**: Automatically uses America/Phoenix (Mac mini local time).

## Installation

Copy `obsidian_inbox.py` anywhere in your `PATH` and make it executable:

```bash
chmod +x obsidian_inbox.py
# Optional: symlink to /usr/local/bin
sudo ln -s "$(pwd)/obsidian_inbox.py" /usr/local/bin/obsidian_inbox
```

## Usage

### 1. Command‑line argument
```bash
obsidian_inbox.py "Finish the quarterly review" --tag todo --tag work
```

### 2. Standard input (piping)
```bash
echo "Check rental alerts" | obsidian_inbox.py --tag rental
```

### 3. Interactive prompt (when no argument and stdin is a terminal)
```bash
obsidian_inbox.py
# Enter note (Ctrl‑D to finish):
```

### 4. With multiple tags
```bash
obsidian_inbox.py "New coaching contact: Dan Casey" --tag coach --tag followup
```

## Output Format

Each appended note is added as a block:

```
---
Appended: 2026-04-15T02:00:00-07:00
Note text here #todo #work
```

Blocks are separated by `---` lines.

The existing YAML frontmatter (if present) is preserved at the top of the file.

## Verification

Run the included test suite:

```bash
python3 verify.py
```

The test creates a temporary vault, runs the CLI with various inputs, and validates the output.

## Integration Ideas

- **Cron jobs**: Append nightly‑build summaries automatically.
- **Quick‑log alias**: `alias ql='obsidian_inbox.py'` for rapid capture.
- **Script output**: Pipe `git status`, `docker ps`, or system alerts into Obsidian.
- **Meeting notes**: Combine with `gog calendar` to auto‑create meeting templates.

## Notes

- The target file is hard‑coded to `~/obsidian-vault/0 - Inbox/append-note.md`. Override with environment variable `OBSIDIAN_INBOX_TEST_PATH` for testing.
- Timezone is derived from the system’s local time (America/Phoenix on Victor’s Mac mini).
- If the inbox file does not exist, it will be created (along with parent directories).

## License

Public domain / Unlicense – use as you wish.