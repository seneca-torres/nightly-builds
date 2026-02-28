#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


@dataclass
class StaffMatch:
    head_coach: str
    offensive_coordinator: str
    coaching_tree: str


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def detect_staff(staff_db: list[dict[str, Any]], team: str, game_date: str) -> StaffMatch | None:
    target = parse_date(game_date)
    for entry in staff_db:
        if entry["team"].lower() != team.lower():
            continue
        start = parse_date(entry["start_date"])
        end = parse_date(entry["end_date"]) if entry.get("end_date") else date.max
        if start <= target <= end:
            return StaffMatch(
                head_coach=entry["head_coach"],
                offensive_coordinator=entry["offensive_coordinator"],
                coaching_tree=entry.get("coaching_tree", "Unknown"),
            )
    return None


def apply_tags(
    play: dict[str, Any],
    *,
    head_coach: str | None = None,
    offensive_coordinator: str | None = None,
    coaching_tree: str | None = None,
    concepts: list[str] | None = None,
    players: list[str] | None = None,
    auto_staff: StaffMatch | None = None,
) -> dict[str, Any]:
    tags = play.setdefault("tags", {})

    if auto_staff is not None:
        tags["head_coach"] = auto_staff.head_coach
        tags["offensive_coordinator"] = auto_staff.offensive_coordinator
        tags["coaching_tree"] = auto_staff.coaching_tree

    if head_coach:
        tags["head_coach"] = head_coach
    if offensive_coordinator:
        tags["offensive_coordinator"] = offensive_coordinator
    if coaching_tree:
        tags["coaching_tree"] = coaching_tree
    if concepts:
        tags["concepts"] = sorted(set(tags.get("concepts", []) + concepts))
    if players:
        tags["players"] = sorted(set(tags.get("players", []) + players))

    return play


def matches_filter(play: dict[str, Any], args: argparse.Namespace) -> bool:
    tags = play.get("tags", {})

    if args.team and play["team"].lower() != args.team.lower():
        return False
    if args.head_coach and tags.get("head_coach", "").lower() != args.head_coach.lower():
        return False
    if args.offensive_coordinator and tags.get("offensive_coordinator", "").lower() != args.offensive_coordinator.lower():
        return False
    if args.coaching_tree and tags.get("coaching_tree", "").lower() != args.coaching_tree.lower():
        return False
    if args.concept:
        concepts = [item.lower() for item in tags.get("concepts", [])]
        if args.concept.lower() not in concepts:
            return False
    if args.player:
        players = [item.lower() for item in tags.get("players", [])]
        if args.player.lower() not in players:
            return False

    return True


def print_results(plays: list[dict[str, Any]]) -> None:
    if not plays:
        print("No plays matched.")
        return

    for play in plays:
        tags = play.get("tags", {})
        print(f"{play['play_id']} | {play['date']} | {play['team']} vs {play['opponent']}")
        print(f"  {play['description']}")
        print(
            f"  HC={tags.get('head_coach', 'n/a')} | "
            f"OC={tags.get('offensive_coordinator', 'n/a')} | "
            f"Tree={tags.get('coaching_tree', 'n/a')}"
        )
        print(
            f"  Concepts={', '.join(tags.get('concepts', [])) or 'n/a'} | "
            f"Players={', '.join(tags.get('players', [])) or 'n/a'}"
        )


def cmd_search(args: argparse.Namespace) -> int:
    plays = load_json(Path(args.plays))
    results = [play for play in plays if matches_filter(play, args)]
    print_results(results)
    return 0


def cmd_tag(args: argparse.Namespace) -> int:
    plays_path = Path(args.plays)
    staff_path = Path(args.staff)
    plays = load_json(plays_path)
    staff_db = load_json(staff_path)

    play = next((item for item in plays if item["play_id"] == args.play_id), None)
    if play is None:
        raise SystemExit(f"Play not found: {args.play_id}")

    auto_staff = None
    if args.auto_detect:
        auto_staff = detect_staff(staff_db, play["team"], play["date"])
        if auto_staff is None:
            raise SystemExit(
                "No coaching staff match found for this play. "
                "Use --head-coach/--offensive-coordinator manually or add staff data."
            )

    apply_tags(
        play,
        head_coach=args.head_coach,
        offensive_coordinator=args.offensive_coordinator,
        coaching_tree=args.coaching_tree,
        concepts=args.concept or [],
        players=args.player or [],
        auto_staff=auto_staff,
    )

    save_json(plays_path, plays)
    print(f"Updated {args.play_id}")
    return 0


def cmd_detect_staff(args: argparse.Namespace) -> int:
    staff_db = load_json(Path(args.staff))
    match = detect_staff(staff_db, args.team, args.date)
    if match is None:
        print("No coaching staff match found.")
        return 1

    print(f"Head coach: {match.head_coach}")
    print(f"Offensive coordinator: {match.offensive_coordinator}")
    print(f"Coaching tree: {match.coaching_tree}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Small CLI for OPAD play tagging and coaching attribution."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search plays by coaching and concept tags.")
    search.add_argument("--plays", default="data/plays.json")
    search.add_argument("--team")
    search.add_argument("--head-coach")
    search.add_argument("--offensive-coordinator")
    search.add_argument("--coaching-tree")
    search.add_argument("--concept")
    search.add_argument("--player")
    search.set_defaults(func=cmd_search)

    tag = subparsers.add_parser("tag", help="Tag a play manually or with auto-detected staff.")
    tag.add_argument("play_id")
    tag.add_argument("--plays", default="data/plays.json")
    tag.add_argument("--staff", default="data/staff.json")
    tag.add_argument("--auto-detect", action="store_true")
    tag.add_argument("--head-coach")
    tag.add_argument("--offensive-coordinator")
    tag.add_argument("--coaching-tree")
    tag.add_argument("--concept", action="append")
    tag.add_argument("--player", action="append")
    tag.set_defaults(func=cmd_tag)

    detect = subparsers.add_parser("detect-staff", help="Show staff inferred from team + date.")
    detect.add_argument("--staff", default="data/staff.json")
    detect.add_argument("--team", required=True)
    detect.add_argument("--date", required=True)
    detect.set_defaults(func=cmd_detect_staff)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
