# Canvas Auto-Updater

A Python script that automatically updates the Nightly Builds dashboard (`~/clawd/canvas/index.html`) based on the contents of `~/clawd/NIGHTLY-BUILDS.md`.

## Features

- Parses completed builds from NIGHTLY-BUILDS.md
- Updates the "Latest Build" section with the most recent build
- Rebuilds the completed builds list in reverse chronological order
- Updates statistics (completed count, ideas count)
- Safe backup and dry-run mode
- Zero external dependencies (standard library only)

## Usage

```bash
python canvas_updater.py [--dry-run] [--output path] [--help]
```

- `--dry-run`: Print changes without modifying the HTML file
- `--output`: Write updated HTML to a custom path (default: same file)
- `--help`: Show help message

## How It Works

1. Reads `~/clawd/NIGHTLY-BUILDS.md` and extracts completed builds using regex.
2. Sorts builds by date (newest first).
3. Reads `~/clawd/canvas/index.html` and replaces:
   - The `#last-build` div with the latest build
   - The `#completed-list` div with fresh build cards
   - The stats counters (`#completed-count`, `#ideas-count`, etc.)
4. Creates a backup of the original HTML file (`.backup`).
5. Writes the updated HTML.

## Testing

Run the script with `--dry-run` to see what would be changed:

```bash
cd ~/clawd/nightly-builds/2026-02-24-canvas-auto-updater
python canvas_updater.py --dry-run
```

If the output looks correct, run without `--dry-run` to update the canvas.

## Integration

After each nightly build, run this script to keep the dashboard up to date.

## Notes

- The script assumes the HTML structure of `index.html` remains consistent.
- Build titles may contain emojis; they are preserved.
- PR links are optional; missing links are omitted.
- The "ideas count" is derived from the "Victor's Half-Baked Ideas" section.

## License

MIT