from __future__ import annotations

import argparse
from pathlib import Path
import sys

from broadcaster_notes.converter import convert_text, write_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert plain text broadcaster notes into Obsidian-compatible markdown."
    )
    parser.add_argument("input", nargs="?", help="Path to a plain text input file. Reads stdin if omitted.")
    parser.add_argument("--title", help="Optional note title override.")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for generated markdown files when not using --stdout.",
    )
    parser.add_argument(
        "--source",
        default="plain-text",
        help="Source label to include in YAML frontmatter.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print markdown to stdout instead of writing a file.",
    )
    return parser


def read_input(path_arg: str | None) -> str:
    if path_arg:
        return Path(path_arg).read_text(encoding="utf-8")
    return sys.stdin.read()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    text = read_input(args.input)
    if not text.strip():
        parser.error("input was empty")

    if args.stdout:
        sys.stdout.write(convert_text(text, title=args.title, source=args.source))
        return 0

    output_path = write_markdown(
        text,
        output_dir=Path(args.output_dir),
        title=args.title,
        source=args.source,
    )
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())