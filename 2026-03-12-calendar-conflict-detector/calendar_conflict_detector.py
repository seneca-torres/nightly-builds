#!/usr/bin/env python3
"""Detect calendar conflicts from gog calendar output."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Iterable, Optional


@dataclass
class Event:
    summary: str
    start: datetime
    end: datetime
    duration_minutes: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Detect overlapping events and short breaks using Google Calendar data "
            "from the gog CLI."
        )
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use built-in mock events instead of calling gog.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days ahead to inspect (default: 7).",
    )
    parser.add_argument(
        "--min-break",
        type=int,
        default=5,
        help="Minimum break in minutes between meetings (default: 5).",
    )
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days must be at least 1")
    if args.min_break < 0:
        parser.error("--min-break must be 0 or greater")
    return args


def warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def error(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)


def local_tz():
    return datetime.now().astimezone().tzinfo


def generate_demo_json_lines() -> str:
    tz = local_tz()
    base_date = datetime.now(tz).date() + timedelta(days=1)

    def at(h: int, m: int) -> datetime:
        return datetime.combine(base_date, time(hour=h, minute=m), tzinfo=tz)

    events = [
        {
            "summary": "Daily Standup",
            "start": {"dateTime": at(9, 0).isoformat()},
            "end": {"dateTime": at(9, 30).isoformat()},
        },
        {
            "summary": "Product Sync",
            "start": {"dateTime": at(9, 20).isoformat()},
            "end": {"dateTime": at(10, 0).isoformat()},
        },
        {
            "summary": "1:1 Coaching",
            "start": {"dateTime": at(10, 0).isoformat()},
            "end": {"dateTime": at(10, 30).isoformat()},
        },
        {
            "summary": "Design Review",
            "start": {"dateTime": at(10, 33).isoformat()},
            "end": {"dateTime": at(11, 0).isoformat()},
        },
        {
            "summary": "Lunch",
            "start": {"dateTime": at(12, 0).isoformat()},
            "end": {"dateTime": at(13, 0).isoformat()},
        },
    ]
    return "\n".join(json.dumps(event) for event in events)


def fetch_gog_events(days: int) -> tuple[str, bool]:
    if shutil.which("gog") is None:
        warn("`gog` was not found in PATH. Falling back to demo mode.")
        return generate_demo_json_lines(), True

    cmd = ["gog", "calendar", "list", "--days", str(days)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception as exc:  # pragma: no cover - defensive, OS/runtime dependent.
        warn(f"Failed to execute `{' '.join(cmd)}` ({exc}). Falling back to demo mode.")
        return generate_demo_json_lines(), True

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if stderr:
            warn(f"`gog` returned an error: {stderr}")
        else:
            warn("`gog` returned a non-zero exit code.")
        warn("Falling back to demo mode.")
        return generate_demo_json_lines(), True

    return result.stdout, False


def parse_json_lines(payload: str) -> list[dict[str, Any]]:
    payload = payload.strip()
    if not payload:
        return []

    raw_events: list[dict[str, Any]] = []
    lines = payload.splitlines()

    if len(lines) == 1 and lines[0].lstrip().startswith("["):
        try:
            data = json.loads(lines[0])
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
        except json.JSONDecodeError as exc:
            warn(f"Unable to parse gog output as JSON array ({exc}).")
            return []

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            item = json.loads(stripped)
        except json.JSONDecodeError as exc:
            warn(f"Skipping invalid JSON on line {index}: {exc}")
            continue
        if isinstance(item, dict):
            raw_events.append(item)
        else:
            warn(f"Skipping non-object JSON on line {index}.")

    return raw_events


def parse_iso_datetime(value: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=local_tz())
    return parsed


def parse_time_field(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, dict):
        date_time = value.get("dateTime")
        if isinstance(date_time, str):
            return parse_iso_datetime(date_time)

        date_only = value.get("date")
        if isinstance(date_only, str):
            try:
                day = date.fromisoformat(date_only)
            except ValueError:
                return None
            return datetime.combine(day, time.min, tzinfo=local_tz())

        return None

    if isinstance(value, str):
        return parse_iso_datetime(value)

    return None


def parse_duration_minutes(value: Any) -> Optional[int]:
    if isinstance(value, (int, float)):
        return int(value)

    if isinstance(value, str):
        if value.isdigit():
            return int(value)

        match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?", value)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            return hours * 60 + minutes

    return None


def extract_event(raw: dict[str, Any], index: int) -> Optional[Event]:
    summary = str(raw.get("summary") or raw.get("title") or f"Untitled Event {index}")
    start = parse_time_field(raw.get("start"))
    end = parse_time_field(raw.get("end"))

    if start is None or end is None:
        warn(f"Skipping event '{summary}' because start/end is missing or invalid.")
        return None

    duration = (
        parse_duration_minutes(raw.get("duration"))
        or parse_duration_minutes(raw.get("durationMinutes"))
        or parse_duration_minutes(raw.get("duration_minutes"))
    )

    if end <= start:
        if duration is not None and duration > 0:
            end = start + timedelta(minutes=duration)
        else:
            warn(f"Skipping event '{summary}' because end time is not after start.")
            return None

    duration_minutes = duration
    if duration_minutes is None or duration_minutes <= 0:
        duration_minutes = int((end - start).total_seconds() // 60)

    return Event(summary=summary, start=start, end=end, duration_minutes=duration_minutes)


def load_events(payload: str) -> list[Event]:
    parsed = parse_json_lines(payload)
    events: list[Event] = []
    for idx, item in enumerate(parsed, start=1):
        event = extract_event(item, idx)
        if event is not None:
            events.append(event)
    events.sort(key=lambda evt: (evt.start, evt.end))
    return events


def detect_overlaps(events: list[Event]) -> list[dict[str, Any]]:
    overlaps: list[dict[str, Any]] = []

    for i, first in enumerate(events):
        for second in events[i + 1 :]:
            if second.start >= first.end:
                break
            if first.start < second.end and second.start < first.end:
                overlap_start = max(first.start, second.start)
                overlap_end = min(first.end, second.end)
                minutes = int((overlap_end - overlap_start).total_seconds() // 60)
                overlaps.append(
                    {
                        "first": first,
                        "second": second,
                        "minutes": minutes,
                        "start": overlap_start,
                        "end": overlap_end,
                    }
                )

    return overlaps


def detect_short_breaks(events: list[Event], min_break: int) -> list[dict[str, Any]]:
    short_breaks: list[dict[str, Any]] = []

    for idx in range(len(events) - 1):
        first = events[idx]
        second = events[idx + 1]
        gap_minutes = (second.start - first.end).total_seconds() / 60
        if 0 <= gap_minutes < min_break:
            short_breaks.append({"first": first, "second": second, "gap_minutes": gap_minutes})

    return short_breaks


def format_datetime(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M %Z")


def fmt_minutes(value: float) -> str:
    rounded = round(value, 1)
    if rounded.is_integer():
        return str(int(rounded))
    return str(rounded)


def md_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_markdown_table(rows: Iterable[dict[str, str]]) -> str:
    lines = [
        "| Type | Events | Conflict Details | Suggested Action |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row["Type"]),
                    md_escape(row["Events"]),
                    md_escape(row["Conflict Details"]),
                    md_escape(row["Suggested Action"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def build_rows(events: list[Event], min_break: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    overlaps = detect_overlaps(events)
    short_breaks = detect_short_breaks(events, min_break)

    for overlap in overlaps:
        first = overlap["first"]
        second = overlap["second"]
        rows.append(
            {
                "Type": "Overlap",
                "Events": f"{first.summary} <-> {second.summary}",
                "Conflict Details": (
                    f"Overlap window: {format_datetime(overlap['start'])} to "
                    f"{format_datetime(overlap['end'])} ({overlap['minutes']} min)"
                ),
                "Suggested Action": "Reschedule one event or shorten both meetings.",
            }
        )

    for seq in short_breaks:
        first = seq["first"]
        second = seq["second"]
        rows.append(
            {
                "Type": "Back-to-back",
                "Events": f"{first.summary} -> {second.summary}",
                "Conflict Details": (
                    f"Gap is {fmt_minutes(seq['gap_minutes'])} min between "
                    f"{format_datetime(first.end)} and {format_datetime(second.start)}"
                ),
                "Suggested Action": (
                    f"Insert at least {min_break} min buffer or move one meeting."
                ),
            }
        )

    if not rows:
        rows.append(
            {
                "Type": "No conflicts",
                "Events": "-",
                "Conflict Details": "No overlaps or short breaks detected.",
                "Suggested Action": "No action needed.",
            }
        )

    return rows


def main() -> int:
    args = parse_args()

    using_demo = args.demo
    if using_demo:
        payload = generate_demo_json_lines()
    else:
        payload, fallback_demo = fetch_gog_events(args.days)
        using_demo = fallback_demo

    events = load_events(payload)

    # If gog output exists but cannot be parsed, fallback to demo to keep tool usable.
    if not args.demo and not using_demo and payload.strip() and not events:
        warn("Could not parse any valid events from gog output. Falling back to demo mode.")
        payload = generate_demo_json_lines()
        events = load_events(payload)
        using_demo = True

    if not events:
        warn("No events found for the selected date range.")
        rows = [
            {
                "Type": "No events",
                "Events": "-",
                "Conflict Details": "No calendar events were returned.",
                "Suggested Action": "Try a larger --days window.",
            }
        ]
        print(render_markdown_table(rows))
        return 0

    rows = build_rows(events, args.min_break)
    print(render_markdown_table(rows))

    if using_demo:
        warn("Results are from demo mode mock events.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        error("Interrupted.")
        raise SystemExit(130)
