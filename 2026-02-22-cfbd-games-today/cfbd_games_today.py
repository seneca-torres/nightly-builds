#!/usr/bin/env python3
"""Fetch today's college football games from CFBD and print a table."""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Optional

try:
    import requests  # type: ignore

    _HAS_REQUESTS = True
except Exception:
    _HAS_REQUESTS = False

try:
    from zoneinfo import ZoneInfo
except Exception as exc:  # pragma: no cover - zoneinfo is stdlib in 3.9+
    raise SystemExit(f"zoneinfo unavailable: {exc}")

CFBD_GAMES_URL = "https://api.collegefootballdata.com/games"
PHOENIX_TZ = ZoneInfo("America/Phoenix")
CFBD_API_KEY_ENV = "CFBD_API_KEY"


class AuthError(RuntimeError):
    pass


@dataclass
class GameRow:
    start_time: str
    away_team: str
    home_team: str
    tv: str
    status: str


def phoenix_today() -> date:
    return datetime.now(PHOENIX_TZ).date()


def season_type_for(today: date) -> str:
    # Simple heuristic: postseason often spans mid-Dec through Jan.
    if today.month == 1:
        return "postseason"
    if today.month == 12 and today.day >= 10:
        return "postseason"
    return "regular"


def auth_error_message() -> str:
    return (
        "CFBD API authentication failed: no API key found. "
        "Register for a free key at CollegeFootballData.com and set it via "
        f"{CFBD_API_KEY_ENV} (e.g. `export {CFBD_API_KEY_ENV}='YOUR_KEY'`). "
        "You can also run with --demo for cached sample data."
    )


def _fetch_via_requests(
    url: str,
    params: dict[str, Any],
    api_key: Optional[str],
) -> List[dict[str, Any]]:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    if resp.status_code == 401 and not api_key:
        raise AuthError(auth_error_message())
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError("Unexpected API response (not a list)")
    return data


def _fetch_via_urllib(
    url: str,
    params: dict[str, Any],
    api_key: Optional[str],
) -> List[dict[str, Any]]:
    from urllib.parse import urlencode
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    query = urlencode(params)
    full_url = f"{url}?{query}"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    req = Request(full_url, headers=headers)
    try:
        with urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
    except HTTPError as exc:
        if exc.code == 401 and not api_key:
            raise AuthError(auth_error_message()) from exc
        raise
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Unexpected API response (not a list)")
    return data


def fetch_games(year: int, season_type: str) -> List[dict[str, Any]]:
    params = {"year": year, "seasonType": season_type}
    api_key = os.getenv(CFBD_API_KEY_ENV)
    if _HAS_REQUESTS:
        return _fetch_via_requests(CFBD_GAMES_URL, params, api_key)
    return _fetch_via_urllib(CFBD_GAMES_URL, params, api_key)


def parse_start_datetime(start_date: str) -> Optional[datetime]:
    if not start_date:
        return None
    cleaned = start_date.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        # Try a couple of common ISO formats.
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
    return None


def start_date_matches_today(start_date: str, today: date) -> bool:
    if not start_date:
        return False
    try:
        game_date = date.fromisoformat(start_date[:10])
    except ValueError:
        return False
    return game_date == today


def format_local_time(start_date: str) -> str:
    dt = parse_start_datetime(start_date)
    if not dt:
        return "TBD"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local_dt = dt.astimezone(PHOENIX_TZ)
    return local_dt.strftime("%-I:%M %p")


def normalize_status(game: dict[str, Any]) -> str:
    status_raw = str(game.get("status", "")).lower().strip()
    if game.get("completed") is True or "final" in status_raw:
        return "final"
    if "in progress" in status_raw or "live" in status_raw or status_raw in {"in_progress", "in-progress"}:
        return "in-progress"
    if "scheduled" in status_raw or "pre" in status_raw or not status_raw:
        return "scheduled"
    return status_raw.replace("_", "-")


def game_to_row(game: dict[str, Any]) -> GameRow:
    tv = game.get("broadcast") or game.get("tv") or ""
    return GameRow(
        start_time=format_local_time(game.get("start_date", "")),
        away_team=game.get("away_team", ""),
        home_team=game.get("home_team", ""),
        tv=tv or "-",
        status=normalize_status(game),
    )


def build_table(rows: Iterable[GameRow]) -> str:
    headers = ("start_time", "away_team", "home_team", "TV", "status")
    data = [
        (r.start_time, r.away_team, r.home_team, r.tv, r.status)
        for r in rows
    ]
    widths = [len(h) for h in headers]
    for row in data:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(str(cell)))
    line_parts = [h.ljust(widths[i]) for i, h in enumerate(headers)]
    lines = ["  ".join(line_parts)]
    lines.append("  ".join("-" * w for w in widths))
    for row in data:
        line = "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        lines.append(line)
    return "\n".join(lines)


def load_demo_games(today: date) -> List[dict[str, Any]]:
    demo_path = Path(__file__).with_name("sample_games.json")
    data = json.loads(demo_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Demo data should be a list")
    # Shift demo dates to today while keeping the local time for predictable output.
    shifted = []
    for game in data:
        start_date = game.get("start_date", "")
        dt = parse_start_datetime(start_date)
        if dt:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            local = dt.astimezone(PHOENIX_TZ)
            local = local.replace(year=today.year, month=today.month, day=today.day)
            game = dict(game)
            game["start_date"] = local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        shifted.append(game)
    return shifted


def main() -> int:
    parser = argparse.ArgumentParser(description="CFBD games today (America/Phoenix)")
    parser.add_argument("--demo", action="store_true", help="use cached sample data")
    args = parser.parse_args()

    today = phoenix_today()
    season_type = season_type_for(today)
    year = today.year

    try:
        if args.demo:
            games = load_demo_games(today)
        else:
            games = fetch_games(year, season_type)
    except AuthError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error fetching games: {exc}", file=sys.stderr)
        return 1

    todays_games = [
        g for g in games
        if start_date_matches_today(str(g.get("start_date", "")), today)
    ]

    if not todays_games:
        label = "demo" if args.demo else "live"
        print(f"No games found for {today.isoformat()} ({label} data).")
        return 0

    rows = [game_to_row(g) for g in todays_games]
    print(build_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
