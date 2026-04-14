#!/usr/bin/env python3

"""Convert a Google Doc to Obsidian-ready markdown with YAML frontmatter."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse


DEMO_DOC_ID = "1DemoDocIdAbCdEfGhIjKlMnOpQrStUvWxYz123456"
DEMO_METADATA = {
    "title": "Demo Project Brief",
    "createdTime": "2026-04-10T15:22:01Z",
    "modifiedTime": "2026-04-13T08:45:19Z",
    "owners": [{"displayName": "Alex Example", "emailAddress": "alex@example.com"}],
}
DEMO_TEXT = """Project Brief

Goal
Ship the Google Docs to Markdown converter this week.

Notes
- Output should be clean in Obsidian.
- Keep dependencies to the Python standard library.
- Add a demo mode for quick validation.
"""

DOC_URL_RE = re.compile(r"/document/(?:u/\d+/)?d/([A-Za-z0-9_-]+)")
DOC_ID_RE = re.compile(r"^[A-Za-z0-9_-]{20,}$")


class ConversionError(RuntimeError):
    """Raised when document conversion cannot complete."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a Google Doc to Obsidian-ready markdown with YAML frontmatter.",
    )
    parser.add_argument(
        "doc",
        nargs="?",
        help="Google Doc ID or URL. Omit when using --demo.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write markdown to a file instead of stdout.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Print sample markdown without calling gog.",
    )
    return parser


def extract_doc_id(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ConversionError("No Google Doc ID or URL was provided.")

    if DOC_ID_RE.fullmatch(candidate):
        return candidate

    parsed = urlparse(candidate)
    if parsed.scheme and parsed.netloc:
        match = DOC_URL_RE.search(parsed.path)
        if match:
            return match.group(1)
        query_id = parse_qs(parsed.query).get("id")
        if query_id and DOC_ID_RE.fullmatch(query_id[0]):
            return query_id[0]

    raise ConversionError(
        "Could not extract a Google Doc ID. Pass a raw doc ID or a docs.google.com URL."
    )


def run_gog_command(args: list[str]) -> str:
    if shutil.which("gog") is None:
        raise ConversionError(
            "The 'gog' CLI is not installed or not on PATH. Install/authenticate gog first."
        )

    command = ["gog", *args]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise ConversionError(
            "The 'gog' CLI is not installed or not on PATH. Install/authenticate gog first."
        ) from exc
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or "").strip()
        if details:
            raise ConversionError(f"gog command failed: {details}") from exc
        raise ConversionError(f"gog command failed with exit code {exc.returncode}.") from exc

    return completed.stdout


def load_doc_metadata(doc_id: str) -> dict[str, Any]:
    raw_json = run_gog_command(["docs", "info", "--json", "--results-only", "--no-input", doc_id])
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ConversionError("gog returned invalid JSON for document metadata.") from exc

    if not isinstance(payload, dict):
        raise ConversionError("gog returned unexpected metadata JSON.")
    return payload


def load_doc_text(doc_id: str) -> str:
    text = run_gog_command(["docs", "cat", "--no-input", doc_id])
    if not text.strip():
        raise ConversionError("The document content is empty.")
    return text.rstrip() + "\n"


def nested_get(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if isinstance(current, list):
            if not part.isdigit():
                return None
            index = int(part)
            if index >= len(current):
                return None
            current = current[index]
            continue
        if not isinstance(current, dict):
            return None
        if part not in current:
            return None
        current = current[part]
    return current


def first_value(data: dict[str, Any], paths: Iterable[str]) -> Any:
    for path in paths:
        value = nested_get(data, path)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def normalize_metadata(metadata: dict[str, Any], doc_id: str) -> dict[str, Any]:
    title = first_value(
        metadata,
        ["title", "name", "document.title", "documentTitle", "properties.title"],
    ) or "Untitled"
    created = first_value(
        metadata,
        [
            "createdTime",
            "creationTime",
            "createdDate",
            "created",
            "file.createdTime",
            "driveFile.createdTime",
            "properties.createdTime",
        ],
    )
    modified = first_value(
        metadata,
        [
            "modifiedTime",
            "modifiedDate",
            "lastModifiedTime",
            "updated",
            "updateTime",
            "file.modifiedTime",
            "driveFile.modifiedTime",
            "properties.modifiedTime",
        ],
    )
    author = first_value(
        metadata,
        [
            "author.displayName",
            "author.name",
            "author.emailAddress",
            "owner.displayName",
            "owner.name",
            "owner.emailAddress",
            "lastModifyingUser.displayName",
            "lastModifyingUser.emailAddress",
            "owners.0.displayName",
            "owners.0.name",
            "owners.0.emailAddress",
            "createdBy.displayName",
            "createdBy.emailAddress",
            "creator.displayName",
            "creator.name",
            "creator.emailAddress",
            "authors.0.displayName",
            "authors.0.name",
            "authors.0.emailAddress",
        ],
    )

    return {
        "title": str(title),
        "google_doc_id": doc_id,
        "google_doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
        "author": str(author) if author is not None else None,
        "created": str(created) if created is not None else None,
        "modified": str(modified) if modified is not None else None,
    }


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    text = str(value)
    escaped = (
        text.replace("\\", "\\\\")
        .replace("\"", "\\\"")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def render_markdown(frontmatter: dict[str, Any], body: str) -> str:
    yaml_lines = ["---"]
    for key, value in frontmatter.items():
        yaml_lines.append(f"{key}: {yaml_scalar(value)}")
    yaml_lines.append("---")
    body_text = body.rstrip() + "\n"
    return "\n".join(yaml_lines) + "\n\n" + body_text


def convert_doc(doc_argument: str) -> str:
    doc_id = extract_doc_id(doc_argument)
    metadata = load_doc_metadata(doc_id)
    frontmatter = normalize_metadata(metadata, doc_id)
    body = load_doc_text(doc_id)
    return render_markdown(frontmatter, body)


def demo_markdown() -> str:
    frontmatter = normalize_metadata(DEMO_METADATA, DEMO_DOC_ID)
    return render_markdown(frontmatter, DEMO_TEXT)


def write_output(markdown: str, output_path: str | None) -> None:
    if output_path:
        path = Path(output_path)
        path.write_text(markdown, encoding="utf-8")
        return
    sys.stdout.write(markdown)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.demo and not args.doc:
        parser.error("the following arguments are required: doc (unless using --demo)")

    try:
        markdown = demo_markdown() if args.demo else convert_doc(args.doc)
        write_output(markdown, args.output)
    except ConversionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
