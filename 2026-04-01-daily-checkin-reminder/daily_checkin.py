#!/usr/bin/env python3
"""
Daily Check-in Reminder CLI 🦉
Helps Victor structure his day and maintain focus across context switches.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any


MEMORY_DAILY_DIR = Path.home() / "clawd" / "memory" / "daily"


def get_today_date() -> str:
    """Return today's date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%D")


def get_current_time() -> str:
    """Return current time in HH:MM format."""
    return datetime.now().strftime("%H:%M")


def ensure_daily_file(date_str: str) -> Path:
    """Ensure the daily memory file exists with proper structure."""
    daily_file = MEMORY_DAILY_DIR / f"{date_str}.md"
    
    if not daily_file.exists():
        MEMORY_DAILY_DIR.mkdir(parents=True, exist_ok=True)
        content = f"""# Daily Log — {date_str}

## Summary
*(no entries yet)*

## Events

"""
        daily_file.write_text(content)
        print(f"📁 Created new daily file: {daily_file}")
    
    return daily_file


def append_checkin_entry(date_str: str, entry_text: str):
    """Append a check-in entry to the daily file."""
    daily_file = ensure_daily_file(date_str)
    time_str = get_current_time()
    
    entry = f"- [{time_str}] 🎯 {entry_text}\n"
    
    # Read current content
    content = daily_file.read_text()
    
    # Find the Events section and append
    if "## Events" in content:
        # Insert after the Events section header
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.strip() == "## Events":
                # Insert after this line
                lines.insert(i + 1, entry)
                break
        else:
            # If Events section not found (shouldn't happen), append at end
            lines.append(entry)
        
        daily_file.write_text("\n".join(lines) + "\n")
    else:
        # Append at end as fallback
        with daily_file.open("a") as f:
            f.write(entry)
    
    print(f"📝 Entry added to {date_str}.md")


def get_calendar_events() -> List[Dict[str, Any]]:
    """Get today's calendar events using gog CLI or fallback to demo."""
    try:
        # Try to use gog CLI
        result = subprocess.run(
            ["gog", "calendar", "events", "--today", "--json", "--results-only", "--max=5", "--no-input"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            events = json.loads(result.stdout)
            return events if isinstance(events, list) else []
        else:
            # gog exists but not authenticated or other error
            return get_demo_calendar_events()
    except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
        # gog not installed or other issues
        return get_demo_calendar_events()


def get_demo_calendar_events() -> List[Dict[str, Any]]:
    """Return demo calendar events for testing."""
    now = datetime.now()
    return [
        {
            "summary": "Team Standup",
            "start": {"dateTime": now.replace(hour=9, minute=0).isoformat()},
            "end": {"dateTime": now.replace(hour=9, minute=30).isoformat()}
        },
        {
            "summary": "Lunch Break",
            "start": {"dateTime": now.replace(hour=12, minute=0).isoformat()},
            "end": {"dateTime": now.replace(hour=13, minute=0).isoformat()}
        },
        {
            "summary": "Project Review",
            "start": {"dateTime": now.replace(hour=14, minute=0).isoformat()},
            "end": {"dateTime": now.replace(hour=15, minute=0).isoformat()}
        }
    ]


def display_calendar():
    """Display today's calendar events."""
    print("\n📅 Today's Calendar:")
    print("-" * 40)
    
    events = get_calendar_events()
    
    if not events:
        print("No events found or calendar unavailable.")
        return
    
    for i, event in enumerate(events, 1):
        summary = event.get("summary", "No title")
        
        # Parse times
        start = event.get("start", {})
        start_time = start.get("dateTime", start.get("date", "All day"))
        
        # Try to extract just the time
        if "T" in start_time:
            try:
                dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                start_time = dt.strftime("%I:%M %p")
            except ValueError:
                pass
        
        print(f"{i}. {summary}")
        print(f"   ⏰ {start_time}")
    
    print("-" * 40)


def prompt_with_default(prompt: str, default: str = "") -> str:
    """Prompt user with optional default value."""
    if default:
        response = input(f"{prompt} [{default}]: ").strip()
        return response if response else default
    else:
        return input(f"{prompt}: ").strip()


def run_full_mode(date_str: str):
    """Run full check-in with all questions."""
    print("\n🦉 Daily Check-in — Full Mode")
    print("=" * 40)
    
    # Yesterday's accomplishments
    print("\n🌟 What did you accomplish yesterday?")
    print("(Enter 3-5 bullet points, one per line. Empty line to finish)")
    yesterday_accomplishments = []
    for i in range(1, 6):
        point = input(f"  {i}. ").strip()
        if not point:
            break
        yesterday_accomplishments.append(point)
    
    # Today's priorities
    print("\n🎯 Top 3 priorities for today:")
    priorities = []
    for i in range(1, 4):
        priority = input(f"  {i}. ").strip()
        if priority:
            priorities.append(priority)
    
    # Blockers
    print("\n🚧 Any blockers or decisions needed?")
    print("(Leave empty if none)")
    blockers = input("  ").strip()
    
    # Energy & focus
    print("\n⚡ Energy level (1-5, where 5 = fully charged):")
    energy = prompt_with_default("  ", "3")
    
    print("\n🎯 Primary focus area today:")
    focus = prompt_with_default("  (Day Job, Sports Analytics, Personal, etc.)", "Day Job")
    
    # Create summary
    summary_lines = []
    summary_lines.append("## Daily Check-in")
    
    if yesterday_accomplishments:
        summary_lines.append("### Yesterday's Wins")
        for point in yesterday_accomplishments:
            summary_lines.append(f"- {point}")
    
    if priorities:
        summary_lines.append("\n### Today's Priorities")
        for i, priority in enumerate(priorities, 1):
            summary_lines.append(f"{i}. {priority}")
    
    if blockers:
        summary_lines.append("\n### Blockers/Decisions")
        summary_lines.append(f"- {blockers}")
    
    summary_lines.append(f"\n### Energy & Focus")
    summary_lines.append(f"- Energy: {energy}/5")
    summary_lines.append(f"- Focus: {focus}")
    
    full_summary = "\n".join(summary_lines)
    
    # Append to daily file
    append_checkin_entry(date_str, f"Daily check-in: {focus} focus, energy {energy}/5")
    
    print("\n✅ Check-in saved!")
    print("\n📋 Summary (copy to Slack/Telegram):")
    print("=" * 40)
    print(full_summary)
    print("=" * 40)


def run_quick_mode(date_str: str):
    """Run quick check-in with just priorities."""
    print("\n🦉 Daily Check-in — Quick Mode")
    print("=" * 40)
    
    print("\n🎯 Top 3 priorities for today:")
    priorities = []
    for i in range(1, 4):
        priority = input(f"  {i}. ").strip()
        if priority:
            priorities.append(priority)
    
    # Create summary
    summary_lines = ["## Quick Check-in", "### Today's Priorities"]
    for i, priority in enumerate(priorities, 1):
        summary_lines.append(f"{i}. {priority}")
    
    full_summary = "\n".join(summary_lines)
    
    # Append to daily file
    if priorities:
        priority_text = ", ".join(priorities[:2])
        append_checkin_entry(date_str, f"Quick check-in: {priority_text}")
    
    print("\n✅ Check-in saved!")
    print("\n📋 Summary:")
    print("=" * 40)
    print(full_summary)
    print("=" * 40)


def run_review_mode():
    """Review last 3 days of check-ins."""
    print("\n🦉 Check-in Review — Last 3 Days")
    print("=" * 40)
    
    today = datetime.now()
    for i in range(3):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%D")
        daily_file = MEMORY_DAILY_DIR / f"{date_str}.md"
        
        print(f"\n📅 {date_str}:")
        if daily_file.exists():
            content = daily_file.read_text()
            # Look for check-in entries
            lines = content.splitlines()
            checkin_lines = [line for line in lines if "🎯" in line or "check-in" in line.lower()]
            
            if checkin_lines:
                for line in checkin_lines[-3:]:  # Show last 3 check-ins
                    print(f"  {line}")
            else:
                print("  No check-ins found")
        else:
            print("  No daily file")


def main():
    parser = argparse.ArgumentParser(
        description="Daily Check-in Reminder CLI 🦉",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s full          # Full check-in with all questions
  %(prog)s quick         # Just priorities
  %(prog)s review        # Review last 3 days
  %(prog)s --calendar    # Show today's calendar events
        """
    )
    
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["full", "quick", "review"],
        default="full",
        help="Check-in mode (default: full)"
    )
    
    parser.add_argument(
        "--calendar",
        "-c",
        action="store_true",
        help="Show today's calendar events"
    )
    
    parser.add_argument(
        "--date",
        "-d",
        help="Use specific date (YYYY-MM-DD) instead of today"
    )
    
    args = parser.parse_args()
    
    date_str = args.date if args.date else get_today_date()
    
    # Show calendar if requested
    if args.calendar:
        display_calendar()
        if args.mode == "full" or args.mode == "quick":
            print()  # Add spacing
    
    # Run selected mode
    if args.mode == "full":
        run_full_mode(date_str)
    elif args.mode == "quick":
        run_quick_mode(date_str)
    elif args.mode == "review":
        run_review_mode()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())