#!/usr/bin/env python3
"""Quick daily log helper."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path


SECTIONS = {
    "event": "## Events",
    "idea": "## Ideas",
    "todo": "## Todos",
}


def _default_memory_path(date_str: str) -> Path:
    return Path("~").expanduser() / "clawd" / "memory" / "daily" / f"{date_str}.md"


def _read_stdin() -> str:
    data = sys.stdin.read()
    return data.strip("\n")


def _ensure_parent_dir(path: Path) -> None:
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def _init_file(path: Path, date_str: str) -> None:
    template = (
        f"# Daily Log — {date_str}\n\n"
        "## Summary\n"
        "*(no entries yet)*\n\n"
        "## Events\n\n"
    )
    path.write_text(template, encoding="utf-8")


def _get_last_bullets(text: str, count: int = 5) -> list[str]:
    bullets = [line for line in text.splitlines() if line.lstrip().startswith("-")]
    return bullets[-count:]


def _find_insertion_point(lines: list[str], section_header: str) -> int:
    # Find the line index after the section header. If not found, return -1.
    for i, line in enumerate(lines):
        if line.strip() == section_header:
            return i
    return -1


def _find_summary_index(lines: list[str]) -> int:
    for i, line in enumerate(lines):
        if line.strip() == "## Summary":
            return i
    return -1


def _ensure_section(lines: list[str], section_header: str) -> None:
    if any(line.strip() == section_header for line in lines):
        return
    summary_idx = _find_summary_index(lines)
    insert_at = summary_idx + 1 if summary_idx != -1 else len(lines)
    # Insert a blank line before and after for readability.
    if insert_at < len(lines) and lines[insert_at].strip() != "":
        lines.insert(insert_at, "")
        insert_at += 1
    lines.insert(insert_at, section_header)
    lines.insert(insert_at + 1, "")


def _find_date_header_index(lines: list[str], section_header: str, date_header: str) -> int:
    section_idx = _find_insertion_point(lines, section_header)
    if section_idx == -1:
        return -1
    # Search within section until next H2.
    for i in range(section_idx + 1, len(lines)):
        line = lines[i]
        if line.startswith("## "):
            break
        if line.strip() == date_header:
            return i
    return -1


def _append_note(
    path: Path,
    note: str,
    category: str,
    now: datetime,
) -> None:
    section_header = SECTIONS[category]
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    category_title = category.capitalize()
    date_header = f"### [{date_str}] {category_title}"

    if not path.exists():
        _ensure_parent_dir(path)
        _init_file(path, date_str)

    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    _ensure_section(lines, section_header)

    date_idx = _find_date_header_index(lines, section_header, date_header)
    if date_idx == -1:
        section_idx = _find_insertion_point(lines, section_header)
        insert_at = section_idx + 1
        # Ensure a blank line after section header.
        if insert_at < len(lines) and lines[insert_at].strip() != "":
            lines.insert(insert_at, "")
            insert_at += 1
        lines.insert(insert_at, date_header)
        lines.insert(insert_at + 1, "")
        date_idx = insert_at

    # Find end of this date header block (before next header).
    insert_at = date_idx + 1
    while insert_at < len(lines):
        line = lines[insert_at]
        if line.startswith("### ") or line.startswith("## "):
            break
        insert_at += 1

    note_lines = note.splitlines() or [""]
    bullet_prefix = f"- [{time_str}] "
    bullet_lines = [bullet_prefix + note_lines[0]]
    for extra in note_lines[1:]:
        bullet_lines.append("  " + extra)

    if insert_at > 0 and lines[insert_at - 1].strip() != "":
        # Ensure a blank line between existing content and new bullet if needed.
        pass

    lines[insert_at:insert_at] = bullet_lines

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _list_recent(path: Path) -> int:
    if not path.exists():
        print("No entries yet (file does not exist).")
        return 0
    content = path.read_text(encoding="utf-8")
    bullets = _get_last_bullets(content, 5)
    if not bullets:
        print("No bullet entries found.")
        return 0
    print("\n".join(bullets))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append quick notes to a daily log file.")
    parser.add_argument(
        "note",
        nargs="?",
        help="Note text. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "-c",
        "--category",
        default="event",
        choices=sorted(SECTIONS.keys()),
        help="Category section for the note.",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List the last 5 bullet entries from today's file.",
    )
    parser.add_argument(
        "-p",
        "--path",
        help="Path to memory file (defaults to ~/clawd/memory/daily/YYYY-MM-DD.md).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    path = Path(args.path).expanduser() if args.path else _default_memory_path(date_str)

    if args.list:
        try:
            return _list_recent(path)
        except OSError as exc:
            print(f"Error reading file: {exc}", file=sys.stderr)
            return 1

    note = args.note
    if note is None:
        if sys.stdin.isatty():
            print("No note provided. Pass a note or pipe stdin.", file=sys.stderr)
            return 1
        note = _read_stdin()

    if note is None or note.strip() == "":
        print("Empty note. Nothing to append.", file=sys.stderr)
        return 1

    try:
        _append_note(path, note, args.category, now)
    except OSError as exc:
        print(f"Error writing file: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
