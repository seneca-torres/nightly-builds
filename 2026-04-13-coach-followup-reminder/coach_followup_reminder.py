#!/usr/bin/env python3
"""CLI for finding overdue and upcoming CRM follow-ups."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
import re
from typing import Iterable

DEFAULT_CONTACTS_DIR = Path("~/clawd/coach-crm/contacts").expanduser()
FRONTMATTER_DELIMITER = "---"
KEY_VALUE_RE = re.compile(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$")


@dataclass
class ReminderContact:
    """Normalized reminder data for a single contact."""

    name: str
    role: str
    school: str
    next_followup: str
    status: str
    days: int
    source_file: str


@dataclass
class ScanStats:
    """Bookkeeping for scan results and recoverable errors."""

    files_seen: int = 0
    markdown_files: int = 0
    files_with_frontmatter: int = 0
    contacts_with_followup: int = 0
    skipped_missing_followup: int = 0
    skipped_outside_horizon: int = 0
    parse_errors: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan coach CRM contacts and report overdue or due-soon follow-ups."
        )
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days ahead to include as due soon (default: 7).",
    )
    parser.add_argument(
        "--output-format",
        choices=("text", "markdown", "json"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each processed file to stderr.",
    )
    return parser.parse_args()


def warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def extract_frontmatter(file_path: Path) -> dict[str, str] | None:
    """Extract a flat YAML frontmatter block using simple line parsing.

    The contact files use a small subset of YAML: one `key: value` pair per line
    between the first two `---` delimiters. Nested YAML is intentionally not
    supported because the tool must use only the Python standard library.
    """

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"unable to read file: {exc}") from exc

    lines = content.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return None

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == FRONTMATTER_DELIMITER:
            end_index = index
            break

    if end_index is None:
        raise ValueError("frontmatter start found but closing delimiter is missing")

    frontmatter: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines[1:end_index], start=2):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        match = KEY_VALUE_RE.match(raw_line)
        if not match:
            raise ValueError(f"malformed frontmatter line {line_number}: {raw_line!r}")

        key = match.group(1).strip()
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        frontmatter[key] = value

    return frontmatter


def build_contact(frontmatter: dict[str, str], file_path: Path, horizon_days: int, today: date) -> ReminderContact | None:
    next_followup = frontmatter.get("next_followup", "").strip()
    if not next_followup:
        return None

    try:
        followup_date = date.fromisoformat(next_followup)
    except ValueError as exc:
        raise ValueError(
            f"invalid next_followup date {next_followup!r}; expected YYYY-MM-DD"
        ) from exc

    days_until = (followup_date - today).days
    if days_until < 0:
        status = "overdue"
    elif days_until <= horizon_days:
        status = "due soon"
    else:
        return None

    name = frontmatter.get("name", "").strip() or file_path.stem.replace("_", " ").replace("-", " ").title()
    role = frontmatter.get("role", "").strip()
    school = frontmatter.get("school", "").strip()

    return ReminderContact(
        name=name,
        role=role,
        school=school,
        next_followup=followup_date.isoformat(),
        status=status,
        days=days_until,
        source_file=str(file_path),
    )


def scan_contacts(contacts_dir: Path, horizon_days: int, verbose: bool = False) -> tuple[list[ReminderContact], ScanStats]:
    stats = ScanStats()
    reminders: list[ReminderContact] = []
    today = date.today()

    if not contacts_dir.exists():
        raise FileNotFoundError(f"contacts directory does not exist: {contacts_dir}")
    if not contacts_dir.is_dir():
        raise NotADirectoryError(f"contacts path is not a directory: {contacts_dir}")

    for file_path in sorted(contacts_dir.iterdir()):
        stats.files_seen += 1
        if file_path.suffix.lower() != ".md":
            continue

        stats.markdown_files += 1
        if verbose:
            print(f"Processing {file_path}", file=sys.stderr)

        try:
            frontmatter = extract_frontmatter(file_path)
            if frontmatter is None:
                warn(f"{file_path}: no YAML frontmatter found")
                continue
            stats.files_with_frontmatter += 1

            reminder = build_contact(frontmatter, file_path, horizon_days, today)
            if reminder is None:
                if frontmatter.get("next_followup", "").strip():
                    stats.skipped_outside_horizon += 1
                else:
                    stats.skipped_missing_followup += 1
                continue

            stats.contacts_with_followup += 1
            reminders.append(reminder)
        except ValueError as exc:
            stats.parse_errors += 1
            warn(f"{file_path}: {exc}")
        except OSError as exc:
            stats.parse_errors += 1
            warn(f"{file_path}: unable to access file: {exc}")

    reminders.sort(key=lambda item: (item.next_followup, item.name.lower()))
    return reminders, stats


def summarize(reminders: Iterable[ReminderContact]) -> dict[str, int]:
    reminder_list = list(reminders)
    overdue = sum(1 for item in reminder_list if item.status == "overdue")
    due_soon = sum(1 for item in reminder_list if item.status == "due soon")
    return {
        "overdue": overdue,
        "due_soon": due_soon,
        "total": len(reminder_list),
    }


def format_text(reminders: list[ReminderContact], summary: dict[str, int]) -> str:
    headers = ["Name", "Role", "School", "Next Follow-up", "Status", "Days"]
    rows = [
        [
            item.name,
            item.role,
            item.school,
            item.next_followup,
            item.status,
            str(item.days),
        ]
        for item in reminders
    ]

    if not rows:
        return (
            "No overdue or due-soon contacts found.\n\n"
            f"Summary: {summary['overdue']} overdue, {summary['due_soon']} due soon, {summary['total']} total"
        )

    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    def format_row(row: list[str]) -> str:
        return "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))

    lines = [format_row(headers), format_row(["-" * width for width in widths])]
    lines.extend(format_row(row) for row in rows)
    lines.append("")
    lines.append(
        f"Summary: {summary['overdue']} overdue, {summary['due_soon']} due soon, {summary['total']} total"
    )
    return "\n".join(lines)


def format_markdown(reminders: list[ReminderContact], summary: dict[str, int]) -> str:
    lines = [
        "| Name | Role | School | Next Follow-up | Status | Days |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for item in reminders:
        lines.append(
            f"| {item.name} | {item.role} | {item.school} | {item.next_followup} | {item.status} | {item.days} |"
        )

    if not reminders:
        lines.append("| _None_ |  |  |  |  |  |")

    lines.append("")
    lines.append(
        f"**Summary:** {summary['overdue']} overdue, {summary['due_soon']} due soon, {summary['total']} total"
    )
    return "\n".join(lines)


def format_json(
    reminders: list[ReminderContact],
    summary: dict[str, int],
    contacts_dir: Path,
    horizon_days: int,
    stats: ScanStats,
) -> str:
    payload = {
        "generated_on": date.today().isoformat(),
        "contacts_directory": str(contacts_dir),
        "horizon_days": horizon_days,
        "contacts": [asdict(item) for item in reminders],
        "summary": summary,
        "scan_stats": asdict(stats),
    }
    return json.dumps(payload, indent=2)


def main() -> int:
    args = parse_args()
    if args.days < 0:
        print("Error: --days must be zero or greater.", file=sys.stderr)
        return 2

    contacts_dir = DEFAULT_CONTACTS_DIR

    try:
        reminders, stats = scan_contacts(contacts_dir, args.days, args.verbose)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    summary = summarize(reminders)

    if args.output_format == "json":
        output = format_json(reminders, summary, contacts_dir, args.days, stats)
    elif args.output_format == "markdown":
        output = format_markdown(reminders, summary)
    else:
        output = format_text(reminders, summary)

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
