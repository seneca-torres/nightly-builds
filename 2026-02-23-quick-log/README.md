# Quick Log

A small command-line helper to append timestamped notes to a daily Markdown log.

## Installation

1. Ensure Python 3 is available.
2. Make the script executable (optional):

```sh
chmod +x quicklog.py
```

## Usage

```sh
# Append a quick event note (default category)
./quicklog.py "Wrapped up sprint demo"

# Append an idea note
./quicklog.py -c idea "Try a weekly retrospective checklist"

# Append a todo note
./quicklog.py -c todo "Follow up with design about error states"

# Read a multi-line note from stdin
cat <<'EOF' | ./quicklog.py -c event
Met with vendor
Agreed on next steps
EOF

# List the last 5 bullet entries from today's file
./quicklog.py --list
```

## Default log location

By default, notes are written to:

```
~/clawd/memory/daily/YYYY-MM-DD.md
```

You can override with `--path`:

```sh
./quicklog.py --path ~/notes/daily/2026-02-23.md "Custom location"
```
