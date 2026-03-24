# Tool Catalog CLI

A Python CLI tool that scans the `~/clawd/nightly-builds` directory and creates a searchable catalog of all tools built during nightly builds.

## Purpose

As the number of nightly builds grows, it becomes hard to remember what tools exist and how to use them. This tool helps discover, search, and reference the growing collection of utilities.

## Features

- **Scan**: Automatically scan the nightly-builds directory for tools
- **List**: View all tools with dates and descriptions
- **Search**: Find tools by name, description, or directory
- **Info**: Get detailed information about a specific tool
- **Usage**: Show usage examples for a tool
- **Generate Markdown**: Create a reference table in Markdown format

## Installation & Setup

No installation required - just run the Python script:

```bash
cd ~/clawd/nightly-builds/2026-03-24-tool-catalog
python3 tool-catalog.py --help
```

## Usage

### First: Scan for tools
```bash
python3 tool-catalog.py scan
```
This scans the `~/clawd/nightly-builds` directory and saves a catalog to `tool_catalog.json`.

### List all tools
```bash
python3 tool-catalog.py list
python3 tool-catalog.py list --verbose  # More detailed view
```

### Search for tools
```bash
python3 tool-catalog.py search "calendar"
python3 tool-catalog.py search "github"
python3 tool-catalog.py search "coach"
```

### Get detailed info about a tool
```bash
python3 tool-catalog.py info "calendar-quickadd"
python3 tool-catalog.py info "2026-03-02-calendar-quickadd"  # By ID
```

### Show usage examples
```bash
python3 tool-catalog.py usage "calendar-quickadd"
```

### Generate a markdown reference table
```bash
python3 tool-catalog.py generate-markdown > catalog.md
```

### Update the catalog
```bash
python3 tool-catalog.py update
```

## Example Output

```
$ python3 tool-catalog.py list
  1. 2026-03-23 - Coach Relationship Visualizer
  2. 2026-03-22 - Morning Briefing Aggregator
  3. 2026-03-21 - Rental Alert Diff Detection
  4. 2026-03-20 - Portfolio Dark Light Mode Toggle
  5. 2026-03-19 - Github Daily PR Digest
  ... (40+ more tools)
```

```
$ python3 tool-catalog.py search "calendar"
Found 4 tools matching 'calendar':
  1. 2026-03-18 - Calendar Duration Analyzer (calendar-duration-analyzer)
  2. 2026-03-13 - Calendar Free Slots Finder (calendar-free-slots-finder)
  3. 2026-03-12 - Calendar Conflict Detector (calendar-conflict-detector)
  4. 2026-03-02 - Calendar Quick Add CLI (calendar-quickadd)
```

## How It Works

1. **Directory Scanning**: Looks for date-patterned directories (`YYYY-MM-DD`) in nightly-builds
2. **Metadata Extraction**: Reads README.md files and Python files to extract descriptions and usage
3. **Catalog Storage**: Saves metadata to `tool_catalog.json` for fast access
4. **Search & Discovery**: Provides multiple ways to find and learn about tools

## Verification

Run the verification script to ensure the tool works correctly:

```bash
python3 verify.py
```

## Future Enhancements

Potential improvements:
- Integration with `~/clawd/scripts` directory
- Rating/feedback system for tool usefulness
- Automatic categorization (CLI tools, web apps, utilities)
- Usage statistics tracking
- Integration with TOOLS_REGISTRY.md

## Why This Tool?

As noted in AGENTS.md: "DRY Rule — No Duplicate Projects or Tools. Victor is resource-constrained. Before building anything new, check TOOLS_REGISTRY.md — does this already exist?"

This tool helps enforce that rule by making existing tools discoverable before building new ones.