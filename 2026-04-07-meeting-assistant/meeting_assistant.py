#!/usr/bin/env python3
"""
Meeting Assistant - CLI tool for preparing meetings with coaches and analysts.

Pulls information from:
- Coach CRM (~/clawd/coach-crm/contacts/*.md)
- Google Calendar (via gog CLI)
- Daily memory files
- GitHub PRs/issues (via gh CLI)

Usage:
  python3 meeting_assistant.py prepare <name>
  python3 meeting_assistant.py list
  python3 meeting_assistant.py search <query>
  python3 meeting_assistant.py demo
"""

import os
import sys
import json
import glob
import re
import subprocess
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Configuration
CLAWD_PATH = os.path.expanduser("~/clawd")
CRM_PATH = os.path.join(CLAWD_PATH, "coach-crm", "contacts")
MEMORY_DAILY_PATH = os.path.join(CLAWD_PATH, "memory", "daily")
MEMORY_PEOPLE_PATH = os.path.join(CLAWD_PATH, "memory", "people")
DEMO_MODE = False

# ANSI color codes for terminal output
COLORS = {
    "header": "\033[1;36m",  # Cyan
    "section": "\033[1;34m",  # Blue
    "success": "\033[1;32m",  # Green
    "warning": "\033[1;33m",  # Yellow
    "error": "\033[1;31m",    # Red
    "info": "\033[0;37m",     # White
    "reset": "\033[0m"
}

def color_text(text, color_name):
    """Add color to text for terminal output."""
    if color_name in COLORS:
        return f"{COLORS[color_name]}{text}{COLORS['reset']}"
    return text

def check_tool_available(tool_name):
    """Check if a CLI tool is available."""
    try:
        subprocess.run([tool_name, "--version"], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def parse_markdown_frontmatter(file_path):
    """Parse YAML frontmatter from markdown files."""
    content = Path(file_path).read_text()
    frontmatter = {}
    
    # Match YAML frontmatter between --- markers
    match = re.match(r'^---\n(.*?\n)---\n(.*)', content, re.DOTALL)
    if match:
        yaml_content = match.group(1)
        # Simple YAML parsing (basic key-value)
        for line in yaml_content.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip().strip('"\'')
    
    return frontmatter

def get_crm_contacts():
    """Get all contacts from the coach CRM."""
    contacts = []
    if not os.path.exists(CRM_PATH):
        print(color_text(f"Warning: CRM path not found: {CRM_PATH}", "warning"))
        return contacts
    
    for md_file in glob.glob(os.path.join(CRM_PATH, "*.md")):
        frontmatter = parse_markdown_frontmatter(md_file)
        if frontmatter:
            frontmatter['_file'] = md_file
            contacts.append(frontmatter)
    
    return contacts

def find_contact_by_name(name):
    """Find a contact by name (fuzzy matching)."""
    contacts = get_crm_contacts()
    name_lower = name.lower()
    
    for contact in contacts:
        contact_name = contact.get('name', '').lower()
        if name_lower in contact_name or contact_name in name_lower:
            return contact
        
        # Also check email
        email = contact.get('email', '').lower()
        if name_lower in email:
            return contact
    
    return None

def get_upcoming_meetings(contact):
    """Get upcoming meetings with a contact from Google Calendar."""
    meetings = []
    
    if DEMO_MODE:
        # Demo data
        meetings = [
            {"title": "Weekly Sync with Coach", "start": "2026-04-07T10:00:00", "end": "2026-04-07T11:00:00"},
            {"title": "OPAD Review", "start": "2026-04-08T14:00:00", "end": "2026-04-08T15:00:00"}
        ]
        return meetings
    
    if not check_tool_available("gog"):
        print(color_text("Note: gog CLI not available. Skipping calendar check.", "warning"))
        return meetings
    
    email = contact.get('email')
    if not email:
        print(color_text("No email found for contact. Skipping calendar check.", "warning"))
        return meetings
    
    try:
        # Get meetings for next 7 days
        cmd = [
            "gog", "calendar", "events", "list",
            "--attendees", email,
            "--from", "now",
            "--to", "+7d",
            "--format", "json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            events = json.loads(result.stdout)
            for event in events:
                meetings.append({
                    "title": event.get("summary", "Untitled"),
                    "start": event.get("start", {}).get("dateTime", ""),
                    "end": event.get("end", {}).get("dateTime", ""),
                    "description": event.get("description", "")
                })
    except Exception as e:
        print(color_text(f"Error fetching calendar: {e}", "warning"))
    
    return meetings

def search_memory_interactions(contact_name, days_back=30):
    """Search memory files for recent interactions with a contact."""
    interactions = []
    
    # Search daily memory files
    daily_files = glob.glob(os.path.join(MEMORY_DAILY_PATH, "*.md"))
    daily_files.sort(reverse=True)  # Most recent first
    
    cutoff_date = datetime.now() - timedelta(days=days_back)
    name_lower = contact_name.lower()
    
    for file_path in daily_files:
        # Check if file is recent enough
        try:
            file_date_str = Path(file_path).stem
            file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
            if file_date < cutoff_date:
                continue
        except ValueError:
            continue
        
        content = Path(file_path).read_text()
        
        # Look for mentions of the contact
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if name_lower in line.lower():
                # Get context (3 lines before and after)
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                context = '\n'.join(lines[start:end])
                
                interactions.append({
                    "date": file_date_str,
                    "context": context,
                    "file": file_path
                })
    
    return interactions[:10]  # Limit to 10 most recent

def get_github_activity(contact_name):
    """Get GitHub issues/PRs related to a contact."""
    activity = []
    
    if DEMO_MODE:
        # Demo data
        activity = [
            {"type": "PR", "title": "Add coach profile page", "state": "open", "repo": "seneca-torres/coach-database"},
            {"type": "issue", "title": "Bug: Stats not loading", "state": "closed", "repo": "seneca-torres/pbp-parser"}
        ]
        return activity
    
    if not check_tool_available("gh"):
        print(color_text("Note: gh CLI not available. Skipping GitHub check.", "warning"))
        return activity
    
    # Common repos to check
    repos = [
        "seneca-torres/nightly-builds",
        "seneca-torres/coach-database",
        "seneca-torres/pbp-parser",
        "seneca-torres/pbp-analysis"
    ]
    
    for repo in repos:
        try:
            # Search for mentions
            cmd = [
                "gh", "issue", "list",
                "--repo", repo,
                "--search", f"mentions:{contact_name} OR assignee:{contact_name}",
                "--json", "title,number,state,url"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                issues = json.loads(result.stdout)
                for issue in issues:
                    activity.append({
                        "type": "issue",
                        "title": issue.get("title", ""),
                        "number": issue.get("number", ""),
                        "state": issue.get("state", ""),
                        "url": issue.get("url", ""),
                        "repo": repo
                    })
        except Exception as e:
            print(color_text(f"Error checking repo {repo}: {e}", "warning"))
    
    return activity

def format_report(contact, meetings, interactions, github_activity):
    """Format a meeting preparation report."""
    report = []
    
    # Header
    report.append(color_text(f"╔═══════════════════════════════════════════════════╗", "header"))
    report.append(color_text(f"║           MEETING PREPARATION REPORT             ║", "header"))
    report.append(color_text(f"╚═══════════════════════════════════════════════════╝", "header"))
    report.append("")
    
    # Contact Info
    report.append(color_text("📇 CONTACT INFORMATION", "section"))
    report.append("─" * 40)
    report.append(f"Name: {contact.get('name', 'N/A')}")
    report.append(f"Title: {contact.get('title', 'N/A')}")
    report.append(f"Organization: {contact.get('organization', 'N/A')}")
    report.append(f"Email: {contact.get('email', 'N/A')}")
    report.append(f"Phone: {contact.get('phone', 'N/A')}")
    report.append(f"Last Contact: {contact.get('last_contact', 'N/A')}")
    report.append(f"Next Follow-up: {contact.get('next_followup', 'N/A')}")
    report.append("")
    
    # Upcoming Meetings
    report.append(color_text("📅 UPCOMING MEETINGS", "section"))
    report.append("─" * 40)
    if meetings:
        for i, meeting in enumerate(meetings, 1):
            start_time = meeting.get('start', '').replace('T', ' ')
            report.append(f"{i}. {meeting.get('title', 'Untitled')}")
            report.append(f"   Time: {start_time}")
            if meeting.get('description'):
                desc = textwrap.shorten(meeting.get('description', ''), width=60)
                report.append(f"   Desc: {desc}")
    else:
        report.append("No upcoming meetings found in the next 7 days.")
    report.append("")
    
    # Recent Interactions
    report.append(color_text("🗣️ RECENT INTERACTIONS (Last 30 days)", "section"))
    report.append("─" * 40)
    if interactions:
        for i, interaction in enumerate(interactions, 1):
            report.append(f"{i}. Date: {interaction['date']}")
            report.append(f"   Context: {textwrap.shorten(interaction['context'], width=70)}")
            report.append("")
    else:
        report.append("No recent interactions found in memory files.")
    report.append("")
    
    # GitHub Activity
    report.append(color_text("🐙 GITHUB ACTIVITY", "section"))
    report.append("─" * 40)
    if github_activity:
        for i, item in enumerate(github_activity, 1):
            state_emoji = "✅" if item.get('state') == 'closed' else "⏳"
            report.append(f"{i}. {state_emoji} {item.get('type', 'item').upper()} #{item.get('number', '?')}")
            report.append(f"   {item.get('title', '')}")
            report.append(f"   Repo: {item.get('repo', '')}")
            report.append("")
    else:
        report.append("No GitHub issues/PRs found.")
    report.append("")
    
    # Quick Notes Section
    report.append(color_text("📝 QUICK NOTES (Add your own notes below)", "section"))
    report.append("─" * 40)
    report.append("1. ")
    report.append("2. ")
    report.append("3. ")
    report.append("")
    
    # Footer
    report.append(color_text("Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "info"))
    
    return '\n'.join(report)

def save_report_to_file(report_text, contact_name):
    """Save the report to a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[^\w\s-]', '', contact_name).strip().replace(' ', '_')
    filename = f"meeting_prep_{safe_name}_{timestamp}.md"
    
    with open(filename, 'w') as f:
        f.write(report_text)
    
    print(color_text(f"✅ Report saved to: {filename}", "success"))
    return filename

def list_contacts():
    """List all contacts in the CRM."""
    contacts = get_crm_contacts()
    
    if not contacts:
        print(color_text("No contacts found in CRM.", "warning"))
        return
    
    print(color_text("📋 CRM CONTACTS", "section"))
    print("─" * 60)
    
    for i, contact in enumerate(contacts, 1):
        name = contact.get('name', 'Unknown')
        title = contact.get('title', '')
        organization = contact.get('organization', '')
        
        print(f"{i:2}. {name}")
        if title or organization:
            print(f"    {title}" + (f" at {organization}" if organization else ""))
        print()

def search_contacts(query):
    """Search contacts and interactions."""
    contacts = get_crm_contacts()
    query_lower = query.lower()
    results = []
    
    # Search in contacts
    for contact in contacts:
        name = contact.get('name', '').lower()
        title = contact.get('title', '').lower()
        org = contact.get('organization', '').lower()
        email = contact.get('email', '').lower()
        
        if (query_lower in name or query_lower in title or 
            query_lower in org or query_lower in email):
            results.append({
                "type": "contact",
                "contact": contact,
                "match": "Contact match"
            })
    
    # Search in memory interactions (limited)
    print(color_text(f"Found {len(results)} contact matches for '{query}'", "info"))
    print()
    
    if results:
        print(color_text("🔍 SEARCH RESULTS", "section"))
        print("─" * 60)
        
        for result in results[:5]:  # Show top 5
            contact = result['contact']
            print(f"📇 {contact.get('name', 'Unknown')}")
            print(f"   Title: {contact.get('title', 'N/A')}")
            print(f"   Org: {contact.get('organization', 'N/A')}")
            print(f"   Email: {contact.get('email', 'N/A')}")
            print()
    else:
        print(color_text("No matches found.", "warning"))

def run_demo():
    """Run the tool in demo mode."""
    global DEMO_MODE
    DEMO_MODE = True
    
    print(color_text("🚀 DEMO MODE - Using sample data", "header"))
    print()
    
    # Create a sample contact
    sample_contact = {
        "name": "Coach John Smith",
        "title": "Offensive Coordinator",
        "organization": "University of Arizona",
        "email": "john.smith@arizona.edu",
        "phone": "(520) 555-1234",
        "last_contact": "2026-03-15",
        "next_followup": "2026-04-10"
    }
    
    meetings = get_upcoming_meetings(sample_contact)
    interactions = search_memory_interactions("Coach John Smith")
    github_activity = get_github_activity("Coach John Smith")
    
    report = format_report(sample_contact, meetings, interactions, github_activity)
    print(report)
    
    # Ask if user wants to save
    response = input(color_text("Save this demo report? (y/n): ", "info"))
    if response.lower() == 'y':
        save_report_to_file(report, "Demo_Coach")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Meeting Assistant for coaches and analysts")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Prepare command
    prepare_parser = subparsers.add_parser('prepare', help='Prepare for meeting with a contact')
    prepare_parser.add_argument('name', help='Contact name (partial match OK)')
    prepare_parser.add_argument('--save', action='store_true', help='Save report to file')
    
    # List command
    subparsers.add_parser('list', help='List all contacts in CRM')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search contacts and interactions')
    search_parser.add_argument('query', help='Search query')
    
    # Demo command
    subparsers.add_parser('demo', help='Run in demo mode with sample data')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'prepare':
            contact = find_contact_by_name(args.name)
            if not contact:
                print(color_text(f"❌ Contact not found: {args.name}", "error"))
                print("Available contacts:")
                list_contacts()
                sys.exit(1)
            
            print(color_text(f"🎯 Preparing meeting with: {contact.get('name', 'Unknown')}", "success"))
            print()
            
            meetings = get_upcoming_meetings(contact)
            interactions = search_memory_interactions(contact.get('name', ''))
            github_activity = get_github_activity(contact.get('name', ''))
            
            report = format_report(contact, meetings, interactions, github_activity)
            print(report)
            
            if args.save or DEMO_MODE:
                save_report_to_file(report, contact.get('name', 'Unknown'))
            else:
                print(color_text("💡 Tip: Use --save flag to save this report to a file", "info"))
        
        elif args.command == 'list':
            list_contacts()
        
        elif args.command == 'search':
            search_contacts(args.query)
        
        elif args.command == 'demo':
            run_demo()
    
    except KeyboardInterrupt:
        print(color_text("\n\n👋 Operation cancelled by user.", "info"))
        sys.exit(0)
    except Exception as e:
        print(color_text(f"❌ Error: {e}", "error"))
        sys.exit(1)

if __name__ == "__main__":
    main()