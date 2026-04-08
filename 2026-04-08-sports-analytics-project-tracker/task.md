# Task: Build Sports Analytics Project Tracker

## Project Goal
Help Victor manage and quickly context-switch between multiple sports analytics projects (OPAD, Coach DB, broadcaster notes, client bots, etc.). Show project status, next actions, blockers, and last updated.

## Requirements

### 1. CLI Tool (Python)
- `sports-project-tracker.py` with commands:
  - `list`: Show all projects in table format
  - `status`: Show detailed status with next actions and blockers
  - `update <project> --status <status> --next-action <action> --blocker <blocker>`: Update a project
  - `add <name> --description <desc>`: Add new project
  - `web`: Launch the web dashboard
  
- Data storage: JSON file at `~/clawd/sports-projects/projects.json`
- Each project has:
  - name (string)
  - description (string)
  - status: 'active', 'blocked', 'paused', 'planning', 'completed'
  - next_action (string)
  - blocker (string, optional)
  - last_updated (ISO timestamp)
  - category: 'data', 'infra', 'client', 'tooling', 'research'
  - repo_path (optional)
  - priority: 1-5 (1=highest)

### 2. Web Dashboard (HTML/CSS/JS)
- `dashboard.html` with dark theme (match portfolio style)
- Visual cards for each project with color-coded status
- Filter by status/category
- Search box
- Click to expand details
- Auto-refresh every 30 seconds
- Display in a clean, scannable grid

### 3. Initial Data
Seed with Victor's actual sports analytics projects:
1. One Play a Day (OPAD) - active, category: data, priority: 1
2. Coach Database - blocked (needs PFF wrapper), category: infra, priority: 2  
3. Broadcaster Notes Intelligence System - active, category: research, priority: 2
4. Client-facing bot framework - completed, category: client, priority: 3
5. Rental Finder - active, category: tooling, priority: 4
6. CFBD Staff Fetcher - completed, category: data, priority: 4
7. GitHub Projects Sync - completed, category: tooling, priority: 5

### 4. Features
- Zero external dependencies (standard library only)
- Demo mode that works without real data
- Verification script to test all features
- README.md with setup and usage instructions

## Implementation Notes
- Use Python's `argparse` for CLI
- Use `json` module for storage
- Web dashboard uses vanilla JavaScript
- Match Victor's dark theme aesthetic
- All code in this directory

When done, commit all changes, push to a new branch, and open a PR against main.