#!/usr/bin/env python3
"""
Search OpenClaw session JSONL files for matching messages.
"""

import argparse
import datetime as dt
import glob
import json
import os
import re
import sys
import tempfile
from collections import deque
from typing import Any, Deque, Dict, List, Optional


DEFAULT_GLOB = os.path.expanduser("~/.openclaw/agents/main/sessions/*.jsonl")
VALID_ROLES = {"user", "assistant", "system"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search OpenClaw session JSONL files for matching messages."
    )
    parser.add_argument("query", help="String or pattern to search for")
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Enable case-sensitive search (default: case-insensitive)",
    )
    parser.add_argument(
        "--regex",
        action="store_true",
        help="Treat query as a regular expression pattern",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of matches to output (default: 10)",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=1,
        help="Number of lines before/after each match (default: 1)",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--session-id", help="Filter by exact session ID")
    parser.add_argument(
        "--role",
        choices=sorted(VALID_ROLES),
        help="Filter by role",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debugging logs to stderr",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use built-in sample data instead of real session files",
    )
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be >= 1")
    if args.context < 0:
        parser.error("--context must be >= 0")
    return args


def log_verbose(enabled: bool, msg: str) -> None:
    if enabled:
        print(f"[verbose] {msg}", file=sys.stderr)


def shorten_session_id(session_id: str) -> str:
    if not session_id:
        return "unknown"
    if len(session_id) <= 12:
        return session_id
    return f"{session_id[:8]}...{session_id[-4:]}"


def to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def snippet(text: str, width: int = 140) -> str:
    clean = " ".join(text.split())
    if len(clean) <= width:
        return clean
    return clean[: width - 3] + "..."


def human_timestamp(raw: Any) -> str:
    if raw is None:
        return "unknown"
    if isinstance(raw, (int, float)):
        try:
            return dt.datetime.fromtimestamp(raw).isoformat(sep=" ", timespec="seconds")
        except (OverflowError, OSError, ValueError):
            return str(raw)
    text = str(raw).strip()
    if not text:
        return "unknown"
    maybe_iso = text.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(maybe_iso)
        return parsed.isoformat(sep=" ", timespec="seconds")
    except ValueError:
        return text


def compile_matcher(query: str, use_regex: bool, case_sensitive: bool) -> re.Pattern:
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = query if use_regex else re.escape(query)
    return re.compile(pattern, flags)


def extract_content(obj: Dict[str, Any]) -> str:
    if "content" in obj:
        return to_text(obj["content"])
    for key in ("message", "text", "body"):
        if key in obj:
            return to_text(obj[key])
    return ""


def make_demo_file() -> str:
    records = [
        {
            "sessionId": "demo-session-1234567890",
            "timestamp": "2026-03-16T09:00:00Z",
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "sessionId": "demo-session-1234567890",
            "timestamp": "2026-03-16T09:00:02Z",
            "role": "user",
            "content": "Can you find notes about release health checks?",
        },
        {
            "sessionId": "demo-session-1234567890",
            "timestamp": "2026-03-16T09:00:05Z",
            "role": "assistant",
            "content": "Yes, I found a health check script and a release checklist.",
        },
    ]
    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", prefix="session_search_demo_", delete=False
    )
    with handle:
        for row in records:
            handle.write(json.dumps(row) + "\n")
    return handle.name


def output_text(matches: List[Dict[str, Any]]) -> None:
    if not matches:
        print("No matches found.")
        return
    for idx, match in enumerate(matches, start=1):
        print(f"[{idx}] {match['short_session_id']} | {match['timestamp']} | {match['role']}")
        print(f"  {match['snippet']}")
        if match["before"] or match["after"]:
            print("  Context:")
            for line in match["before"]:
                print(f"    - {line}")
            print(f"    > {match['snippet']}")
            for line in match["after"]:
                print(f"    + {line}")
        print()


def output_json(matches: List[Dict[str, Any]]) -> None:
    print(json.dumps(matches, indent=2, ensure_ascii=False))


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def output_markdown(matches: List[Dict[str, Any]]) -> None:
    print("| Session | Timestamp | Role | Snippet |")
    print("|---|---|---|---|")
    for match in matches:
        print(
            "| "
            + " | ".join(
                [
                    markdown_escape(match["short_session_id"]),
                    markdown_escape(match["timestamp"]),
                    markdown_escape(match["role"]),
                    markdown_escape(match["snippet"]),
                ]
            )
            + " |"
        )


def search_files(
    file_paths: List[str],
    matcher: re.Pattern,
    limit: int,
    context: int,
    role_filter: Optional[str],
    session_filter: Optional[str],
    verbose: bool,
) -> List[Dict[str, Any]]:
    matches: List[Dict[str, Any]] = []
    for path in file_paths:
        if len(matches) >= limit:
            break
        log_verbose(verbose, f"Scanning {path}")
        before_buffer: Deque[str] = deque(maxlen=context)
        pending_after: List[Dict[str, Any]] = []

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line_number, raw_line in enumerate(f, start=1):
                    line = raw_line.rstrip("\n")
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError as err:
                        log_verbose(
                            verbose,
                            f"Malformed JSON in {path}:{line_number}: {err.msg}",
                        )
                        continue

                    role = to_text(obj.get("role", "unknown")) or "unknown"
                    session_id = to_text(obj.get("sessionId")) or "unknown"
                    content = extract_content(obj)

                    for pending in list(pending_after):
                        if pending["remaining_after"] > 0:
                            pending["after"].append(snippet(content))
                            pending["remaining_after"] -= 1
                        if pending["remaining_after"] <= 0:
                            pending_after.remove(pending)

                    before_buffer.append(snippet(content))

                    if role_filter and role != role_filter:
                        continue
                    if session_filter and session_id != session_filter:
                        continue

                    if matcher.search(content):
                        match = {
                            "session_id": session_id,
                            "short_session_id": shorten_session_id(session_id),
                            "timestamp": human_timestamp(obj.get("timestamp")),
                            "role": role,
                            "snippet": snippet(content),
                            "file": path,
                            "line_number": line_number,
                            "before": list(before_buffer)[:-1] if context else [],
                            "after": [],
                            "remaining_after": context,
                        }
                        matches.append(match)
                        if context > 0:
                            pending_after.append(match)
                        if len(matches) >= limit:
                            break
        except OSError as err:
            log_verbose(verbose, f"Could not read {path}: {err}")
            continue
    for match in matches:
        match.pop("remaining_after", None)
    return matches


def main() -> int:
    args = parse_args()

    try:
        matcher = compile_matcher(args.query, args.regex, args.case_sensitive)
    except re.error as err:
        print(f"Invalid regex pattern: {err}", file=sys.stderr)
        return 2

    demo_file = None
    if args.demo:
        demo_file = make_demo_file()
        file_paths = [demo_file]
        log_verbose(args.verbose, f"Using demo file: {demo_file}")
    else:
        file_paths = sorted(glob.glob(DEFAULT_GLOB))

    if not file_paths:
        print(
            f"No session files found at {DEFAULT_GLOB}"
            if not args.demo
            else "No demo file available.",
            file=sys.stderr,
        )
        return 1

    matches = search_files(
        file_paths=file_paths,
        matcher=matcher,
        limit=args.limit,
        context=args.context,
        role_filter=args.role,
        session_filter=args.session_id,
        verbose=args.verbose,
    )

    if args.output_format == "json":
        output_json(matches)
    elif args.output_format == "markdown":
        output_markdown(matches)
    else:
        output_text(matches)

    if demo_file and os.path.exists(demo_file):
        os.unlink(demo_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())