#!/usr/bin/env python3
"""Analyze Google Calendar events for a date range and visualize time usage."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class EventSegment:
    start: datetime
    end: datetime
    summary: str

    @property
    def minutes(self) -> float:
        return max(0.0, (self.end - self.start).total_seconds() / 60.0)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze Google Calendar event durations.")
    p.add_argument("--date", help="Start date YYYY-MM-DD (default: today)")
    p.add_argument("--days", type=int, default=1, help="Number of days to analyze (default: 1)")
    p.add_argument("--start", type=int, default=9, help="Workday start hour (default: 9)")
    p.add_argument("--end", type=int, default=17, help="Workday end hour (default: 17)")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument("--demo", action="store_true", help="Use built-in sample events")
    p.add_argument(
        "--include-all-day",
        action="store_true",
        help="Include all-day events (otherwise ignored)",
    )
    return p.parse_args()


def parse_iso_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return dt


def parse_event_window(event: dict, include_all_day: bool) -> Optional[Tuple[datetime, datetime]]:
    s = event.get("start", {})
    e = event.get("end", {})

    if "dateTime" in s and "dateTime" in e:
        return parse_iso_datetime(s["dateTime"]), parse_iso_datetime(e["dateTime"])

    if "date" in s and "date" in e:
        if not include_all_day:
            return None
        sd = date.fromisoformat(s["date"])
        ed = date.fromisoformat(e["date"])
        st = datetime.combine(sd, time.min).astimezone()
        en = datetime.combine(ed, time.min).astimezone()
        return st, en

    return None


def split_event_by_day(start: datetime, end: datetime, summary: str) -> List[Tuple[date, EventSegment]]:
    if end <= start:
        return []
    out: List[Tuple[date, EventSegment]] = []
    cur = start
    while cur.date() < end.date():
        nxt = datetime.combine(cur.date() + timedelta(days=1), time.min, tzinfo=cur.tzinfo)
        out.append((cur.date(), EventSegment(cur, nxt, summary)))
        cur = nxt
    out.append((cur.date(), EventSegment(cur, end, summary)))
    return out


def demo_events() -> List[dict]:
    return [
        {
            "summary": "Team standup",
            "start": {"dateTime": "2026-03-18T09:30:00-07:00"},
            "end": {"dateTime": "2026-03-18T10:00:00-07:00"},
        },
        {
            "summary": "Planning",
            "start": {"dateTime": "2026-03-18T11:00:00-07:00"},
            "end": {"dateTime": "2026-03-18T12:15:00-07:00"},
        },
        {
            "summary": "Overnight maintenance",
            "start": {"dateTime": "2026-03-18T23:00:00-07:00"},
            "end": {"dateTime": "2026-03-19T01:00:00-07:00"},
        },
        {
            "summary": "Conference",
            "start": {"date": "2026-03-19"},
            "end": {"date": "2026-03-20"},
        },
    ]


def run_gog_events(start_day: date, days: int) -> List[dict]:
    if shutil.which("gog") is None:
        raise RuntimeError("gog not found in PATH")

    end_day = start_day + timedelta(days=days)
    cmd = [
        "gog", "calendar", "events",
        "--from", start_day.isoformat(),
        "--to", end_day.isoformat(),
        "--all-pages",
        "--json",
        "--results-only",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip() or "gog command failed")

    payload = json.loads(proc.stdout or "[]")
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "items" in payload:
        return payload["items"]
    raise RuntimeError("Unexpected gog JSON format")


def daterange(start_day: date, days: int) -> Iterable[date]:
    for i in range(days):
        yield start_day + timedelta(days=i)


def clip_window(start: datetime, end: datetime, ws: datetime, we: datetime) -> Optional[Tuple[datetime, datetime]]:
    s = max(start, ws)
    e = min(end, we)
    return (s, e) if e > s else None


def format_minutes(minutes: float) -> str:
    t = int(round(minutes))
    h, m = divmod(t, 60)
    return f"{h}h {m}m"


def ascii_timeline(events: List[EventSegment], d: date, start_hour: int, end_hour: int, tz) -> List[str]:
    rows = []
    for h in range(start_hour, end_hour):
        blocks = ["░"] * 4
        for i in range(4):
            b0 = datetime.combine(d, time(hour=h), tzinfo=tz) + timedelta(minutes=15 * i)
            b1 = b0 + timedelta(minutes=15)
            if any(ev.start < b1 and ev.end > b0 for ev in events):
                blocks[i] = "█"
        rows.append(f"{h:02d}:00-{h+1:02d}:00 {' '.join(blocks)}")
    return rows


def textual_pie(meeting: float, free: float) -> List[str]:
    total = meeting + free
    if total <= 0:
        return ["Pie: no time in selected window"]
    ratio = meeting / total
    n = 20
    meet_n = int(round(ratio * n))
    free_n = n - meet_n
    return [
        "Pie (Meeting vs Free):",
        f"[{'●' * meet_n}{'○' * free_n}]",
        f"Meeting {ratio * 100:5.1f}% | Free {(1-ratio) * 100:5.1f}%",
    ]


def analyze(events_raw: List[dict], start_day: date, days: int, start_hour: int, end_hour: int, include_all_day: bool) -> dict:
    if days < 1:
        raise ValueError("--days must be >= 1")
    if not (0 <= start_hour <= 23 and 1 <= end_hour <= 24 and start_hour < end_hour):
        raise ValueError("--start/--end must define a valid workday range")

    tz = datetime.now().astimezone().tzinfo
    by_day: Dict[date, List[EventSegment]] = {d: [] for d in daterange(start_day, days)}
    all_segments: List[EventSegment] = []

    for ev in events_raw:
        w = parse_event_window(ev, include_all_day)
        if not w:
            continue
        s, e = w
        summary = ev.get("summary", "(untitled)")
        for day_key, seg in split_event_by_day(s, e, summary):
            if day_key in by_day:
                by_day[day_key].append(seg)
                all_segments.append(seg)

    total_meeting = 0.0
    total_work = 0.0
    day_rows = []

    for d in daterange(start_day, days):
        ws = datetime.combine(d, time(hour=start_hour), tzinfo=tz)
        we = datetime.combine(d, time.min, tzinfo=tz) + timedelta(hours=end_hour)
        clipped: List[EventSegment] = []
        for ev in by_day[d]:
            c = clip_window(ev.start, ev.end, ws, we)
            if c:
                clipped.append(EventSegment(c[0], c[1], ev.summary))

        meeting_minutes = sum(x.minutes for x in clipped)
        work_minutes = (we - ws).total_seconds() / 60.0
        free_minutes = max(0.0, work_minutes - meeting_minutes)

        hourly = {}
        for h in range(start_hour, end_hour):
            hs = datetime.combine(d, time(hour=h), tzinfo=tz)
            he = hs + timedelta(hours=1)
            hourly[f"{h:02d}:00-{h+1:02d}:00"] = sum(1 for ev in clipped if ev.start < he and ev.end > hs)

        day_rows.append(
            {
                "date": d.isoformat(),
                "meeting_minutes": round(meeting_minutes, 2),
                "free_minutes": round(free_minutes, 2),
                "meeting_count": len(clipped),
                "hourly_distribution": hourly,
                "timeline": ascii_timeline(clipped, d, start_hour, end_hour, tz),
            }
        )
        total_meeting += meeting_minutes
        total_work += work_minutes

    avg = total_meeting / len(all_segments) if all_segments else 0.0
    longest = max((x.minutes for x in all_segments), default=0.0)

    return {
        "date_start": start_day.isoformat(),
        "days": days,
        "workday_start": start_hour,
        "workday_end": end_hour,
        "summary": {
            "total_meeting_minutes": round(total_meeting, 2),
            "total_free_minutes": round(max(0.0, total_work - total_meeting), 2),
            "meeting_count": len(all_segments),
            "average_meeting_minutes": round(avg, 2),
            "longest_meeting_minutes": round(longest, 2),
        },
        "days_detail": day_rows,
    }


def print_report(payload: dict) -> None:
    s = payload["summary"]
    print("Calendar Duration Analyzer")
    print(
        f"Range: {payload['date_start']} for {payload['days']} day(s), "
        f"workday {payload['workday_start']:02d}:00-{payload['workday_end']:02d}:00"
    )
    print()
    print(f"Total meeting time: {format_minutes(s['total_meeting_minutes'])}")
    print(f"Free time: {format_minutes(s['total_free_minutes'])}")
    print(f"Number of meetings: {s['meeting_count']}")
    print(f"Average duration: {format_minutes(s['average_meeting_minutes'])}")
    print(f"Longest meeting: {format_minutes(s['longest_meeting_minutes'])}")
    print()
    print("Hourly meeting distribution:")
    for d in payload["days_detail"]:
        print(f"  {d['date']}")
        for hour, cnt in d["hourly_distribution"].items():
            print(f"    {hour}: {cnt}")
    print()
    print("Workday timeline:")
    for d in payload["days_detail"]:
        print(f"  {d['date']}")
        for line in d["timeline"]:
            print(f"    {line}")
    print()
    for line in textual_pie(s["total_meeting_minutes"], s["total_free_minutes"]):
        print(line)


def main() -> int:
    args = parse_args()
    try:
        start_day = date.fromisoformat(args.date) if args.date else date.today()
    except ValueError:
        print("Invalid --date, expected YYYY-MM-DD", file=sys.stderr)
        return 2

    if args.demo:
        events = demo_events()
    else:
        try:
            events = run_gog_events(start_day, args.days)
        except Exception as e:
            print(f"Warning: gog failed ({e}); falling back to demo events.", file=sys.stderr)
            events = demo_events()

    try:
        report = analyze(events, start_day, args.days, args.start, args.end, args.include_all_day)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())