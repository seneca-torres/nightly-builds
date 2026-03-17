#!/usr/bin/env python3
"""Generate weekly retrospective reports from daily markdown files."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ENTRY_RE = re.compile(r"^\s*-\s*\[(\d{2}):(\d{2})\]\s*(.+?)\s*$")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
PR_RE = re.compile(r"\bPR\s*#?\d+\b|\bpull request\b", re.IGNORECASE)

CATEGORY_ORDER = ["PR", "Deployment", "Decision", "Suggestion", "TODO", "Note"]


@dataclass(frozen=True)
class Entry:
    date: dt.date
    time: dt.time
    text: str
    category: str
    source_file: Path

    @property
    def sort_key(self) -> tuple[dt.date, dt.time, str]:
        return (self.date, self.time, self.text)

    @property
    def timestamp(self) -> str:
        return f"{self.date.isoformat()} {self.time.strftime('%H:%M')}"


def parse_date(value: str, flag_name: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{flag_name} must be YYYY-MM-DD: {value}") from exc


def category_for_text(text: str) -> str:
    stripped = text.strip()
    emoji_rules = [
        ("🔀", "PR"),
        ("✅", "Deployment"),
        ("📋", "Decision"),
        ("💡", "Suggestion"),
        ("☑", "TODO"),
        ("📝", "Note"),
    ]
    for emoji, category in emoji_rules:
        if stripped.startswith(emoji):
            return category

    lower = stripped.lower()
    if lower.startswith("decision:") or " decision:" in lower:
        return "Decision"
    if PR_RE.search(stripped):
        return "PR"
    if "deploy" in lower:
        return "Deployment"
    if "suggestion" in lower or "idea:" in lower:
        return "Suggestion"
    if "todo" in lower or "to-do" in lower or "to do" in lower:
        return "TODO"
    return "Note"


def date_from_filename(path: Path) -> dt.date | None:
    match = DATE_RE.search(path.name)
    if not match:
        return None
    try:
        return dt.date.fromisoformat(match.group(1))
    except ValueError:
        return None


def collect_entries(
    daily_dir: Path, start_date: dt.date, end_date: dt.date
) -> tuple[list[Entry], list[tuple[Path, int]]]:
    all_entries: list[Entry] = []
    processed_files: list[tuple[Path, int]] = []

    for path in sorted(daily_dir.glob("*.md")):
        file_date = date_from_filename(path)
        if file_date is None or not (start_date <= file_date <= end_date):
            continue

        count = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                match = ENTRY_RE.match(line)
                if not match:
                    continue
                hours, minutes, text = match.groups()
                count += 1
                all_entries.append(
                    Entry(
                        date=file_date,
                        time=dt.time(hour=int(hours), minute=int(minutes)),
                        text=text.strip(),
                        category=category_for_text(text),
                        source_file=path,
                    )
                )
        processed_files.append((path, count))

    return all_entries, processed_files


def dedupe_entries(entries: list[Entry]) -> list[Entry]:
    earliest_by_text: dict[str, Entry] = {}
    for entry in sorted(entries, key=lambda item: item.sort_key):
        key = " ".join(entry.text.split())
        if key not in earliest_by_text:
            earliest_by_text[key] = entry
    return sorted(earliest_by_text.values(), key=lambda item: item.sort_key)


def render_entry_list(entries: list[Entry]) -> list[str]:
    if not entries:
        return ["_None._"]
    return [f"- [{entry.timestamp}] {entry.text}" for entry in entries]


def generate_report(entries: list[Entry], start_date: dt.date, end_date: dt.date) -> str:
    counts = Counter(entry.category for entry in entries)

    lines = [
        "# Weekly Retrospective",
        "",
        f"Range: {start_date.isoformat()} to {end_date.isoformat()}",
        "",
        "## Summary",
    ]
    if counts:
        ordered = [cat for cat in CATEGORY_ORDER if cat in counts]
        extras = sorted(cat for cat in counts if cat not in CATEGORY_ORDER)
        for category in ordered + extras:
            lines.append(f"- {category}: {counts[category]}")
    else:
        lines.append("_No entries found._")

    lines.extend(["", "## Events (chronological)"])
    lines.extend(render_entry_list(entries))

    decisions = [entry for entry in entries if entry.category == "Decision"]
    prs = [entry for entry in entries if entry.category == "PR" or PR_RE.search(entry.text)]
    deployments = [entry for entry in entries if entry.category == "Deployment"]
    suggestions = [entry for entry in entries if entry.category == "Suggestion"]
    todos = [entry for entry in entries if entry.category == "TODO"]

    lines.extend(["", "## Decisions"])
    lines.extend(render_entry_list(decisions))

    lines.extend(["", "## PRs"])
    lines.extend(render_entry_list(prs))

    lines.extend(["", "## Deployments"])
    lines.extend(render_entry_list(deployments))

    lines.extend(["", "## Suggestions"])
    lines.extend(render_entry_list(suggestions))

    lines.extend(["", "## TODOs"])
    lines.extend(render_entry_list(todos))

    return "\n".join(lines) + "\n"


def build_demo_daily_files(daily_dir: Path) -> tuple[dt.date, dt.date]:
    today = dt.date.today()
    yesterday = today - dt.timedelta(days=1)

    samples = {
        yesterday: [
            "# Daily Notes",
            "- [09:00] 🔀 PR #5 in one-play-a-day",
            "- [10:15] 📋 Decision: switch release cadence to weekly",
            "- [14:10] ✅ Deployment: shipped v1.2.0",
            "- [15:00] Team sync with design",
        ],
        today: [
            "# Daily Notes",
            "- [08:30] 🔀 PR #6 in one-play-a-day",
            "- [09:45] 📋 Decision: switch release cadence to weekly",
            "- [12:20] 💡 Suggestion: automate changelog generation",
            "- [16:00] TODO: add regression tests for onboarding",
        ],
    }

    for day, lines in samples.items():
        target = daily_dir / f"{day.isoformat()}.md"
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return yesterday, today


def compute_range(args: argparse.Namespace) -> tuple[dt.date, dt.date]:
    if args.days <= 0:
        raise argparse.ArgumentTypeError("--days must be greater than 0")

    today = dt.date.today()

    start_date = parse_date(args.start, "--start") if args.start else None
    end_date = parse_date(args.end, "--end") if args.end else None

    if start_date is None and end_date is None:
        end_date = today
        start_date = end_date - dt.timedelta(days=args.days - 1)
    elif start_date is None:
        start_date = end_date - dt.timedelta(days=args.days - 1)
    elif end_date is None:
        end_date = today

    if start_date > end_date:
        raise argparse.ArgumentTypeError("--start cannot be after --end")

    return start_date, end_date


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a weekly retrospective report from daily markdown files."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to include when --start/--end are not provided. Default: 7",
    )
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", help="Write report to this file instead of stdout")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print processed files and entry counts to stderr",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run against generated sample daily files",
    )
    parser.add_argument(
        "--daily-dir",
        default="~/clawd/memory/daily",
        help="Directory containing daily markdown files. Default: ~/clawd/memory/daily",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        start_date, end_date = compute_range(args)
    except argparse.ArgumentTypeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.demo:
        with tempfile.TemporaryDirectory(prefix="weekly-retrospective-demo-") as temp_dir:
            demo_dir = Path(temp_dir)
            demo_start, demo_end = build_demo_daily_files(demo_dir)
            start_date = min(start_date, demo_start)
            end_date = max(end_date, demo_end)
            entries, processed_files = collect_entries(demo_dir, start_date, end_date)
            deduped_entries = dedupe_entries(entries)
            report = generate_report(deduped_entries, start_date, end_date)
    else:
        daily_dir = Path(args.daily_dir).expanduser()
        if not daily_dir.exists():
            print(f"Error: daily directory not found: {daily_dir}", file=sys.stderr)
            return 1
        entries, processed_files = collect_entries(daily_dir, start_date, end_date)
        deduped_entries = dedupe_entries(entries)
        report = generate_report(deduped_entries, start_date, end_date)

    if args.verbose:
        print(
            f"Processed {len(processed_files)} file(s) between {start_date} and {end_date}.",
            file=sys.stderr,
        )
        for path, count in processed_files:
            print(f"- {path}: {count} entr{'y' if count == 1 else 'ies'}", file=sys.stderr)
        print(
            f"Extracted {len(entries)} entries; {len(deduped_entries)} after dedupe.",
            file=sys.stderr,
        )

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
