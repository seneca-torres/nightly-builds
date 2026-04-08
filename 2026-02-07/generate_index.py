#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class IndexedFile:
    path: str
    name: str
    content: str
    mtime: float | None
    size: int | None


def iter_md_files(root: Path, include_hidden: bool) -> Iterable[Path]:
    for p in root.rglob("*.md"):
        try:
            rel = p.relative_to(root)
        except ValueError:
            rel = p
        if not include_hidden:
            if any(part.startswith(".") for part in rel.parts):
                continue
        if p.is_file():
            yield p


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def to_indexed_file(root: Path, p: Path) -> IndexedFile:
    rel = p.relative_to(root).as_posix()
    st = p.stat()
    return IndexedFile(
        path=rel,
        name=p.name,
        content=read_text(p),
        mtime=float(st.st_mtime),
        size=int(st.st_size),
    )


def build_index(root: Path, include_hidden: bool) -> dict:
    files = [to_indexed_file(root, p) for p in iter_md_files(root, include_hidden)]
    files.sort(key=lambda f: f.path)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "files": [f.__dict__ for f in files],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a JSON index of markdown files for static search.",
    )
    parser.add_argument(
        "--root",
        default=os.path.expanduser("~/clawd/memory"),
        help="Root directory to scan for *.md files (default: %(default)s).",
    )
    parser.add_argument(
        "--output",
        default="memory_index.json",
        help="Output JSON path (default: %(default)s). Use '-' for stdout.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include files under dot-directories (e.g. .git, .obsidian).",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"error: root directory not found: {root}", file=sys.stderr)
        return 2

    index = build_index(root, include_hidden=bool(args.include_hidden))
    out = args.output

    payload = json.dumps(index, ensure_ascii=False, indent=2)
    if out == "-":
        sys.stdout.write(payload)
        sys.stdout.write("\n")
        return 0

    out_path = Path(out)
    out_path.write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

