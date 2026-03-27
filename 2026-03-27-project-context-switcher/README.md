# Project Context Switcher CLI

A lightweight Python CLI for quickly switching between project contexts. This tool helps Victor manage his multiple projects by providing quick context switching with environment variables, directory changes, and command execution.

## Features

- **Project Management**: Store project configurations in YAML
- **Quick Activation**: Switch between projects with a single command
- **Environment Variables**: Set project-specific environment variables
- **Command Execution**: Run commands in the project context
- **File Opening**: Open project files or directories
- **Persistent State**: Remember active context across sessions

## Installation

```bash
# Make the script executable
chmod +x context_switcher.py

# Optional: Create a symlink for easy access
ln -sf "$PWD/context_switcher.py" /usr/local/bin/pctx
```

## Configuration

Create a configuration file at `~/.project_contexts.yaml`:

```yaml
projects:
  coach-db:
    description: "Coach Database API and frontend"
    root: "~/clawd/coach-database"
    env:
      DB_URL: "postgresql://localhost:5432/coachdb"
      APP_ENV: "development"
    files:
      - "README.md"
      - "package.json"
    commands:
      - "git status"
      - "docker-compose ps"

  nightly-builds:
    description: "Nightly builds repository"
    root: "~/clawd/nightly-builds"
    env:
      NIGHTLY_DIR: "~/clawd/nightly-builds"
    files:
      - "NIGHTLY-BUILDS.md"

  portfolio:
    description: "VT Sports Solutions portfolio site"
    root: "~/clawd/portfolio"
    env:
      NODE_ENV: "development"
    files:
      - "index.html"
    commands:
      - "open index.html"
```

## Usage

### List available projects
```bash
python3 context_switcher.py list
```

### Activate a project
```bash
python3 context_switcher.py activate coach-db
```

### Show current status
```bash
python3 context_switcher.py status
```

### Run a command in active project context
```bash
python3 context_switcher.py run "ls -la"
```

### Open project files
```bash
python3 context_switcher.py open
```

### Deactivate current project
```bash
python3 context_switcher.py deactivate
```

### Add a new project
```bash
python3 context_switcher.py add
```

## Example Workflow

```bash
# Switch to coach-db project
pctx activate coach-db

# Check status
pctx status

# Run commands in project context
pctx run "docker-compose up -d"
pctx run "npm start"

# Open project files
pctx open

# Switch to another project
pctx activate nightly-builds

# Deactivate when done
pctx deactivate
```

## Verification

Run the verification script to test basic functionality:

```bash
python3 verify.py
```

## Dependencies

- Python 3.9+
- PyYAML (for YAML parsing)
- No other external dependencies

## Why This Tool Helps

Victor works on multiple projects and frequently switches contexts. This tool:

1. **Reduces cognitive load** by providing a consistent way to switch projects
2. **Automates setup** by setting environment variables and running initialization commands
3. **Saves time** by avoiding manual directory navigation and setup
4. **Improves workflow** with a simple, memorable CLI interface

## Integration with Existing Tools

- Works with VS Code (`code .` to open project)
- Compatible with tmux sessions
- Integrates with git, docker, and other development tools
- Can be extended with custom commands