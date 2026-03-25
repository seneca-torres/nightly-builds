# Memory Cleanup CLI 🧠

A Python CLI tool for maintaining and organizing the memory system in `~/clawd/memory/`. This tool helps keep memory files clean, deduplicated, and well-organized.

## Features

- **📊 Statistics**: Get insights into memory usage (total files, entries, activity patterns)
- **🧹 Deduplication**: Remove repetitive entries (cron logs, duplicate decisions)
- **🔧 Formatting fixes**: Fix common issues like empty Summary sections, malformed timestamps
- **🗄️ Archiving**: Move old files to archive directory (configurable age threshold)
- **⚠️ Dry-run mode**: Preview changes before applying them
- **📈 Activity analysis**: See when most entries are logged (24h heatmap)

## Installation

No installation required! This is a standalone Python script with zero external dependencies.

```bash
# Make executable
chmod +x memory_cleanup.py

# Or run directly with Python
python3 memory_cleanup.py --help
```

## Usage

### Basic Usage

```bash
# Show statistics
python3 memory_cleanup.py --stats

# Dry-run: see what would be changed
python3 memory_cleanup.py --dry-run --dedupe --fix-formatting

# Apply changes (deduplicate + fix formatting)
python3 memory_cleanup.py --dedupe --fix-formatting

# Archive files older than 30 days
python3 memory_cleanup.py --archive

# Verbose output with all operations
python3 memory_cleanup.py --stats --dedupe --fix-formatting --verbose
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dry-run` | Show what would be changed without making changes | `False` |
| `--verbose` | Show detailed output | `False` |
| `--archive` | Archive files older than `--max-age` days | `False` |
| `--stats` | Show memory usage statistics | `False` |
| `--dedupe` | Deduplicate repetitive entries | `True` |
| `--fix-formatting` | Fix common formatting issues | `True` |
| `--max-age` | Maximum age in days for archiving | `30` |

## What It Fixes

### 1. Deduplication
Removes duplicate entries that match common repetitive patterns:
- ✅ Cron task completions
- 📋 Decision logs (especially empty queue decisions)
- 🔀 PR references
- 💡 Suggestions
- 🚨 Alerts

### 2. Formatting Issues
- **Empty Summary sections**: Adds `*(no entries yet)*` placeholder
- **Malformed timestamps**: Fixes timestamps missing brackets (e.g., `12:00 Meeting` → `[12:00] Meeting`)

### 3. Archiving
Moves files older than 30 days (configurable) to `~/clawd/memory/archive/daily/`

## Example Output

### Statistics Mode
```
🧠 Memory Cleanup CLI
Scanning /Users/vicmacmini/clawd/memory/daily...
Found 45 memory file(s)

============================================================
MEMORY STATISTICS
============================================================

📊 Overview:
  Total files: 45
  Total lines: 1,234
  Total entries: 567
  Total words: ~12,345
  Date range: 2025-01-31 to 2026-03-25 (420 days)
  Avg entries/day: 1.4
  Avg lines/day: 2.9

📝 Summary Sections:
  Files with empty Summary: 3
  Files without Summary: 2

📅 Files by Month:
  2025-01: 1 file
  2025-06: 1 file
  2026-01: 12 files
  2026-02: 15 files
  2026-03: 16 files

⏰ Activity by Hour (24h):
  00:00 ████████████ 120
  01:00 ████ 45
  02:00 ███████ 78
  ... (more hours)
  23:00 █ 12

============================================================
✅ Done!
```

### Cleanup Mode (with --verbose)
```
🧠 Memory Cleanup CLI
Scanning /Users/vicmacmini/clawd/memory/daily...
Found 45 memory file(s)

🔧 Processing files...

Processing 2026-03-25.md:
  Removing duplicate: [00:03] ✅ outcome for this cron run...
  Removing duplicate: [00:04] 📋 Decision: queue is empty...
  Fixing empty Summary section at line 3
  Would save changes to 2026-03-25.md

Processing 2026-03-24.md:
  Fixing malformed timestamp: 12:00 Meeting with client...
  Would save changes to 2026-03-24.md

📝 Summary:
  Duplicates removed: 15
  Formatting issues fixed: 8

⚠️ DRY RUN: No changes were saved. Use without --dry-run to apply.

✅ Done!
```

## Verification

Run the verification script to test the tool:

```bash
python3 verify_memory_cleanup.py
```

The verification script creates a test memory structure and runs all major features:
- Dry-run mode
- Actual deduplication and formatting fixes
- Statistics generation
- Archive functionality
- Help output

## How It Works

1. **File Scanning**: Recursively scans `~/clawd/memory/daily/` for `.md` files
2. **Pattern Matching**: Uses regex patterns to identify repetitive entries
3. **Content Analysis**: Parses timestamps, counts entries, checks formatting
4. **Safe Operations**: All destructive operations (deduplication, archiving) require explicit flags
5. **Dry-run First**: Always test with `--dry-run` before applying changes

## Integration with Daily Workflow

Add to your nightly build or weekly maintenance routine:

```bash
# Weekly memory cleanup (every Sunday)
python3 memory_cleanup.py --stats --dedupe --fix-formatting

# Monthly archiving (first of the month)
python3 memory_cleanup.py --archive --max-age 30
```

## Customization

### Adding Deduplication Patterns

Edit the `REPETITIVE_PATTERNS` list in `memory_cleanup.py`:

```python
REPETITIVE_PATTERNS = [
    r"^\[\d{2}:\d{2}\] ✅ (?:outcome for this cron run|action for this cron execution)",
    # Add your own patterns here
    r"^\[\d{2}:\d{2}\] 🔄 .*",  # Example: rotation logs
]
```

### Changing Archive Threshold

```bash
# Archive files older than 60 days
python3 memory_cleanup.py --archive --max-age 60
```

## Safety Features

- **Dry-run mode**: Preview all changes before applying
- **Backup-free but safe**: Original files are modified in-place, but changes are minimal and focused
- **Confirmation prompts**: Archive operations could prompt in future versions
- **Error handling**: Graceful handling of file permission issues, malformed content

## Requirements

- Python 3.7+
- No external dependencies (standard library only)
- Read/write access to `~/clawd/memory/`

## License

Part of the Nightly Builds collection. Use freely within the OpenClaw ecosystem.

---

**Built**: 2026-03-25  
**Purpose**: Keep the memory system clean and maintainable  
**Nightly Build ID**: Memory Cleanup CLI