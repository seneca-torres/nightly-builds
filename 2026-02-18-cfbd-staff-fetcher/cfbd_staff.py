#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

API_BASE = "https://api.collegefootballdata.com"
COACHES_ENDPOINT = "/coaches"

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


def normalize_school_tag(school: str) -> str:
    return school.strip().lower().replace(" ", "-")


def coach_full_name(coach: Dict[str, Any]) -> str:
    first = coach.get("first_name") or ""
    last = coach.get("last_name") or ""
    return (first + " " + last).strip()


def fetch_coaches(school: Optional[str], year: Optional[int]) -> List[Dict[str, Any]]:
    params = {}
    if school:
        params["school"] = school
    if year is not None:
        params["year"] = year

    url = API_BASE + COACHES_ENDPOINT
    response = requests.get(url, params=params, timeout=30)
    if response.status_code in (401, 403):
        api_key = input("CFBD API key required for this query. Enter key: ").strip()
        if not api_key:
            raise RuntimeError("API key was not provided.")
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, params=params, headers=headers, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(
            f"CFBD API request failed (HTTP {response.status_code}): {response.text.strip()}"
        )

    data = response.json()
    if not isinstance(data, list):
        raise RuntimeError("Unexpected response format from CFBD API.")
    return data


def filter_history_by_name(data: List[Dict[str, Any]], name_query: str) -> List[Dict[str, Any]]:
    needle = name_query.strip().lower()
    if not needle:
        return []
    results = []
    for coach in data:
        full = coach_full_name(coach).lower()
        if needle in full:
            results.append(coach)
    return results


def format_date(date_str: Optional[str]) -> str:
    if not date_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.date().isoformat()
    except ValueError:
        return date_str


def build_markdown(school: str, year: int, data: List[Dict[str, Any]]) -> str:
    tag_school = normalize_school_tag(school)
    lines = [
        "---",
        f"tags: [football, coaching-staff, {tag_school}, {year}]",
        f"school: {school}",
        f"year: {year}",
        "---",
        f"# {school} Coaching Staff {year}",
        "",
        "| Coach | Role | Hire Date |",
        "| --- | --- | --- |",
    ]

    for coach in data:
        name = coach_full_name(coach) or "Unknown"
        role = coach.get("position") or coach.get("role") or "Unknown"
        hire_date = format_date(coach.get("hire_date"))
        lines.append(f"| {name} | {role} | {hire_date} |")

    lines.append("")
    for coach in data:
        name = coach_full_name(coach) or "Unknown"
        role = coach.get("position") or coach.get("role") or "Unknown"
        hire_date = format_date(coach.get("hire_date"))
        lines.extend(
            [
                f"## {name}",
                f"- Role: {role}",
                f"- Hire Date: {hire_date}",
                "",
                "| School | Year | Games | Wins | Losses | Ties | Preseason Rank | Postseason Rank |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        seasons = coach.get("seasons") or []
        for season in seasons:
            lines.append(
                "| {school} | {year} | {games} | {wins} | {losses} | {ties} | {pre} | {post} |".format(
                    school=season.get("school") or "Unknown",
                    year=season.get("year") or "Unknown",
                    games=season.get("games") or 0,
                    wins=season.get("wins") or 0,
                    losses=season.get("losses") or 0,
                    ties=season.get("ties") or 0,
                    pre=season.get("preseason_rank")
                    if season.get("preseason_rank") is not None
                    else "-",
                    post=season.get("postseason_rank")
                    if season.get("postseason_rank") is not None
                    else "-",
                )
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_csv(data: List[Dict[str, Any]]) -> str:
    output = []
    header = [
        "first_name",
        "last_name",
        "position",
        "hire_date",
        "season_school",
        "season_year",
        "games",
        "wins",
        "losses",
        "ties",
        "preseason_rank",
        "postseason_rank",
    ]
    output.append(header)
    for coach in data:
        base = [
            coach.get("first_name") or "",
            coach.get("last_name") or "",
            coach.get("position") or coach.get("role") or "",
            coach.get("hire_date") or "",
        ]
        seasons = coach.get("seasons") or []
        if not seasons:
            output.append(base + ["", "", "", "", "", "", ""])
        for season in seasons:
            row = base + [
                season.get("school") or "",
                season.get("year") or "",
                season.get("games") or 0,
                season.get("wins") or 0,
                season.get("losses") or 0,
                season.get("ties") or 0,
                "" if season.get("preseason_rank") is None else season.get("preseason_rank"),
                "" if season.get("postseason_rank") is None else season.get("postseason_rank"),
            ]
            output.append(row)

    from io import StringIO

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerows(output)
    return buf.getvalue()


def build_json(data: List[Dict[str, Any]]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def resolve_data(args: argparse.Namespace) -> List[Dict[str, Any]]:
    if args.demo:
        return DEMO_DATA
    return fetch_coaches(args.school, args.year)


def command_staff(args: argparse.Namespace) -> str:
    data = resolve_data(args)
    if not data:
        return "No staff data found.\n"
    lines = []
    for coach in data:
        name = coach_full_name(coach) or "Unknown"
        role = coach.get("position") or coach.get("role") or "Unknown"
        hire_date = format_date(coach.get("hire_date"))
        lines.append(f"{name} — {role} (Hire Date: {hire_date})")
    return "\n".join(lines) + "\n"


def command_history(args: argparse.Namespace) -> str:
    data = resolve_data(args)
    matches = filter_history_by_name(data, args.coach)
    if not matches:
        return f"No coaches matched '{args.coach}'.\n"

    lines = []
    for coach in matches:
        name = coach_full_name(coach) or "Unknown"
        lines.append(name)
        seasons = coach.get("seasons") or []
        if not seasons:
            lines.append("  No season history available.")
            continue
        for season in seasons:
            school = season.get("school") or "Unknown"
            year = season.get("year") or "Unknown"
            wins = season.get("wins") or 0
            losses = season.get("losses") or 0
            ties = season.get("ties") or 0
            lines.append(f"  {year} — {school}: {wins}-{losses}-{ties}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def command_export(args: argparse.Namespace) -> str:
    data = resolve_data(args)
    if args.format == "markdown":
        if not args.school or args.year is None:
            raise RuntimeError("markdown export requires --school and --year.")
        return build_markdown(args.school, args.year, data)
    if args.format == "json":
        return build_json(data)
    if args.format == "csv":
        return build_csv(data)
    raise RuntimeError(f"Unsupported format: {args.format}")


def write_output(text: str, output_path: Optional[str]) -> None:
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch college football coaching staff data from the CFBD API."
    )
    parser.add_argument("--demo", action="store_true", help="Use demo data (no API calls)")
    parser.add_argument("--output", help="Write output to a file instead of stdout")

    subparsers = parser.add_subparsers(dest="command", required=True)

    staff_parser = subparsers.add_parser("staff", help="List coaching staff")
    staff_parser.add_argument("--school", required=False, help="School name")
    staff_parser.add_argument("--year", type=int, required=False, help="Season year")
    staff_parser.set_defaults(func=command_staff)

    history_parser = subparsers.add_parser("history", help="Show coach history")
    history_parser.add_argument("--coach", required=True, help="Coach name to search")
    history_parser.add_argument("--school", required=False, help="School name")
    history_parser.add_argument("--year", type=int, required=False, help="Season year")
    history_parser.set_defaults(func=command_history)

    export_parser = subparsers.add_parser("export", help="Export staff data")
    export_parser.add_argument("--school", required=False, help="School name")
    export_parser.add_argument("--year", type=int, required=False, help="Season year")
    export_parser.add_argument(
        "--format",
        choices=["markdown", "json", "csv"],
        required=True,
        help="Export format",
    )
    export_parser.set_defaults(func=command_export)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        output = args.func(args)
        write_output(output, args.output)
        return 0
    except requests.RequestException as exc:
        sys.stderr.write(f"Network error: {exc}\n")
    except RuntimeError as exc:
        sys.stderr.write(f"Error: {exc}\n")
    except KeyboardInterrupt:
        sys.stderr.write("Aborted.\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
