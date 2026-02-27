# StatBroadcast Teamstats Parser

Parse the StatBroadcast teamstats HTML view embedded in cached game JSON and emit cleaned JSON.

## Requirements

- Python 3.9+
- `beautifulsoup4`

Install dependencies:

```bash
python3 -m pip install beautifulsoup4
```

## Usage

Parse the default cached game JSON and print to stdout:

```bash
python3 statbroadcast_teamstats_parser.py
```

Parse a specific cached game JSON and write to a file:

```bash
python3 statbroadcast_teamstats_parser.py /path/to/game.json -o /tmp/teamstats.json
```

## Output format

The script outputs JSON with the following top-level keys:

- `team_stats`
- `game_comparison`
- `offensive_efficiency`
- `special_teams`
- `defensive_comparison`

Each value is an array of objects representing table rows. Headers are derived from HTML table headers when available, otherwise fallback keys like `col_1`, `col_2`, etc. Missing sections are returned as empty arrays.
