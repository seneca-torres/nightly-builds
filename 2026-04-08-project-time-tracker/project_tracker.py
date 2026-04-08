#!/usr/bin/env python3
"""
Project Time Tracker & Prioritization Dashboard
A CLI tool to help track time spent on projects and visualize priorities.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
import math

class ProjectTracker:
    def __init__(self, data_dir=None):
        if data_dir is None:
            self.data_dir = Path.home() / ".config" / "project-tracker"
        else:
            self.data_dir = Path(data_dir)
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.projects_file = self.data_dir / "projects.json"
        self.entries_file = self.data_dir / "entries.json"
        
        # Load data
        self.projects = self._load_json(self.projects_file, default=[])
        self.entries = self._load_json(self.entries_file, default=[])
    
    def _load_json(self, path, default=None):
        """Load JSON file, return default if file doesn't exist."""
        if path.exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return default if default is not None else []
        return default if default is not None else []
    
    def _save_json(self, path, data):
        """Save data to JSON file."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_project(self, name, category, priority, estimated_hours):
        """Add a new project."""
        # Check if project already exists
        for project in self.projects:
            if project['name'].lower() == name.lower():
                print(f"⚠️  Project '{name}' already exists.")
                return False
        
        project = {
            'name': name,
            'category': category,
            'priority': int(priority),
            'estimated_hours_per_week': float(estimated_hours),
            'actual_hours_spent': 0.0,
            'created_at': datetime.now().isoformat()
        }
        
        self.projects.append(project)
        self._save_json(self.projects_file, self.projects)
        print(f"✅ Added project: {name}")
        return True
    
    def log_time(self, project_name, date, duration, description=""):
        """Log time for a project."""
        # Find project
        project = None
        for p in self.projects:
            if p['name'].lower() == project_name.lower():
                project = p
                break
        
        if not project:
            print(f"❌ Project '{project_name}' not found.")
            return False
        
        # Parse date if needed
        if date.lower() == 'today':
            date_str = datetime.now().strftime('%Y-%m-%d')
        elif date.lower() == 'yesterday':
            date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            # Validate date format
            try:
                datetime.strptime(date, '%Y-%m-%d')
                date_str = date
            except ValueError:
                print(f"❌ Invalid date format: {date}. Use YYYY-MM-DD or 'today'/'yesterday'.")
                return False
        
        entry = {
            'project': project['name'],
            'date': date_str,
            'duration': float(duration),
            'description': description,
            'logged_at': datetime.now().isoformat()
        }
        
        self.entries.append(entry)
        project['actual_hours_spent'] += float(duration)
        
        self._save_json(self.entries_file, self.entries)
        self._save_json(self.projects_file, self.projects)
        
        print(f"✅ Logged {duration}h for '{project_name}' on {date_str}")
        return True
    
    def generate_report(self, period='week'):
        """Generate a time report for the specified period."""
        now = datetime.now()
        
        if period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        elif period == 'all':
            start_date = datetime.min
        else:
            print(f"❌ Invalid period: {period}. Use 'week', 'month', or 'all'.")
            return
        
        # Filter entries by date
        recent_entries = []
        for entry in self.entries:
            try:
                entry_date = datetime.strptime(entry['date'], '%Y-%m-%d')
                if entry_date >= start_date:
                    recent_entries.append(entry)
            except ValueError:
                continue
        
        # Group by project
        project_hours = defaultdict(float)
        for entry in recent_entries:
            project_hours[entry['project']] += entry['duration']
        
        # Get project details
        project_details = {}
        for project in self.projects:
            project_details[project['name']] = project
        
        print(f"\n📊 Time Report ({period}):")
        print("=" * 60)
        
        total_hours = sum(project_hours.values())
        if total_hours == 0:
            print("No time logged in this period.")
            return
        
        # Sort by hours (descending)
        sorted_projects = sorted(project_hours.items(), key=lambda x: x[1], reverse=True)
        
        for project_name, hours in sorted_projects:
            project = project_details.get(project_name, {})
            category = project.get('category', 'unknown')
            priority = project.get('priority', 3)
            estimated = project.get('estimated_hours_per_week', 0)
            
            # Calculate percentage
            percentage = (hours / total_hours) * 100
            
            # Create ASCII bar
            bar_length = 40
            filled = int((hours / max(project_hours.values())) * bar_length)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            print(f"\n{project_name} ({category})")
            print(f"  Priority: {priority}/5 | Estimated: {estimated}h/week")
            print(f"  Actual: {hours:.1f}h ({percentage:.1f}% of total)")
            print(f"  {bar}")
            
            # Check for alerts
            if estimated > 0:
                ratio = hours / estimated if period == 'week' else (hours / 4) / estimated
                if ratio > 1.5:
                    print(f"  ⚠️  OVER TIME: {ratio:.1f}x estimated")
                elif ratio < 0.5:
                    print(f"  ⚠️  UNDER TIME: {ratio:.1f}x estimated")
    
    def dashboard(self):
        """Show dashboard with priority vs time matrix."""
        print("\n🎯 Priority vs Time Dashboard")
        print("=" * 60)
        
        if not self.projects:
            print("No projects defined. Use 'add-project' first.")
            return
        
        # Calculate weekly hours for each project
        week_ago = datetime.now() - timedelta(days=7)
        project_weekly_hours = defaultdict(float)
        
        for entry in self.entries:
            try:
                entry_date = datetime.strptime(entry['date'], '%Y-%m-%d')
                if entry_date >= week_ago:
                    project_weekly_hours[entry['project']] += entry['duration']
            except ValueError:
                continue
        
        # Create matrix
        print("\nPriority (rows) vs Time Allocation (columns):")
        print("     Low Time    Balanced    High Time")
        print("     ---------   ---------   ---------")
        
        for priority in range(1, 6):
            row_projects = [p for p in self.projects if p['priority'] == priority]
            if not row_projects:
                continue
            
            # Calculate average time ratio
            time_ratios = []
            for project in row_projects:
                weekly_hours = project_weekly_hours.get(project['name'], 0)
                estimated = project.get('estimated_hours_per_week', 0)
                ratio = weekly_hours / estimated if estimated > 0 else 0
                time_ratios.append(ratio)
            
            avg_ratio = sum(time_ratios) / len(time_ratios) if time_ratios else 0
            
            # Determine column
            if avg_ratio == 0:
                column = "No Time   "
            elif avg_ratio < 0.5:
                column = "Low Time  "
            elif avg_ratio > 1.5:
                column = "High Time "
            else:
                column = "Balanced  "
            
            # Color coding
            if avg_ratio == 0:
                emoji = "❌"
            elif avg_ratio < 0.5:
                emoji = "🔴"
            elif avg_ratio > 1.5:
                emoji = "🟡"
            else:
                emoji = "🟢"
            
            print(f"P{priority} {emoji}   {column}")
        
        print("\n🟢 = Good balance | 🟡 = Too much time | 🔴 = Too little time | ❌ = No time")
        
        # Show top alerts
        print("\n🔔 Priority Alerts:")
        alerts = []
        
        for project in self.projects:
            weekly_hours = project_weekly_hours.get(project['name'], 0)
            estimated = project.get('estimated_hours_per_week', 0)
            
            if estimated > 0:
                ratio = weekly_hours / estimated
                if ratio == 0:
                    alerts.append((project['name'], "No time logged this week"))
                elif ratio < 0.3:
                    alerts.append((project['name'], f"Only {ratio:.1f}x estimated time"))
                elif ratio > 2.0:
                    alerts.append((project['name'], f"{ratio:.1f}x over estimated time"))
        
        if alerts:
            for project_name, message in alerts[:5]:  # Show top 5
                print(f"  • {project_name}: {message}")
            if len(alerts) > 5:
                print(f"  ... and {len(alerts) - 5} more alerts")
        else:
            print("  No major alerts")
    
    def export_markdown(self, output_file=None):
        """Export project data to markdown format."""
        if output_file is None:
            output_file = self.data_dir / "report.md"
        
        with open(output_file, 'w') as f:
            f.write("# Project Time Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            
            # Summary stats
            total_projects = len(self.projects)
            total_entries = len(self.entries)
            total_hours = sum(entry['duration'] for entry in self.entries)
            
            f.write("## Summary\n\n")
            f.write(f"- **Projects:** {total_projects}\n")
            f.write(f"- **Time Entries:** {total_entries}\n")
            f.write(f"- **Total Hours Tracked:** {total_hours:.1f}\n\n")
            
            # Projects by category
            f.write("## Projects by Category\n\n")
            categories = defaultdict(list)
            for project in self.projects:
                categories[project['category']].append(project)
            
            for category, projs in categories.items():
                f.write(f"### {category.title()}\n\n")
                for project in projs:
                    f.write(f"- **{project['name']}** (Priority: {project['priority']}/5)\n")
                    f.write(f"  - Estimated: {project['estimated_hours_per_week']}h/week\n")
                    f.write(f"  - Actual: {project['actual_hours_spent']:.1f}h total\n\n")
            
            # Recent entries
            f.write("## Recent Time Entries\n\n")
            recent_entries = sorted(self.entries, 
                                  key=lambda x: x.get('logged_at', ''), 
                                  reverse=True)[:10]
            
            for entry in recent_entries:
                f.write(f"- **{entry['project']}** on {entry['date']}\n")
                f.write(f"  - Duration: {entry['duration']}h\n")
                if entry['description']:
                    f.write(f"  - Description: {entry['description']}\n")
                f.write("\n")
        
        print(f"✅ Report exported to {output_file}")
    
    def demo_mode(self):
        """Load demo data for testing."""
        demo_projects = [
            {
                'name': 'Day Job - Feature X',
                'category': 'day-job',
                'priority': 5,
                'estimated_hours_per_week': 30.0,
                'actual_hours_spent': 25.0,
                'created_at': '2026-04-01T10:00:00'
            },
            {
                'name': 'Sports Analytics Platform',
                'category': 'side-business',
                'priority': 4,
                'estimated_hours_per_week': 15.0,
                'actual_hours_spent': 8.0,
                'created_at': '2026-04-01T10:00:00'
            },
            {
                'name': 'Coach CRM Improvements',
                'category': 'side-business',
                'priority': 3,
                'estimated_hours_per_week': 5.0,
                'actual_hours_spent': 2.5,
                'created_at': '2026-04-01T10:00:00'
            },
            {
                'name': 'Personal Learning',
                'category': 'personal',
                'priority': 2,
                'estimated_hours_per_week': 5.0,
                'actual_hours_spent': 1.0,
                'created_at': '2026-04-01T10:00:00'
            }
        ]
        
        demo_entries = [
            {
                'project': 'Day Job - Feature X',
                'date': '2026-04-07',
                'duration': 6.0,
                'description': 'Sprint planning and development',
                'logged_at': '2026-04-07T18:30:00'
            },
            {
                'project': 'Sports Analytics Platform',
                'date': '2026-04-07',
                'duration': 2.0,
                'description': 'API integration work',
                'logged_at': '2026-04-07T20:00:00'
            },
            {
                'project': 'Day Job - Feature X',
                'date': '2026-04-08',
                'duration': 7.5,
                'description': 'Code reviews and testing',
                'logged_at': '2026-04-08T17:00:00'
            },
            {
                'project': 'Coach CRM Improvements',
                'date': '2026-04-08',
                'duration': 1.5,
                'description': 'Added search functionality',
                'logged_at': '2026-04-08T19:00:00'
            }
        ]
        
        # Save demo data
        demo_dir = self.data_dir / "demo"
        demo_dir.mkdir(exist_ok=True)
        
        self.projects_file = demo_dir / "projects.json"
        self.entries_file = demo_dir / "entries.json"
        
        self.projects = demo_projects
        self.entries = demo_entries
        
        self._save_json(self.projects_file, demo_projects)
        self._save_json(self.entries_file, demo_entries)
        
        print("✅ Demo data loaded. Use --data-dir to point to demo directory.")
        print(f"   Demo directory: {demo_dir}")
        
        # Switch back to original data dir
        self.data_dir = demo_dir

def main():
    parser = argparse.ArgumentParser(
        description="Project Time Tracker & Prioritization Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add-project "Day Job" day-job 5 30
  %(prog)s log-time "Day Job" today 6 "Sprint planning"
  %(prog)s report --period week
  %(prog)s dashboard
  %(prog)s export --output weekly_report.md
  %(prog)s demo
        """
    )
    
    parser.add_argument(
        '--data-dir',
        help='Directory to store data files (default: ~/.config/project-tracker)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Add project command
    add_parser = subparsers.add_parser('add-project', help='Add a new project')
    add_parser.add_argument('name', help='Project name')
    add_parser.add_argument('category', choices=['day-job', 'side-business', 'personal'],
                          help='Project category')
    add_parser.add_argument('priority', type=int, choices=range(1, 6),
                          help='Priority (1-5, where 5 is highest)')
    add_parser.add_argument('estimated_hours', type=float,
                          help='Estimated hours per week')
    
    # Log time command
    log_parser = subparsers.add_parser('log-time', help='Log time for a project')
    log_parser.add_argument('project', help='Project name')
    log_parser.add_argument('date', help='Date (YYYY-MM-DD, today, or yesterday)')
    log_parser.add_argument('duration', type=float, help='Duration in hours')
    log_parser.add_argument('description', nargs='?', default='',
                          help='Description of work done')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate time report')
    report_parser.add_argument('--period', choices=['week', 'month', 'all'],
                             default='week', help='Time period for report')
    
    # Dashboard command
    subparsers.add_parser('dashboard', help='Show priority vs time dashboard')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export to markdown')
    export_parser.add_argument('--output', help='Output file path')
    
    # Demo command
    subparsers.add_parser('demo', help='Load demo data for testing')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    tracker = ProjectTracker(args.data_dir)
    
    if args.command == 'add-project':
        tracker.add_project(args.name, args.category, args.priority, args.estimated_hours)
    
    elif args.command == 'log-time':
        tracker.log_time(args.project, args.date, args.duration, args.description)
    
    elif args.command == 'report':
        tracker.generate_report(args.period)
    
    elif args.command == 'dashboard':
        tracker.dashboard()
    
    elif args.command == 'export':
        tracker.export_markdown(args.output)
    
    elif args.command == 'demo':
        tracker.demo_mode()
        print("\n🎮 Demo mode activated!")
        print("Try these commands:")
        print("  python project_tracker.py --data-dir ~/.config/project-tracker/demo report")
        print("  python project_tracker.py --data-dir ~/.config/project-tracker/demo dashboard")

if __name__ == '__main__':
    main()