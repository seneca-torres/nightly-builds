#!/usr/bin/env python3
"""Detect new rental listings by comparing fresh search results with a local cache."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

RENTAL_FINDER_PATH = Path("/Users/vicmacmini/clawd/nightly-builds/2026-01-30/rental_finder.py")
LISTINGS_FILE = RENTAL_FINDER_PATH.parent / "listings.json"
CACHE_FILE = Path.cwd() / "previous_listings.json"


def load_json_list(path: Path, label: str, verbose: bool = False) -> List[Dict[str, Any]]:
    if not path.exists():
        if verbose:
            print(f"[verbose] {label} file not found: {path}")
        return []
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, list):
            print(f"[warn] {label} JSON is not a list in {path}. Using empty list.")
            return []
        return [item for item in data if isinstance(item, dict)]
    except json.JSONDecodeError as exc:
        print(f"[warn] Failed to parse {label} JSON at {path}: {exc}. Using empty list.")
        return []
    except OSError as exc:
        print(f"[warn] Failed reading {label} file at {path}: {exc}. Using empty list.")
        return []


def save_json_list(path: Path, data: List[Dict[str, Any]], verbose: bool = False) -> bool:
    try:
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        if verbose:
            print(f"[verbose] Wrote {len(data)} cached listings to {path}")
        return True
    except OSError as exc:
        print(f"[error] Failed to write cache file {path}: {exc}")
        return False


def listing_key(item: Dict[str, Any]) -> str:
    link = item.get("link")
    return link.strip() if isinstance(link, str) else ""


def merge_by_link(old_items: List[Dict[str, Any]], fresh_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Keep insertion order by first loading old items, then replacing/updating with fresh items by link.
    merged: Dict[str, Dict[str, Any]] = {}
    no_link_items: List[Dict[str, Any]] = []

    for item in old_items:
        key = listing_key(item)
        if key:
            merged[key] = item
        else:
            no_link_items.append(item)

    for item in fresh_items:
        key = listing_key(item)
        if key:
            merged[key] = item
        else:
            no_link_items.append(item)

    return list(merged.values()) + no_link_items


def print_new_listings_markdown(new_items: List[Dict[str, Any]]) -> None:
    if not new_items:
        print("## New Rental Listings")
        print("")
        print("No new listings found.")
        return

    print("## New Rental Listings")
    print("")
    for item in new_items:
        address = item.get("address") or "Unknown address"
        price = item.get("price")
        price_text = f"${price}" if price is not None else "N/A"
        beds_baths = item.get("beds_baths") or "N/A"
        link = item.get("link") or "N/A"
        source = item.get("source") or "N/A"
        listing_date = item.get("listing_date") or "N/A"

        print(f"### {address}")
        print(f"- **Price:** {price_text}")
        print(f"- **Beds/Baths:** {beds_baths}")
        print(f"- **Link:** {link}")
        print(f"- **Source:** {source}")
        print(f"- **Listing Date:** {listing_date}")
        print("")


def run_rental_finder(use_demo: bool, verbose: bool = False) -> bool:
    if not RENTAL_FINDER_PATH.exists():
        print(f"[error] rental_finder.py not found at {RENTAL_FINDER_PATH}")
        return False

    cmd = [sys.executable, str(RENTAL_FINDER_PATH), "--search"]
    if use_demo:
        cmd.append("--demo")

    if verbose:
        print(f"[verbose] Running: {' '.join(cmd)}")
        print(f"[verbose] Working directory: {RENTAL_FINDER_PATH.parent}")

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(RENTAL_FINDER_PATH.parent),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(f"[error] Failed to execute rental_finder.py: {exc}")
        return False

    if verbose and proc.stdout.strip():
        print("[verbose] rental_finder stdout:")
        print(proc.stdout.strip())
    if verbose and proc.stderr.strip():
        print("[verbose] rental_finder stderr:")
        print(proc.stderr.strip())

    if proc.returncode != 0:
        print(f"[error] rental_finder.py exited with code {proc.returncode}")
        return False

    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect new rental listings from rental_finder results.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", action="store_true", help="Run rental_finder in demo mode (default).")
    mode.add_argument("--real", action="store_true", help="Run rental_finder without --demo.")
    parser.add_argument("--verbose", action="store_true", help="Print verbose diagnostics.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Default to demo for safety unless user explicitly asks for real mode.
    use_demo = not args.real
    if args.verbose:
        print(f"[verbose] Mode: {'demo' if use_demo else 'real'}")

    prev_items = load_json_list(CACHE_FILE, "cache", verbose=args.verbose)
    prev_links: Set[str] = {listing_key(item) for item in prev_items if listing_key(item)}

    if not run_rental_finder(use_demo=use_demo, verbose=args.verbose):
        print("[error] Search step failed; cache was not updated.")
        print("Verification: 0 new listings found.")
        return 1

    fresh_items = load_json_list(LISTINGS_FILE, "fresh listings", verbose=args.verbose)
    if args.verbose:
        print(f"[verbose] Loaded {len(prev_items)} previous cached listings")
        print(f"[verbose] Loaded {len(fresh_items)} fresh listings from {LISTINGS_FILE}")

    new_items = []
    for item in fresh_items:
        key = listing_key(item)
        if key and key not in prev_links:
            new_items.append(item)

    print_new_listings_markdown(new_items)

    combined = merge_by_link(prev_items, fresh_items)
    save_json_list(CACHE_FILE, combined, verbose=args.verbose)

    print(f"Verification: {len(new_items)} new listings found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())