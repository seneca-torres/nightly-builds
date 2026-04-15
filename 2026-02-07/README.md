# Memory Search UI (Static)

A simple standalone HTML page that searches through markdown content provided by a JSON index.

## Files

- `index.html`: Search UI (single file, embedded CSS/JS).
- `generate_index.py`: Builds `memory_index.json` from `~/clawd/memory/**/*.md`.
- `memory_index.json`: Generated at runtime (not committed by default).

## Quick start (demo)

1. Start a local static server in this folder:

   - `python3 -m http.server 8000`

2. Open:

   - `http://localhost:8000/index.html`

If `memory_index.json` is not present (or can’t be fetched), the page falls back to embedded demo data.

## Generate an index from real markdown files

Generate `memory_index.json` (default scans `~/clawd/memory`):

- `python3 generate_index.py`

Custom root + output:

- `python3 generate_index.py --root ~/clawd/memory --output memory_index.json`

Print to stdout:

- `python3 generate_index.py --output -`

Then refresh `index.html`. It will load `memory_index.json` from the same directory.

## Notes / limitations

- This is a substring (case-insensitive) search, intended as a lightweight UI.
- You must serve over HTTP for `fetch()` to work reliably; `file://` often blocks JSON loading due to browser security rules.

