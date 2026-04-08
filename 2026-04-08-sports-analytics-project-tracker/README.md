# Sports Analytics Project Tracker

A CLI tool and web dashboard to help Victor manage and quickly context-switch between multiple sports analytics projects (OPAD, Coach DB, broadcaster notes, client bots, etc.). Shows project status, next actions, blockers, and last updated.

## Features

### CLI Tool
- `list`: Show all projects in table format
- `status`: Show detailed status with next actions and blockers
- `update <project>`: Update a project's status, next action, or blocker
- `add <name>`: Add new project
- `web`: Launch the web dashboard

### Web Dashboard
- Dark theme (matches portfolio style)
- Visual cards for each project with color-coded status
- Filter by status/category
- Search box
- Click to expand details
- Auto-refresh every 30 seconds

## Installation

No installation required - just run the Python script:

```bash
cd ~/clawd/nightly-builds/2026-04-08-sports-analytics-project-tracker
python3 sports-project-tracker.py --help
```

## Usage

### List all projects
```bash
python3 sports-project-tracker.py list
```

### Show detailed status
```bash
python3 sports-project-tracker.py status
```

### Update a project
```bash
python3 sports-project-tracker.py update "One Play a Day" --status active --next-action "Add more plays" --blocker "Need PFF API access"
```

### Add a new project
```bash
python3 sports-project-tracker.py add "New Project" --description "Description here" --category data --priority 3
```

### Launch web dashboard
```bash
python3 sports-project-tracker.py web
```

## Data Storage

Projects are stored in JSON format at: `~/clawd/sports-projects/projects.json`

Each project has:
- `name` (string)
- `description` (string)
- `status`: 'active', 'blocked', 'paused', 'planning', 'completed'
- `next_action` (string)
- `blocker` (string, optional)
- `last_updated` (ISO timestamp)
- `category`: 'data', 'infra', 'client', 'tooling', 'research'
- `repo_path` (optional)
- `priority`: 1-5 (1=highest)

## Initial Data

The tracker comes pre-seeded with Victor's actual sports analytics projects:
1. One Play a Day (OPAD) - active, category: data, priority: 1
2. Coach Database - blocked (needs PFF wrapper), category: infra, priority: 2
3. Broadcaster Notes Intelligence System - active, category: research, priority: 2
4. Client-facing bot framework - completed, category: client, priority: 3
5. Rental Finder - active, category: tooling, priority: 4
6. CFBD Staff Fetcher - completed, category: data, priority: 4
7. GitHub Projects Sync - completed, category: tooling, priority: 5

## License

MIT