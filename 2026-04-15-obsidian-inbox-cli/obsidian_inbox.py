#!/usr/bin/env python3
"""
Obsidian Inbox CLI - Append notes to Victor's Obsidian inbox.

Usage:
  obsidian_inbox.py [--tag TAG...] [NOTE_TEXT]
  obsidian_inbox.py [--tag TAG...] -i
  echo "NOTE_TEXT" | obsidian_inbox.py [--tag TAG...]

If NOTE_TEXT is provided as an argument, it's used.
If no arguments and stdin is a terminal, prompts interactively.
Otherwise reads from stdin.

Appends to ~/obsidian-vault/0 - Inbox/append-note.md with format:
---
Appended: YYYY-MM-DDTHH:MM:SS-HH:MM
NOTE_TEXT #tag1 #tag2
---
"""

import sys
import os
import argparse
import datetime
import tempfile
import shutil
from pathlib import Path

# Allow environment override for testing
VAULT_PATH = Path(os.environ.get('OBSIDIAN_INBOX_TEST_PATH',
    str(Path.home() / "obsidian-vault" / "0 - Inbox" / "append-note.md")))
TIMEZONE = "America/Phoenix"

def get_current_time():
    """Return current timestamp string in ISO format with local timezone."""
    # Use system local time (Mac mini is America/Phoenix)
    now = datetime.datetime.now()
    # Format as ISO with timezone offset (no colon in offset for compatibility)
    # We'll produce something like '2026-04-15T02:00:00-07:00'
    # Python's isoformat doesn't include colon in offset, but Obsidian uses colon.
    # We'll manually format.
    # Get offset
    import time
    utc_offset = time.localtime().tm_gmtoff
    offset_hours = utc_offset // 3600
    offset_minutes = (utc_offset % 3600) // 60
    sign = '+' if utc_offset >= 0 else '-'
    offset_str = f"{sign}{abs(offset_hours):02d}:{offset_minutes:02d}"
    iso_time = now.strftime("%Y-%m-%dT%H:%M:%S")
    return f"{iso_time}{offset_str}"

def read_frontmatter(content_lines):
    """Return (frontmatter_lines, rest_lines) where frontmatter is between --- markers."""
    if not content_lines or content_lines[0].strip() != "---":
        return [], content_lines
    end_idx = None
    for i in range(1, len(content_lines)):
        if content_lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return [], content_lines
    frontmatter = content_lines[:end_idx + 1]
    rest = content_lines[end_idx + 1:]
    return frontmatter, rest

def append_note(text, tags):
    """Append note text with tags to the inbox file."""
    # Ensure vault directory exists
    VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing content
    if VAULT_PATH.exists():
        with open(VAULT_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = []
    
    frontmatter, rest = read_frontmatter(lines)
    
    # Prepare new note block
    timestamp = get_current_time()
    tag_str = " ".join(f"#{tag}" for tag in tags) if tags else ""
    note_line = text.rstrip()
    if tag_str:
        note_line += " " + tag_str
    
    new_block = f"\n---\nAppended: {timestamp}\n{note_line}\n"
    
    # Write atomically: create temp file in same directory
    temp_fd, temp_path = tempfile.mkstemp(dir=VAULT_PATH.parent, suffix='.md.tmp')
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            # Write frontmatter
            if frontmatter:
                f.writelines(frontmatter)
            # Write rest of content (after frontmatter)
            if rest:
                f.writelines(rest)
            # Append new block
            f.write(new_block)
        # Replace original file
        shutil.move(temp_path, VAULT_PATH)
    except Exception:
        os.unlink(temp_path)
        raise

def main():
    parser = argparse.ArgumentParser(
        description="Append a note to Obsidian inbox.",
        epilog="If no NOTE_TEXT provided, reads from stdin (non‑interactive) or prompts (interactive)."
    )
    parser.add_argument(
        "note_text",
        nargs="?",
        default=None,
        help="Note text (optional)"
    )
    parser.add_argument(
        "--tag", "-t",
        action="append",
        default=[],
        help="Add tag(s) to the note (can be repeated)"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Force interactive prompt (ignore stdin)"
    )
    args = parser.parse_args()
    
    text = args.note_text
    tags = args.tag
    
    # Determine input source
    if text is not None:
        # Use command line argument
        pass
    elif not sys.stdin.isatty() and not args.interactive:
        # Read from stdin (piped/redirected)
        text = sys.stdin.read().strip()
    else:
        # Interactive prompt
        sys.stderr.write("Enter note (Ctrl‑D to finish):\n")
        lines = []
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                lines.append(line)
        except KeyboardInterrupt:
            sys.stderr.write("\nCancelled.\n")
            sys.exit(1)
        text = "".join(lines).strip()
    
    if not text:
        sys.stderr.write("No note text provided.\n")
        sys.exit(1)
    
    try:
        append_note(text, tags)
        sys.stderr.write(f"✓ Appended to {VAULT_PATH}\n")
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()