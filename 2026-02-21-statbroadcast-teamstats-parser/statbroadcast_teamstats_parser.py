#!/usr/bin/env python3
"""Parse StatBroadcast teamstats HTML view from cached game JSON."""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup


DEFAULT_INPUT = os.path.expanduser("~/.cache/statbroadcast/game_604099.json")


WHITESPACE_RE = re.compile(r"\s+")


def clean_text(value: str) -> str:
    value = value.replace("\xa0", " ").strip()
    return WHITESPACE_RE.sub(" ", value)


def iter_strings(obj: Any) -> List[str]:
    strings: List[str] = []
    if isinstance(obj, str):
        strings.append(obj)
    elif isinstance(obj, dict):
        for val in obj.values():
            strings.extend(iter_strings(val))
    elif isinstance(obj, list):
        for item in obj:
            strings.extend(iter_strings(item))
    return strings


def extract_html(payload: Any) -> Optional[str]:
    candidates = []
    for text in iter_strings(payload):
        lowered = text.lower()
        if "<table" in lowered or "<html" in lowered or "teamstats" in lowered:
            candidates.append(text)
    if not candidates:
        return None
    # Prefer the longest candidate (usually the full HTML block).
    candidates.sort(key=len, reverse=True)
    return candidates[0]


def get_title_for_table(table) -> str:
    caption = table.find("caption")
    if caption and caption.get_text(strip=True):
        return clean_text(caption.get_text())

    # Walk backward through siblings for heading-like elements.
    for sibling in table.find_all_previous():
        if sibling.name in {"h1", "h2", "h3", "h4", "h5"}:
            text = sibling.get_text(strip=True)
            if text:
                return clean_text(text)
        if sibling.name in {"div", "p", "span"}:
            classes = " ".join(sibling.get("class", []))
            if any(token in classes.lower() for token in ["title", "header", "section"]):
                text = sibling.get_text(strip=True)
                if text:
                    return clean_text(text)
        if sibling.name == "strong":
            text = sibling.get_text(strip=True)
            if text:
                return clean_text(text)
    return ""


def normalize_title(title: str) -> str:
    lowered = re.sub(r"[^a-z0-9 ]", " ", title.lower())
    lowered = WHITESPACE_RE.sub(" ", lowered).strip()
    return lowered


def map_title_to_key(title: str) -> Optional[str]:
    normalized = normalize_title(title)
    # Map patterns to output keys
    mapping = [
        ("team stats", "team_stats"),
        ("offensive cumulative stats", "team_stats"),
        ("game comparison", "game_comparison"),
        ("offensive efficiency", "offensive_efficiency"),
        ("offense efficiency comparison", "offensive_efficiency"),
        ("special teams", "special_teams"),
        ("special teams comparison", "special_teams"),
        ("defensive comparison", "defensive_comparison"),
        ("defensive stats", "defensive_comparison"),
    ]
    for pattern, key in mapping:
        if pattern in normalized:
            return key
    return None


def extract_headers(row) -> Optional[List[str]]:
    headers = [clean_text(cell.get_text()) for cell in row.find_all("th")]
    if headers:
        return headers
    return None


def parse_table(table) -> List[Dict[str, str]]:
    rows = table.find_all("tr")
    if not rows:
        return []

    header_row_index = None
    headers: Optional[List[str]] = None

    for idx, row in enumerate(rows):
        headers = extract_headers(row)
        if headers:
            header_row_index = idx
            break

    data_rows = rows[header_row_index + 1 if header_row_index is not None else 0 :]

    if headers is None:
        # Build default headers from the widest row.
        max_cells = 0
        for row in rows:
            cell_count = len(row.find_all(["th", "td"]))
            max_cells = max(max_cells, cell_count)
        headers = [f"col_{i + 1}" for i in range(max_cells)]

    parsed: List[Dict[str, str]] = []
    for row in data_rows:
        cells = row.find_all(["th", "td"])
        if not cells:
            continue
        values = [clean_text(cell.get_text()) for cell in cells]
        if all(not value for value in values):
            continue
        row_data: Dict[str, str] = {}
        for idx, header in enumerate(headers):
            row_data[header or f"col_{idx + 1}"] = values[idx] if idx < len(values) else ""
        parsed.append(row_data)

    return parsed


def parse_tables(html: str) -> Dict[str, List[Dict[str, str]]]:
    soup = BeautifulSoup(html, "html.parser")
    results = {
        "team_stats": [],
        "game_comparison": [],
        "offensive_efficiency": [],
        "special_teams": [],
        "defensive_comparison": [],
    }

    for table in soup.find_all("table"):
        title = get_title_for_table(table)
        key = map_title_to_key(title)
        if not key:
            # Try to infer from table class/id.
            attrs = " ".join([" ".join(table.get("class", [])), table.get("id", "")])
            key = map_title_to_key(attrs)
        if not key:
            continue
        results[key].extend(parse_table(table))

    return results


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse StatBroadcast teamstats HTML view from cached game JSON."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=DEFAULT_INPUT,
        help="Path to cached game JSON file",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to write cleaned JSON (defaults to stdout)",
    )
    args = parser.parse_args()

    input_path = os.path.expanduser(args.input)
    if not os.path.exists(input_path):
        sys.stderr.write(f"Input file not found: {input_path}\n")
        return 1

    payload = load_json(input_path)
    html = extract_html(payload)
    if not html:
        sys.stderr.write("No HTML content found in the JSON payload.\n")
        data = {
            "team_stats": [],
            "game_comparison": [],
            "offensive_efficiency": [],
            "special_teams": [],
            "defensive_comparison": [],
        }
    else:
        data = parse_tables(html)

    output_json = json.dumps(data, indent=2, ensure_ascii=True)
    if args.output:
        output_path = os.path.expanduser(args.output)
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(output_json)
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
