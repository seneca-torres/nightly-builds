#!/usr/bin/env python3
"""Extract simple entities from plain-text coaching notes and write Markdown output.

This script detects entities using static lists/patterns:
- coach names
- school names
- dates
- roles

It then writes a Markdown file with YAML frontmatter, backlink sections,
and optionally inline backlinks in the original text.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


# Static detection lists (case-insensitive matching)
COACHES = [
    "Nick Saban",
    "Kirby Smart",
    "Dabo Swinney",
    "Ryan Day",
    "Lincoln Riley",
    "Lane Kiffin",
    "Mike Norvell",
    "Jim Harbaugh",
    "Deion Sanders",
    "Brian Kelly",
    "Ryan Grubb",
    "Kalen DeBoer",
]

SCHOOLS = [
    "Alabama",
    "Georgia",
    "Clemson",
    "Ohio State",
    "USC",
    "Ole Miss",
    "Florida State",
    "Michigan",
    "Colorado",
    "LSU",
    "Texas",
]

ROLES = [
    "Head Coach",
    "Offensive Coordinator",
    "Defensive Coordinator",
    "Quarterbacks Coach",
    "Running Backs Coach",
    "Wide Receivers Coach",
    "Linebackers Coach",
    "Special Teams Coordinator",
    "Recruiting Coordinator",
    "Assistant Coach",
]

# Date patterns: YYYY-MM-DD, MM/DD/YYYY, and Month DD, YYYY
DATE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"),
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
        re.IGNORECASE,
    ),
]


def find_from_static_list(text: str, items: list[str]) -> list[str]:
    """Return unique list entries found in text (case-insensitive), preserving list order."""
    lower_text = text.lower()
    found: list[str] = []
    for item in items:
        if item.lower() in lower_text:
            found.append(item)
    return found


def find_dates(text: str) -> list[str]:
    """Extract date-like strings using simple regex patterns."""
    matches: list[str] = []
    seen: set[str] = set()
    for pattern in DATE_PATTERNS:
        for m in pattern.findall(text):
            if m not in seen:
                seen.add(m)
                matches.append(m)
    return matches


def replace_with_backlinks(text: str, items: list[str]) -> str:
    """Replace each occurrence of items with [[item]] in the text."""
    # Sort by length descending to avoid partial replacements
    sorted_items = sorted(items, key=lambda x: len(x), reverse=True)
    for item in sorted_items:
        # Use case-insensitive replacement, preserving original casing
        # We'll use a regex with word boundaries
        pattern = re.compile(re.escape(item), re.IGNORECASE)
        text = pattern.sub(f"[[{item}]]", text)
    return text


def to_yaml_list(key: str, values: list[str]) -> str:
    """Build a YAML list block for frontmatter."""
    if not values:
        return f"{key}: []"
    lines = [f"{key}:"]
    lines.extend(f'  - "{v}"' for v in values)
    return "\n".join(lines)


def build_markdown(
    source_name: str,
    text: str,
    coaches: list[str],
    schools: list[str],
    dates: list[str],
    roles: list[str],
    inline_backlinks: bool = True,
) -> str:
    """Create final Markdown output with YAML frontmatter and backlinks."""
    backlinks = sorted({*coaches, *schools, *roles})

    fm_lines = [
        "---",
        f'source: "{source_name}"',
        to_yaml_list("coaches", coaches),
        to_yaml_list("schools", schools),
        to_yaml_list("dates", dates),
        to_yaml_list("roles", roles),
        "---",
        "",
        "# Extracted Entities",
        "",
    ]

    body_lines = []
    
    # Original text with backlinks
    if inline_backlinks:
        transformed_text = text
        transformed_text = replace_with_backlinks(transformed_text, coaches)
        transformed_text = replace_with_backlinks(transformed_text, schools)
        transformed_text = replace_with_backlinks(transformed_text, roles)
        # Dates we might not want to backlink, but we can if desired
        body_lines.append("## Original Text with Backlinks")
        body_lines.append("")
        body_lines.append("```")
        body_lines.append(transformed_text)
        body_lines.append("```")
        body_lines.append("")
    
    body_lines.extend([
        "## Coaches",
        *([f"- {name}" for name in coaches] or ["- None"]),
        "",
        "## Schools",
        *([f"- {name}" for name in schools] or ["- None"]),
        "",
        "## Dates",
        *([f"- {d}" for d in dates] or ["- None"]),
        "",
        "## Roles",
        *([f"- {r}" for r in roles] or ["- None"]),
        "",
        "## Backlinks",
        *([f"- [[{item}]]" for item in backlinks] or ["- None"]),
        "",
    ])

    return "\n".join(fm_lines + body_lines)


def parse_args() -> argparse.Namespace:
    """Parse required CLI args: --input and --output."""
    parser = argparse.ArgumentParser(
        description="Extract coaching entities from text notes into Markdown."
    )
    parser.add_argument("--input", required=True, help="Path to input text file.")
    parser.add_argument("--output", required=True, help="Path to output Markdown file.")
    parser.add_argument("--no-inline", action="store_true", help="Disable inline backlinks in output.")
    return parser.parse_args()


def main() -> None:
    """Run extraction pipeline from input file to Markdown output file."""
    args = parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    text = in_path.read_text(encoding="utf-8")

    coaches = find_from_static_list(text, COACHES)
    schools = find_from_static_list(text, SCHOOLS)
    dates = find_dates(text)
    roles = find_from_static_list(text, ROLES)

    markdown = build_markdown(
        in_path.name,
        text,
        coaches,
        schools,
        dates,
        roles,
        inline_backlinks=not args.no_inline,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    main()