# Project Time Tracker & Prioritization Dashboard

A CLI tool to help track time spent on different projects and visualize priorities. Built to help Victor manage context switching between day job, side business, and personal projects.

## 🎯 Why This Tool Helps

Victor frequently switches between multiple projects (day job, sports analytics business, personal learning). This tool helps:

1. **Track actual time spent** vs. estimated time per project
2. **Visualize priorities** with a clear dashboard showing what's getting attention vs. what's being neglected
3. **Generate reports** for weekly standups and reviews
4. **Surface alerts** when projects are getting too much or too little time relative to their priority

## 📦 Features

- **Project Management**: Add projects with categories, priorities (1-5), and weekly time estimates
- **Time Logging**: Quick log entries with dates and descriptions
- **Smart Reports**: Weekly/monthly time allocation with ASCII visualizations
- **Priority Dashboard**: Matrix view showing priority vs. actual time spent
- **Alerts**: Warns when projects are under/over their estimated time
- **Markdown Export**: Generate reports for inclusion in standups
- **Demo Mode**: Test with sample data without affecting real data
- **Zero Dependencies**: Pure Python standard library

## 🚀 Quick Start

### Installation
```bash
# Just download and run - no installation needed
python3 project_tracker.py --help
```

### Basic Usage

1. **Add a project**:
   ```bash
   python3 project_tracker.py add-project "Day Job Feature" day-job 5 30
   ```

2. **Log time**:
   ```bash
   python3 project_tracker.py log-time "Day Job Feature" today 6 "Sprint planning"
   ```

3. **View weekly report**:
   ```bash
   python3 project_tracker.py report --period week
   ```

4. **See dashboard**:
   ```bash
   python3 project_tracker.py dashboard
   ```

5. **Export to markdown**:
   ```bash
   python3 project_tracker.py export --output weekly_report.md
   ```

### Try Demo Mode
```bash
python3 project_tracker.py demo
python3 project_tracker.py --data-dir ~/.config/project-tracker/demo dashboard
```

## 📊 Data Storage

Data is stored in JSON format in `~/.config/project-tracker/`:
- `projects.json`: Project definitions and cumulative hours
- `entries.json`: Individual time entries
- `report.md`: Generated markdown reports

## 🔧 Command Reference

### `add-project`
Add a new project to track.
```bash
python3 project_tracker.py add-project <name> <category> <priority> <estimated_hours>
```
- **Categories**: `day-job`, `side-business`, `personal`
- **Priority**: 1-5 (5 = highest)
- **Estimated hours**: Hours per week

### `log-time`
Log time spent on a project.
```bash
python3 project_tracker.py log-time <project> <date> <duration> [description]
```
- **Date**: `YYYY-MM-DD`, `today`, or `yesterday`
- **Duration**: Hours (decimal OK: `1.5` = 1.5 hours)

### `report`
Generate time allocation report.
```bash
python3 project_tracker.py report [--period week|month|all]
```

### `dashboard`
Show priority vs. time matrix with alerts.
```bash
python3 project_tracker.py dashboard
```

### `export`
Export project data to markdown.
```bash
python3 project_tracker.py export [--output path/to/file.md]
```

### `demo`
Load sample data for testing.
```bash
python3 project_tracker.py demo
```

## 🎨 Sample Output

### Weekly Report
```
📊 Time Report (week):
============================================================

Day Job - Feature X (day-job)
  Priority: 5/5 | Estimated: 30h/week
  Actual: 13.5h (54.0% of total)
  ███████████████████████░░░░░░░░░░░░░░░░░░░

Sports Analytics Platform (side-business)
  Priority: 4/5 | Estimated: 15h/week
  Actual: 2.0h (8.0% of total)
  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  ⚠️  UNDER TIME: 0.1x estimated
```

### Priority Dashboard
```
🎯 Priority vs Time Dashboard
============================================================

Priority (rows) vs Time Allocation (columns):
     Low Time    Balanced    High Time
     ---------   ---------   ---------
P5 🟢   Balanced  
P4 🔴   Low Time  
P3 ❌   No Time   
P2 ❌   No Time   
P1 ❌   No Time   

🟢 = Good balance | 🟡 = Too much time | 🔴 = Too little time | ❌ = No time

🔔 Priority Alerts:
  • Sports Analytics Platform: Only 0.1x estimated time
  • Coach CRM Improvements: No time logged this week
```

## 🧩 Integration with Victor's Workflow

### Morning Standups
Add to daily standup script to include time allocation:
```bash
# In morning briefing script
python3 project_tracker.py report --period week >> daily_standup.md
```

### Weekly Reviews
Export markdown for weekly retrospectives:
```bash
python3 project_tracker.py export --output ~/clawd/memory/weekly/time_report_$(date +%Y-%m-%d).md
```

### Project Context Switching
Before starting work on a project:
```bash
# Quick check: what needs attention?
python3 project_tracker.py dashboard | grep -A2 "🔴\|❌"
```

## 📈 How It Addresses Victor's Pain Points

| Pain Point | Solution |
|------------|----------|
| Context switching fatigue | Clear visual dashboard shows what needs attention |
| Losing track of time allocation | Automated tracking with alerts |
| Hard to prioritize across projects | Priority matrix surfaces misalignments |
| Manual reporting for standups | One-command markdown export |
| Forgetting side projects | Alerts when projects get no time |

## 🔍 Verification

Run the verification script:
```bash
python3 verify.py
```

Or test manually:
```bash
# Test basic functionality
python3 project_tracker.py demo
python3 project_tracker.py --data-dir ~/.config/project-tracker/demo report
python3 project_tracker.py --data-dir ~/.config/project-tracker/demo dashboard
python3 project_tracker.py --data-dir ~/.config/project-tracker/demo export --output test_report.md
```

## 🤝 Contributing

This is part of Victor's nightly builds series. To extend:

1. Add new visualization types
2. Integrate with calendar data
3. Add Slack/Telegram notifications for alerts
4. Create web dashboard version

## 📁 Files

- `project_tracker.py` - Main CLI tool
- `README.md` - This documentation
- `verify.py` - Verification script
- `demo/` - Sample data for testing

---

Built with 🦉 by Seneca for Victor's context-switching workflow. Part of the Nightly Builds series.