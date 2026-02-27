#!/usr/bin/env python3
"""Generate a professional interview dossier for a college football program."""

from __future__ import annotations

import argparse
import html
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

API_BASE = "https://api.collegefootballdata.com"


@dataclass
class SeasonRecord:
    year: int
    wins: int
    losses: int

    @property
    def win_pct(self) -> float:
        total = self.wins + self.losses
        if total == 0:
            return 0.0
        return self.wins / total


class CfbdClient:
    def __init__(self, api_key: str, timeout: int = 20) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            }
        )

    def _get(self, endpoint: str, params: Dict[str, Any]) -> Any:
        url = f"{API_BASE}{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        if response.status_code == 401:
            raise RuntimeError("Unauthorized (401) from CFBD API. Check CFBD_API_KEY.")
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()

    def get_games(self, school: str, year: int) -> List[Dict[str, Any]]:
        data = self._get("/games", {"year": year, "team": school})
        return data if isinstance(data, list) else []

    def get_coaches(self, school: str, year: int) -> List[Dict[str, Any]]:
        data = self._get("/coaches", {"team": school, "year": year})
        return data if isinstance(data, list) else []

    def get_records(self, school: str, year: int) -> List[Dict[str, Any]]:
        data = self._get("/records", {"year": year, "team": school})
        return data if isinstance(data, list) else []


DEMO_SCHOOL = "Indiana"
DEMO_YEAR = 2024
DEMO_DATA = {
    "games": {
        2020: [
            {"home_team": "Indiana", "away_team": "Penn State", "home_points": 36, "away_points": 35, "conference_game": True},
            {"home_team": "Rutgers", "away_team": "Indiana", "home_points": 17, "away_points": 37, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Michigan", "home_points": 38, "away_points": 21, "conference_game": True},
            {"home_team": "Ohio State", "away_team": "Indiana", "home_points": 42, "away_points": 35, "conference_game": True},
            {"home_team": "Maryland", "away_team": "Indiana", "home_points": 35, "away_points": 27, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Wisconsin", "home_points": 14, "away_points": 45, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Purdue", "home_points": 27, "away_points": 13, "conference_game": True},
        ],
        2021: [
            {"home_team": "Iowa", "away_team": "Indiana", "home_points": 34, "away_points": 6, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Cincinnati", "home_points": 24, "away_points": 38, "conference_game": False},
            {"home_team": "Indiana", "away_team": "Western Kentucky", "home_points": 33, "away_points": 31, "conference_game": False},
            {"home_team": "Penn State", "away_team": "Indiana", "home_points": 24, "away_points": 0, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Michigan State", "home_points": 15, "away_points": 20, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Ohio State", "home_points": 7, "away_points": 54, "conference_game": True},
            {"home_team": "Maryland", "away_team": "Indiana", "home_points": 38, "away_points": 35, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Michigan", "home_points": 7, "away_points": 29, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Minnesota", "home_points": 14, "away_points": 35, "conference_game": True},
            {"home_team": "Purdue", "away_team": "Indiana", "home_points": 44, "away_points": 7, "conference_game": True},
        ],
        2022: [
            {"home_team": "Illinois", "away_team": "Indiana", "home_points": 20, "away_points": 23, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Idaho", "home_points": 35, "away_points": 22, "conference_game": False},
            {"home_team": "Cincinnati", "away_team": "Indiana", "home_points": 45, "away_points": 24, "conference_game": False},
            {"home_team": "Nebraska", "away_team": "Indiana", "home_points": 35, "away_points": 21, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Michigan", "home_points": 10, "away_points": 31, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Maryland", "home_points": 33, "away_points": 38, "conference_game": True},
            {"home_team": "Rutgers", "away_team": "Indiana", "home_points": 24, "away_points": 17, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Penn State", "home_points": 14, "away_points": 45, "conference_game": True},
            {"home_team": "Ohio State", "away_team": "Indiana", "home_points": 56, "away_points": 14, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Purdue", "home_points": 16, "away_points": 30, "conference_game": True},
        ],
        2023: [
            {"home_team": "Indiana", "away_team": "Ohio State", "home_points": 3, "away_points": 23, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Indiana State", "home_points": 41, "away_points": 7, "conference_game": False},
            {"home_team": "Louisville", "away_team": "Indiana", "home_points": 21, "away_points": 14, "conference_game": False},
            {"home_team": "Indiana", "away_team": "Akron", "home_points": 29, "away_points": 27, "conference_game": False},
            {"home_team": "Maryland", "away_team": "Indiana", "home_points": 44, "away_points": 17, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Michigan", "home_points": 7, "away_points": 52, "conference_game": True},
            {"home_team": "Rutgers", "away_team": "Indiana", "home_points": 31, "away_points": 14, "conference_game": True},
            {"home_team": "Penn State", "away_team": "Indiana", "home_points": 33, "away_points": 24, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Wisconsin", "home_points": 14, "away_points": 38, "conference_game": True},
            {"home_team": "Illinois", "away_team": "Indiana", "home_points": 48, "away_points": 45, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Michigan State", "home_points": 24, "away_points": 45, "conference_game": True},
            {"home_team": "Purdue", "away_team": "Indiana", "home_points": 35, "away_points": 31, "conference_game": True},
        ],
        2024: [
            {"home_team": "Indiana", "away_team": "FIU", "home_points": 34, "away_points": 10, "conference_game": False},
            {"home_team": "UCLA", "away_team": "Indiana", "home_points": 24, "away_points": 27, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Maryland", "home_points": 31, "away_points": 20, "conference_game": True},
            {"home_team": "Nebraska", "away_team": "Indiana", "home_points": 21, "away_points": 17, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Northwestern", "home_points": 28, "away_points": 14, "conference_game": True},
            {"home_team": "Michigan", "away_team": "Indiana", "home_points": 30, "away_points": 13, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Purdue", "home_points": 35, "away_points": 27, "conference_game": True},
            {"home_team": "Ohio State", "away_team": "Indiana", "home_points": 38, "away_points": 17, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Illinois", "home_points": 24, "away_points": 21, "conference_game": True},
            {"home_team": "Michigan State", "away_team": "Indiana", "home_points": 17, "away_points": 30, "conference_game": True},
            {"home_team": "Indiana", "away_team": "Wisconsin", "home_points": 21, "away_points": 24, "conference_game": True},
            {"home_team": "Minnesota", "away_team": "Indiana", "home_points": 13, "away_points": 16, "conference_game": True},
        ],
    },
    "coaches": [
        {"first_name": "Curt", "last_name": "Cignetti", "position": "Head Coach", "hire_year": 2024},
        {"first_name": "Mike", "last_name": "Shanahan", "position": "Offensive Coordinator", "hire_year": 2024},
        {"first_name": "Bryant", "last_name": "Haines", "position": "Defensive Coordinator", "hire_year": 2024},
        {"first_name": "Grant", "last_name": "Cain", "position": "Special Teams Coordinator", "hire_year": 2024},
    ],
    "records": [
        {
            "year": 2024,
            "team": "Indiana",
            "total": {"wins": 8, "losses": 4},
            "conferenceGames": {"wins": 6, "losses": 3},
        }
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate an HTML coaching interview dossier for a college football program "
            "using College Football Data API data."
        )
    )
    parser.add_argument("--school", type=str, help="School/team name (e.g. Indiana, Purdue).")
    parser.add_argument("--year", type=int, default=2024, help="Current season year (default: 2024).")
    parser.add_argument("--output", type=str, help="Output HTML path (default: dossier_<SCHOOL>_<YEAR>.html).")
    parser.add_argument("--demo", action="store_true", help="Use offline Indiana demo data. No API key required.")
    return parser.parse_args()


def normalize_school_token(school: str) -> str:
    return "_".join(school.strip().split()).upper()


def compute_record(games: List[Dict[str, Any]], school: str) -> SeasonRecord:
    wins = 0
    losses = 0
    for game in games:
        home_team = game.get("home_team")
        away_team = game.get("away_team")
        home_points = game.get("home_points")
        away_points = game.get("away_points")
        if home_points is None or away_points is None:
            continue
        if home_team == school:
            if home_points > away_points:
                wins += 1
            elif home_points < away_points:
                losses += 1
        elif away_team == school:
            if away_points > home_points:
                wins += 1
            elif away_points < home_points:
                losses += 1
    return SeasonRecord(year=0, wins=wins, losses=losses)


def compute_conference_record(games: List[Dict[str, Any]], school: str) -> SeasonRecord:
    wins = 0
    losses = 0
    for game in games:
        if not game.get("conference_game", False):
            continue
        home_team = game.get("home_team")
        away_team = game.get("away_team")
        home_points = game.get("home_points")
        away_points = game.get("away_points")
        if home_points is None or away_points is None:
            continue
        if home_team == school:
            if home_points > away_points:
                wins += 1
            elif home_points < away_points:
                losses += 1
        elif away_team == school:
            if away_points > home_points:
                wins += 1
            elif away_points < home_points:
                losses += 1
    return SeasonRecord(year=0, wins=wins, losses=losses)


def format_win_pct(record: SeasonRecord) -> str:
    return f"{record.win_pct:.3f}" if record.wins + record.losses else "0.000"


def extract_coaching_rows(coach_payload: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    if not coach_payload:
        return []
    first = coach_payload[0]
    if "coaches" in first and isinstance(first["coaches"], list):
        coaches = first["coaches"]
    else:
        coaches = coach_payload
    rows: List[Dict[str, str]] = []
    for coach in coaches:
        first_name = str(coach.get("first_name") or coach.get("firstName") or "").strip()
        last_name = str(coach.get("last_name") or coach.get("lastName") or "").strip()
        full_name = str(coach.get("name") or f"{first_name} {last_name}").strip()
        position = str(coach.get("position") or coach.get("title") or "N/A").strip()
        hire_year = coach.get("hire_year") or coach.get("hireYear")
        hire_text = str(hire_year) if hire_year not in (None, "") else "N/A"
        rows.append({"name": full_name or "N/A", "position": position or "N/A", "hire_year": hire_text})
    return rows


def extract_record_summary(record_payload: List[Dict[str, Any]]) -> str:
    if not record_payload:
        return "Team records endpoint did not return current-year summary data."
    team_entry = record_payload[0]
    total = team_entry.get("total", {}) if isinstance(team_entry, dict) else {}
    conf = team_entry.get("conferenceGames", {}) if isinstance(team_entry, dict) else {}
    total_w = total.get("wins")
    total_l = total.get("losses")
    conf_w = conf.get("wins")
    conf_l = conf.get("losses")
    parts = []
    if total_w is not None and total_l is not None:
        parts.append(f"Official total record: {total_w}-{total_l}")
    if conf_w is not None and conf_l is not None:
        parts.append(f"Official conference record: {conf_w}-{conf_l}")
    if not parts:
        return "Team records endpoint returned limited fields for this program/year."
    return " | ".join(parts)


def build_html(
    school: str,
    year: int,
    season_rows: List[SeasonRecord],
    coaches: List[Dict[str, str]],
    conference_record: Optional[SeasonRecord],
    record_summary: str,
    used_demo: bool,
) -> str:
    school_safe = html.escape(school)

    season_table_rows = "\n".join(
        f"<tr><td>{r.year}</td><td>{r.wins}</td><td>{r.losses}</td><td>{format_win_pct(r)}</td></tr>"
        for r in season_rows
    )

    coach_rows = "\n".join(
        f"<tr><td>{html.escape(c['name'])}</td><td>{html.escape(c['position'])}</td><td>{html.escape(c['hire_year'])}</td></tr>"
        for c in coaches
    )
    if not coach_rows:
        coach_rows = '<tr><td colspan="3">No coaching staff data was returned for this selection.</td></tr>'

    if conference_record and (conference_record.wins + conference_record.losses) > 0:
        comp_text = (
            f"From game-level conference matchups, {school_safe}'s {year} conference record "
            f"computes to <strong>{conference_record.wins}-{conference_record.losses}</strong> "
            f"({format_win_pct(conference_record)} win%)."
        )
    else:
        comp_text = (
            "Conference record could not be computed from game data for this selection. "
            "Some games may be missing scores or conference flags."
        )

    source_badge = "DEMO DATA" if used_demo else "LIVE CFBD DATA"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{school_safe} Coach Interview Dossier ({year})</title>
  <style>
    :root {{
      --navy-950: #071a2f;
      --navy-900: #0a2342;
      --navy-800: #103057;
      --gold-500: #c8a951;
      --gold-400: #d8bc73;
      --slate-100: #eef3fa;
      --slate-300: #c9d3e2;
      --slate-500: #8ea2bf;
      --line: rgba(201, 211, 226, 0.24);
      --panel: rgba(8, 27, 50, 0.72);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Trebuchet MS", "Segoe UI", Tahoma, Arial, sans-serif;
      background:
        radial-gradient(circle at 15% 10%, #194376 0%, transparent 30%),
        radial-gradient(circle at 85% 20%, #12345f 0%, transparent 28%),
        linear-gradient(160deg, var(--navy-950), var(--navy-900) 48%, #061425 100%);
      color: var(--slate-100);
      min-height: 100vh;
    }}
    .wrap {{
      max-width: 1080px;
      margin: 36px auto;
      padding: 0 20px 40px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(16,48,87,0.92), rgba(8,27,50,0.95));
      border: 1px solid rgba(200, 169, 81, 0.34);
      border-radius: 16px;
      padding: 28px;
      box-shadow: 0 18px 40px rgba(2, 8, 20, 0.45);
      position: relative;
      overflow: hidden;
    }}
    .hero::after {{
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(120deg, transparent 35%, rgba(216,188,115,0.08), transparent 62%);
      pointer-events: none;
    }}
    .eyebrow {{
      display: inline-block;
      font-size: 12px;
      letter-spacing: 1.6px;
      font-weight: 700;
      color: var(--gold-400);
      border: 1px solid rgba(216,188,115,0.5);
      border-radius: 999px;
      padding: 6px 10px;
      text-transform: uppercase;
      margin-bottom: 12px;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(28px, 5vw, 44px);
      color: #fff;
      letter-spacing: 0.4px;
    }}
    .subtitle {{
      margin: 8px 0 0;
      color: var(--slate-300);
      font-size: 17px;
      max-width: 720px;
      line-height: 1.45;
    }}
    .grid {{
      margin-top: 18px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 18px;
      backdrop-filter: blur(1px);
    }}
    h2 {{
      margin: 2px 0 12px;
      color: var(--gold-400);
      font-size: 19px;
      letter-spacing: 0.3px;
    }}
    p {{ margin: 8px 0; line-height: 1.45; color: var(--slate-100); }}
    .muted {{ color: var(--slate-500); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      overflow: hidden;
      border-radius: 10px;
      border: 1px solid var(--line);
    }}
    thead tr {{
      background: linear-gradient(90deg, rgba(200,169,81,0.22), rgba(200,169,81,0.08));
    }}
    th, td {{
      text-align: left;
      padding: 10px;
      border-bottom: 1px solid var(--line);
    }}
    tbody tr:nth-child(even) {{ background: rgba(255,255,255,0.03); }}
    tbody tr:last-child td {{ border-bottom: none; }}
    ul {{
      margin: 8px 0 0;
      padding-left: 18px;
      color: var(--slate-100);
      line-height: 1.5;
    }}
    .footer {{
      margin-top: 18px;
      text-align: center;
      font-size: 12px;
      color: var(--slate-500);
      letter-spacing: 0.6px;
      text-transform: uppercase;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="eyebrow">{source_badge}</div>
      <h1>{school_safe} Football | Coach Interview Dossier ({year})</h1>
      <p class="subtitle">Executive snapshot prepared for leadership conversations, contract evaluations, and strategic staffing discussions.</p>
    </section>

    <section class="grid">
      <article class="card">
        <h2>5-Year W/L Record</h2>
        <table>
          <thead><tr><th>Season</th><th>Wins</th><th>Losses</th><th>Win %</th></tr></thead>
          <tbody>{season_table_rows}</tbody>
        </table>
      </article>

      <article class="card">
        <h2>Current Coaching Staff</h2>
        <table>
          <thead><tr><th>Name</th><th>Position</th><th>Hire Year</th></tr></thead>
          <tbody>{coach_rows}</tbody>
        </table>
      </article>

      <article class="card">
        <h2>Competitive Landscape</h2>
        <p>{comp_text}</p>
        <p class="muted">{html.escape(record_summary)}</p>
      </article>

      <article class="card">
        <h2>Key Opportunities &amp; Challenges</h2>
        <ul>
          <li>Opportunity: [Insert roster-development leverage point]</li>
          <li>Opportunity: [Insert NIL / donor engagement angle]</li>
          <li>Challenge: [Insert conference scheduling pressure]</li>
          <li>Challenge: [Insert retention or portal management risk]</li>
        </ul>
      </article>
    </section>

    <div class="footer">Generated by Seneca Coach Dossier Tool</div>
  </div>
</body>
</html>
"""


def load_data(
    school: str,
    year: int,
    demo: bool,
) -> tuple:
    years = list(range(year - 4, year + 1))

    if demo:
        if school != DEMO_SCHOOL or year != DEMO_YEAR:
            raise RuntimeError("Demo mode currently supports only --school Indiana --year 2024.")

        season_records: List[SeasonRecord] = []
        latest_games: List[Dict[str, Any]] = []
        for y in years:
            games = DEMO_DATA["games"].get(y, [])
            stamped_games = [dict(g, season=y) for g in games]
            rec = compute_record(stamped_games, school)
            rec.year = y
            season_records.append(rec)
            if y == year:
                latest_games = stamped_games

        coaches = extract_coaching_rows(DEMO_DATA["coaches"])
        conference_record = compute_conference_record(latest_games, school)
        conference_record.year = year
        record_summary = extract_record_summary(DEMO_DATA["records"])
        return season_records, coaches, conference_record, record_summary

    api_key = os.getenv("CFBD_API_KEY")
    if not api_key:
        raise RuntimeError("CFBD_API_KEY is required for live mode. Set it or use --demo.")

    client = CfbdClient(api_key)
    season_records = []
    latest_games = []
    for y in years:
        games = client.get_games(school, y)
        stamped_games = [dict(g, season=y) for g in games]
        rec = compute_record(stamped_games, school)
        rec.year = y
        season_records.append(rec)
        if y == year:
            latest_games = stamped_games

    coaches_payload = client.get_coaches(school, year)
    coaches = extract_coaching_rows(coaches_payload)

    conference_record = None
    if latest_games:
        conference_record = compute_conference_record(latest_games, school)
        conference_record.year = year

    records_payload = client.get_records(school, year)
    record_summary = extract_record_summary(records_payload)
    return season_records, coaches, conference_record, record_summary


def main() -> int:
    args = parse_args()

    if args.demo:
        school = DEMO_SCHOOL
        year = DEMO_YEAR
    else:
        if not args.school:
            print("Error: --school is required unless --demo is used.", file=sys.stderr)
            return 2
        school = args.school.strip()
        year = args.year

    default_name = f"dossier_{normalize_school_token(school)}_{year}.html"
    output_path = args.output or default_name

    try:
        season_rows, coaches, conference_record, record_summary = load_data(
            school=school, year=year, demo=args.demo
        )
        html_doc = build_html(
            school=school,
            year=year,
            season_rows=season_rows,
            coaches=coaches,
            conference_record=conference_record,
            record_summary=record_summary,
            used_demo=args.demo,
        )
    except requests.RequestException as exc:
        print(f"API request failed: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print(f"Dossier generated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
