# README.md

## OPAD Play Tagging & Attribution

Small Python CLI for enriching an OPAD-style play database with:

- head coach
- offensive coordinator
- coaching tree attribution
- concepts
- key players

It supports two workflows:

1. Auto-detect staff from `team + date` using a small coaching staff lookup table.
2. Semi-manual tagging when you already know the coach, coordinator, concepts, or players.

This keeps the scope intentionally small so it can be extended later without needing a full database or web scraper.

## Files

- `opad_play_tagging.py`: CLI
- `data/staff.json`: date-bounded staff attribution data
- `data/plays.json`: example OPAD-style play records

## Data Model

### Play
Each play is a JSON object with:

- `play_id`
- `date`
- `team`
- `opponent`
- `description`
- `tags`

### Tags
The `tags` object can include:

- `head_coach`
- `offensive_coordinator`
- `coaching_tree`
- `concepts`
- `players`

### Staff
Each staff row includes:

- `team`
- `start_date`
- `end_date`
- `head_coach`
- `offensive_coordinator`
- `coaching_tree`

## Usage

### Detect staff from game context
```bash
python3 opad_play_tagging.py detect-staff --team LSU --date 2023-09-03
```

### Auto-tag a play using team + date
```bash
python3 opad_play_tagging.py tag opad-001 --auto-detect
```

### Semi-manual tagging
```bash
python3 opad_play_tagging.py tag opad-001 \
  --head-coach "Dan Casey" \
  --offensive-coordinator "Dan Casey" \
  --coaching-tree "Shanahan tree" \
  --concept RPO \
  --player "Quarterback Name"
```

### Search examples

Show all Dan Casey plays with RPO concepts:
```bash
python3 opad_play_tagging.py search --head-coach "Dan Casey" --concept RPO
```

Show every play from a Shanahan-tree coordinator:
```bash
python3 opad_play_tagging.py search --coaching-tree "Shanahan tree"
```

Filter by player:
```bash
python3 opad_play_tagging.py search --player "Tyreek Hill"
```

## How To Test

### 1. Smoke test the CLI help
```bash
python3 opad_play_tagging.py --help
python3 opad_play_tagging.py search --help
python3 opad_play_tagging.py tag --help
```

### 2. Verify staff detection
```bash
python3 opad_play_tagging.py detect-staff --team LSU --date 2023-09-03
```

Expected output should include:

- `Brian Kelly`
- `Mike Denbrock`

### 3. Auto-tag a sample play
```bash
python3 opad_play_tagging.py tag opad-001 --auto-detect
```

Then inspect `data/plays.json` and confirm `head_coach`, `offensive_coordinator`, and `coaching_tree` were added.

### 4. Query the enriched data
```bash
python3 opad_play_tagging.py search --concept RPO
python3 opad_play_tagging.py search --coaching-tree "Shanahan tree"
```

## Notes

- This version is intentionally local and file-based.
- There are no external dependencies.
- The coaching lookup is only as good as `data/staff.json`.
- If you want more precision later, the next step is adding richer date ranges, aliases, and importers for larger OPAD exports.
