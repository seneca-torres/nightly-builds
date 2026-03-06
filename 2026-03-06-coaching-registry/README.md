# Coaching Registry Database

A searchable database of football coaches beyond the big names. This prototype ingests coaching staff data from the CFBD API (via the existing CFBD staff fetcher) and stores it in a local SQLite database. Supports querying by position specialty, conference, school, and career stage.

## Features

- **Ingest**: Import coaching staff data from CFBD JSON or direct API calls
- **Store**: SQLite database with normalized tables (coaches, positions, schools, timeline)
- **Search**: CLI queries for coaches by position, school, conference, etc.
- **Export**: Results as markdown, CSV, or JSON

## Usage

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
python coaching_registry.py --db coaching_registry.db init

# Ingest demo data (no API required)
python coaching_registry.py --db coaching_registry.db ingest --demo

# Ingest real data from CFBD API for 2024 season (requires internet)
python coaching_registry.py --db coaching_registry.db ingest --season 2024

# Search for head coaches
python coaching_registry.py --db coaching_registry.db search --position "Head Coach"

# List all coaches at a school
python coaching_registry.py --db coaching_registry.db search --school "Alabama"

# Filter by year
python coaching_registry.py --db coaching_registry.db search --year 2023

# Combine filters
python coaching_registry.py --db coaching_registry.db search --school "Washington" --year 2023

# Output formats: text (default), CSV, JSON
python coaching_registry.py --db coaching_registry.db search --position "Offensive Coordinator" --output csv
python coaching_registry.py --db coaching_registry.db search --position "Defensive Coordinator" --output json
```

## Database Schema

See `schema.sql` for table definitions.

## Future Extensions

- Scrape LinkedIn and press releases for more detail
- Add notable players developed and scheme associations
- Web UI for browsing and filtering
- Integration with Obsidian for personal notes

## License

MIT