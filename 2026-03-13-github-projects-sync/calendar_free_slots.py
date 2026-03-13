#!/usr/bin/env python3
"""
Calendar Free Slots Finder

Finds free time slots in Google Calendar using gog CLI.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, time
from typing import List, Tuple, Optional


def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO 8601 datetime string (with or without timezone)."""
    # Remove microseconds if present, ignore timezone for simplicity
    if '.' in dt_str:
        dt_str = dt_str.split('.')[0]
    if 'Z' in dt_str:
        dt_str = dt_str.replace('Z', '')
    return datetime.fromisoformat(dt_str)


def parse_gog_event(event: dict) -> Optional[Tuple[datetime, datetime]]:
    """Extract start and end datetime from gog event."""
    start = event.get('start', {})
    end = event.get('end', {})
    # All-day events have 'date' field; ignore them
    if 'date' in start or 'date' in end:
        return None
    if 'dateTime' not in start or 'dateTime' not in end:
        return None
    try:
        start_dt = parse_iso_datetime(start['dateTime'])
        end_dt = parse_iso_datetime(end['dateTime'])
        return (start_dt, end_dt)
    except (KeyError, ValueError):
        return None


def fetch_events(days: int = 1) -> List[Tuple[datetime, datetime]]:
    """Fetch events from gog CLI for the next `days` days."""
    cmd = ['gog', 'calendar', 'list', '--json']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        events = data.get('events', [])
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error fetching events: {e}", file=sys.stderr)
        return []
    
    parsed = []
    for ev in events:
        slot = parse_gog_event(ev)
        if slot:
            parsed.append(slot)
    return parsed


def filter_events_by_date(events: List[Tuple[datetime, datetime]], 
                          start_date: datetime, end_date: datetime):
    """Filter events that overlap with the date range."""
    filtered = []
    for s, e in events:
        # If event ends before start_date or starts after end_date, skip
        if e < start_date or s > end_date:
            continue
        filtered.append((s, e))
    return filtered


def find_free_slots(events: List[Tuple[datetime, datetime]], 
                    day_start: time, day_end: time,
                    days: int) -> List[Tuple[datetime, datetime]]:
    """Find free slots within working hours for the next `days` days."""
    now = datetime.now()
    free_slots = []
    for day_offset in range(days):
        day = now.date() + timedelta(days=day_offset)
        day_start_dt = datetime.combine(day, day_start)
        day_end_dt = datetime.combine(day, day_end)
        # Collect events that intersect this day
        day_events = []
        for s, e in events:
            if e < day_start_dt or s > day_end_dt:
                continue
            day_events.append((max(s, day_start_dt), min(e, day_end_dt)))
        # Sort by start
        day_events.sort(key=lambda x: x[0])
        # Find gaps
        current = day_start_dt
        for s, e in day_events:
            if s > current:
                free_slots.append((current, s))
            current = max(current, e)
        if current < day_end_dt:
            free_slots.append((current, day_end_dt))
    return free_slots


def format_slot(slot: Tuple[datetime, datetime]) -> str:
    s, e = slot
    duration = e - s
    hours = duration.total_seconds() / 3600
    return f"{s.strftime('%Y-%m-%d %H:%M')} - {e.strftime('%H:%M')} ({hours:.1f}h)"


def main():
    parser = argparse.ArgumentParser(description='Find free slots in Google Calendar.')
    parser.add_argument('--days', type=int, default=2, help='Number of days to look ahead (default 2)')
    parser.add_argument('--start', default='09:00', help='Start of working hours (HH:MM)')
    parser.add_argument('--end', default='17:00', help='End of working hours (HH:MM)')
    parser.add_argument('--demo', action='store_true', help='Use demo data instead of gog')
    args = parser.parse_args()
    
    try:
        day_start = datetime.strptime(args.start, '%H:%M').time()
        day_end = datetime.strptime(args.end, '%H:%M').time()
    except ValueError:
        print(f"Invalid time format. Use HH:MM", file=sys.stderr)
        sys.exit(1)
    
    if args.demo:
        print("Running in demo mode (no gog call).", file=sys.stderr)
        # Create some mock events for today
        now = datetime.now()
        events = []
        # Example: an event from 10:00 to 11:30 today
        event_start = datetime.combine(now.date(), time(10, 0))
        event_end = datetime.combine(now.date(), time(11, 30))
        events.append((event_start, event_end))
    else:
        events = fetch_events(args.days)
    
    # Filter events to the requested date range
    start_date = datetime.now()
    end_date = start_date + timedelta(days=args.days)
    events = filter_events_by_date(events, start_date, end_date)
    
    free_slots = find_free_slots(events, day_start, day_end, args.days)
    
    if not free_slots:
        print("No free slots found within working hours.")
        return
    
    print(f"Found {len(free_slots)} free slot(s):")
    for slot in free_slots:
        print(f"  • {format_slot(slot)}")


if __name__ == '__main__':
    main()