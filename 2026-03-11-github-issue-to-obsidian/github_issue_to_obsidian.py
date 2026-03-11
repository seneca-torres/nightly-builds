#!/usr/bin/env python3
"""Fetch a GitHub issue with gh CLI and create an Obsidian note."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a GitHub issue via gh CLI and create an Obsidian markdown note."
    )
    parser.add_argument("--url", help="Full GitHub issue URL, e.g. https://github.com/owner/repo/issues/123")
    parser.add_argument("--repo", help="Repository in owner/repo format")
    parser.add_argument("--issue", type=int, help="Issue number")
    parser.add_argument(
        "--output-dir",
        default="~/obsidian-vault/",
        help="Output directory for markdown file (default: ~/obsidian-vault/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without writing files",
    )
    return parser.parse_args()


def parse_issue_url(url: str) -> tuple[str, int]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc != "github.com":
        raise ValueError("URL must be a GitHub issue URL on github.com")

    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 4 or parts[2] != "issues":
        raise ValueError("URL must look like https://github.com/owner/repo/issues/123")

    owner, repo, _, issue_str = parts[:4]
    if not owner or not repo or not issue_str.isdigit():
        raise ValueError("URL must contain valid owner/repo/issues/<number>")

    issue_num = int(issue_str)
    if issue_num <= 0:
        raise ValueError("Issue number must be a positive integer")

    return f"{owner}/{repo}", issue_num


def validate_repo(repo: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo or ""):
        raise ValueError("--repo must be in owner/repo format")
    return repo


def slugify_title(title: str, max_len: int = 50) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("-")
    return slug or "untitled"


def run_gh_issue_view(repo: str, issue: int) -> dict:
    fields = [
        "title",
        "body",
        "number",
        "state",
        "createdAt",
        "updatedAt",
        "assignees",
        "labels",
        "milestone",
        "url",
    ]
    cmd = ["gh", "issue", "view", str(issue), "--repo", repo, "--json", ",".join(fields)]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: 'gh' CLI is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        print(f"Error: gh command failed: {detail}", file=sys.stderr)
        sys.exit(1)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"Error: failed to parse gh JSON output: {exc}", file=sys.stderr)
        sys.exit(1)


def yaml_quote(value: str) -> str:
    escaped = (value or "").replace("'", "''")
    return f"'{escaped}'"


def yaml_list_str(items: list[str]) -> str:
    return "[" + ", ".join(yaml_quote(i) for i in items) + "]"


def build_markdown(issue_data: dict, repo: str) -> str:
    assignees = [a.get("login", "") for a in issue_data.get("assignees", []) if a.get("login")]
    labels = [l.get("name", "") for l in issue_data.get("labels", []) if l.get("name")]
    milestone = ""
    if issue_data.get("milestone") and issue_data["milestone"].get("title"):
        milestone = issue_data["milestone"]["title"]

    title = issue_data.get("title", "")
    body = issue_data.get("body", "") or ""

    lines = [
        "---",
        f"title: {yaml_quote(title)}",
        "source: 'github'",
        f"repo: {yaml_quote(repo)}",
        f"issue_number: {issue_data.get('number')}",
        f"state: {yaml_quote(issue_data.get('state', ''))}",
        f"created_at: {yaml_quote(issue_data.get('createdAt', ''))}",
        f"updated_at: {yaml_quote(issue_data.get('updatedAt', ''))}",
        f"assignees: {yaml_list_str(assignees)}",
        f"labels: {yaml_list_str(labels)}",
        f"milestone: {yaml_quote(milestone)}",
        f"url: {yaml_quote(issue_data.get('url', ''))}",
        "---",
        "",
        body,
        "",
        "## Comments",
        "No comments fetched yet.",
        "",
    ]
    return "\n".join(lines)


def resolve_repo_issue(args: argparse.Namespace) -> tuple[str, int]:
    if args.url:
        if args.repo or args.issue:
            raise ValueError("Use either --url OR both --repo and --issue, not both.")
        return parse_issue_url(args.url)

    if args.repo and args.issue is not None:
        if args.issue <= 0:
            raise ValueError("--issue must be a positive integer")
        return validate_repo(args.repo), int(args.issue)

    raise ValueError("Provide --url OR both --repo and --issue.")


def choose_output_path(output_dir: Path, filename: str, dry_run: bool) -> Path:
    path = output_dir / filename
    if not path.exists():
        return path

    if dry_run:
        timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        alt = output_dir / f"{path.stem}-{timestamp}{path.suffix}"
        print(f"File exists: {path}")
        print(f"Dry-run auto-rename target: {alt}")
        return alt

    while True:
        response = input(f"File already exists: {path}\nOverwrite? [y/N] ").strip().lower()
        if response in {"y", "yes"}:
            return path
        if response in {"", "n", "no"}:
            timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            alt = output_dir / f"{path.stem}-{timestamp}{path.suffix}"
            print(f"Using auto-renamed file: {alt}")
            return alt
        print("Please answer y or n.")


def main() -> int:
    args = parse_args()

    try:
        repo, issue_number = resolve_repo_issue(args)
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    issue_data = run_gh_issue_view(repo, issue_number)

    slug = slugify_title(issue_data.get("title", ""))
    owner_repo = repo.replace("/", "-")
    filename = f"GitHub - {owner_repo}-#{issue_number} - {slug}.md"

    output_dir = Path(os.path.expanduser(args.output_dir)).resolve()
    output_path = choose_output_path(output_dir, filename, args.dry_run)
    markdown = build_markdown(issue_data, repo)

    if args.dry_run:
        print(f"[DRY RUN] Would create: {output_path}")
        print("[DRY RUN] Content preview:\n")
        print(markdown)
        return 0

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        print(f"Error writing file: {exc}", file=sys.stderr)
        return 1

    print(f"Created Obsidian note: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())