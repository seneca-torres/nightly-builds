#!/usr/bin/env python3
"""
Coaching Registry Database CLI.
Ingests CFBD coaching data into SQLite and enables search.
"""
import argparse
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests

# Default database path
DEFAULT_DB = "coaching_registry.db"

# CFBD API base
API_BASE = "https://api.collegefootballdata.com"
COACHES_ENDPOINT = "/coaches"

# Demo data matching CFBD structure (same as cfbd_staff.py)
DEMO_DATA = [
    {
        "first_name": "Kalen",
        "last_name": "DeBoer",
        "hire_date": "2024-01-12",
        "position": "Head Coach",
        "seasons": [
            {
                "school": "Washington",
                "year": 2023,
                "games": 15,
                "wins": 14,
                "losses": 1,
                "ties": 0,
                "preseason_rank": 10,
                "postseason_rank": 2,
            },
            {
                "school": "Alabama",
                "year": 2024,
                "games": 13,
                "wins": 10,
                "losses": 3,
                "ties": 0,
                "preseason_rank": 3,
                "postseason_rank": 8,
            },
        ],
    },
    {
        "first_name": "Ryan",
        "last_name": "Grubb",
        "hire_date": "2024-01-19",
        "position": "Offensive Coordinator",
        "seasons": [
            {
                "school": "Washington",
                "year": 2023,
                "games": 15,
                "wins": 14,
                "losses": 1,
                "ties": 0,
                "preseason_rank": 10,
                "postseason_rank": 2,
            },
            {
                "school": "Alabama",
                "year": 2024,
                "games": 13,
                "wins": 10,
                "losses": 3,
                "ties": 0,
                "preseason_rank": 3,
                "postseason_rank": 8,
            },
        ],
    },
    {
        "first_name": "Kane",
        "last_name": "Wommack",
        "hire_date": "2024-02-01",
        "position": "Defensive Coordinator",
        "seasons": [
            {
                "school": "South Alabama",
                "year": 2023,
                "games": 12,
                "wins": 7,
                "losses": 5,
                "ties": 0,
                "preseason_rank": None,
                "postseason_rank": None,
            },
            {
                "school": "Alabama",
                "year": 2024,
                "games": 13,
                "wins": 10,
                "losses": 3,
                "ties": 0,
                "preseason_rank": 3,
                "postseason_rank": 8,
            },
        ],
    },
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def init_db(db_path: str) -> None:
    """Create tables using schema.sql."""
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        logger.error("schema.sql not found")
        sys.exit(1)
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
    logger.info(f"Database initialized at {db_path}")


def fetch_coaching_data(season: int, team: Optional[str] = None, demo: bool = False) -> List[Dict]:
    """Fetch coaching data from CFBD API or demo."""
    if demo:
        logger.info("Using demo data")
        return DEMO_DATA
    params = {"year": season}
    if team:
        params["team"] = team
    url = API_BASE + COACHES_ENDPOINT
    try:
        logger.info(f"Fetching from {url} with params {params}")
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        sys.exit(1)


def ingest_season(db_path: str, season: int, team: Optional[str] = None, demo: bool = False) -> None:
    """Ingest coaching data for a season."""
    data = fetch_coaching_data(season, team, demo)
    logger.info(f"Ingesting {len(data)} coaches")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for coach in data:
            # Insert or replace coach, get id
            full_name = f"{coach['first_name']} {coach['last_name']}"
            cursor.execute(
                "INSERT OR REPLACE INTO coaches (first_name, last_name, full_name, hire_date) VALUES (?, ?, ?, ?)",
                (coach["first_name"], coach["last_name"], full_name, coach.get("hire_date"))
            )
            # Fetch the coach id (lastrowid may not be reliable with REPLACE)
            cursor.execute("SELECT id FROM coaches WHERE first_name = ? AND last_name = ?",
                           (coach["first_name"], coach["last_name"]))
            coach_id = cursor.fetchone()[0]
            # Insert position if present
            position = coach.get("position")
            position_id = None
            if position:
                cursor.execute("INSERT OR IGNORE INTO positions (title) VALUES (?)", (position,))
                cursor.execute("SELECT id FROM positions WHERE title = ?", (position,))
                position_id = cursor.fetchone()[0]
            # Process each season
            for season_entry in coach.get("seasons", []):
                school = season_entry["school"]
                cursor.execute("INSERT OR IGNORE INTO schools (name) VALUES (?)", (school,))
                cursor.execute("SELECT id FROM schools WHERE name = ?", (school,))
                school_id = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT OR REPLACE INTO coach_seasons
                    (coach_id, school_id, year, position_id, games, wins, losses, ties, preseason_rank, postseason_rank)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    coach_id, school_id, season_entry["year"], position_id,
                    season_entry.get("games"), season_entry.get("wins"), season_entry.get("losses"),
                    season_entry.get("ties"), season_entry.get("preseason_rank"),
                    season_entry.get("postseason_rank")
                ))
        conn.commit()
    logger.info("Ingestion complete")


def search_coaches(db_path: str, filters: Dict) -> List[Dict]:
    """Search coaches based on filters."""
    conditions = []
    params = []
    if filters.get("position"):
        conditions.append("p.title = ?")
        params.append(filters["position"])
    if filters.get("school"):
        conditions.append("s.name = ?")
        params.append(filters["school"])
    if filters.get("year"):
        conditions.append("cs.year = ?")
        params.append(filters["year"])
    # conference not yet implemented (needs conference table populated)
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    query = f"""
        SELECT c.full_name, p.title, s.name, cs.year,
               cs.games, cs.wins, cs.losses, cs.ties,
               cs.preseason_rank, cs.postseason_rank
        FROM coach_seasons cs
        JOIN coaches c ON cs.coach_id = c.id
        JOIN schools s ON cs.school_id = s.id
        LEFT JOIN positions p ON cs.position_id = p.id
        WHERE {where_clause}
        ORDER BY c.full_name, cs.year
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def main():
    parser = argparse.ArgumentParser(description="Coaching Registry Database CLI")
    parser.add_argument("--db", default=DEFAULT_DB, help="Database file path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    parser_init = subparsers.add_parser("init", help="Initialize database tables")

    # ingest
    parser_ingest = subparsers.add_parser("ingest", help="Ingest coaching data")
    parser_ingest.add_argument("--season", type=int, default=2024, help="Season year")
    parser_ingest.add_argument("--team", help="Team filter")
    parser_ingest.add_argument("--demo", action="store_true", help="Use demo data")

    # search
    parser_search = subparsers.add_parser("search", help="Search coaches")
    parser_search.add_argument("--position", help="Position filter")
    parser_search.add_argument("--school", help="School filter")
    parser_search.add_argument("--conference", help="Conference filter (not yet implemented)")
    parser_search.add_argument("--year", type=int, help="Season year filter")
    parser_search.add_argument("--output", choices=["text", "csv", "json"], default="text", help="Output format")

    args = parser.parse_args()

    if args.command == "init":
        init_db(args.db)
    elif args.command == "ingest":
        ingest_season(args.db, args.season, args.team, args.demo)
    elif args.command == "search":
        filters = {
            "position": args.position,
            "school": args.school,
            "year": args.year,
        }
        results = search_coaches(args.db, filters)
        if args.output == "text":
            if not results:
                print("No matches found.")
                return
            # Simple tabular output
            headers = ["Coach", "Position", "School", "Year", "W-L", "Preseason", "Postseason"]
            rows = []
            for r in results:
                wl = f"{r['wins']}-{r['losses']}" if r['wins'] is not None and r['losses'] is not None else "N/A"
                rows.append([
                    r["full_name"],
                    r["title"] or "N/A",
                    r["name"],
                    r["year"],
                    wl,
                    r["preseason_rank"] or "",
                    r["postseason_rank"] or "",
                ])
            # Determine column widths
            col_widths = [max(len(str(val)) for val in col) for col in zip(headers, *rows)]
            # Print header
            header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
            print(header_line)
            print("-" * len(header_line))
            for row in rows:
                print(" | ".join(str(val).ljust(w) for val, w in zip(row, col_widths)))
        elif args.output == "csv":
            import csv
            writer = csv.writer(sys.stdout)
            writer.writerow(["full_name", "title", "school", "year", "games", "wins", "losses", "ties", "preseason_rank", "postseason_rank"])
            for r in results:
                writer.writerow([r["full_name"], r["title"], r["name"], r["year"], r["games"], r["wins"], r["losses"], r["ties"], r["preseason_rank"], r["postseason_rank"]])
        elif args.output == "json":
            import json
            json.dump(results, sys.stdout, indent=2)
        else:
            print(f"Unknown output format: {args.output}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()