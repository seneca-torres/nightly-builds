#!/usr/bin/env python3
"""List open GitHub PRs across repos using the gh CLI."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Iterable, List, Dict, Any

DEFAULT_REPOS = [
    "seneca-torres/nightly-builds",
    "victorres11/portfolio",
    "victorres11/coach-database",
    "victorres11/one-play-a-day-app",
    "victorres11/football-data-adhoc",
]

FAIL_STATES = {"ERROR", "FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED"}
PENDING_STATES = {
    "PENDING",
    "IN_PROGRESS",
    "QUEUED",
    "REQUESTED",
    "WAITING",
}
SUCCESS_STATES = {"SUCCESS", "NEUTRAL", "SKIPPED"}


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List open PRs across repos using the GitHub CLI."
    )
    parser.add_argument(
        "--repos",
        help="Comma-separated list of owner/repo entries.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "plain"],
        default="markdown",
        help="Output format (markdown or plain).",
    )
    return parser.parse_args(argv)


def run_gh_pr_list(repo: str) -> List[Dict[str, Any]]:
    cmd = [
        "gh",
        "pr",
        "list",
        "--repo",
        repo,
        "--state",
        "open",
        "--limit",
        "200",
        "--json",
        "number,title,author,url,statusCheckRollup",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        err = result.stderr.strip() or "unknown error"
        print(f"[warn] Skipping {repo}: {err}", file=sys.stderr)
        return []
    try:
        data = json.loads(result.stdout)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        print(f"[warn] Skipping {repo}: invalid JSON from gh", file=sys.stderr)
    return []


def summarize_checks(pr: Dict[str, Any]) -> str:
    checks = pr.get("statusCheckRollup")
    if not checks:
        return "❔ No checks"

    states = []
    for item in checks:
        state = item.get("state")
        if state:
            states.append(state)

    if not states:
        return "❔ No checks"

    if any(state in FAIL_STATES for state in states):
        return "❌ Checks failing"
    if any(state in PENDING_STATES for state in states):
        return "⏳ Checks pending"
    if all(state in SUCCESS_STATES for state in states):
        return "✅ All checks passed"
    return "⚠️ Mixed status"


def collect_prs(repos: Iterable[str]) -> List[Dict[str, Any]]:
    all_prs: List[Dict[str, Any]] = []
    for repo in repos:
        for pr in run_gh_pr_list(repo):
            pr["_repo"] = repo
            all_prs.append(pr)
    return all_prs


def render_markdown(prs: List[Dict[str, Any]]) -> str:
    lines = ["| PR # | Title | Author | Status | Link |", "| --- | --- | --- | --- | --- |"]
    for pr in prs:
        number = pr.get("number", "")
        title = pr.get("title", "").replace("|", "\\|")
        repo = pr.get("_repo", "")
        if repo:
            title = f"[{repo}] {title}"
        author = (pr.get("author") or {}).get("login", "")
        status = summarize_checks(pr)
        url = pr.get("url", "")
        lines.append(f"| {number} | {title} | {author} | {status} | {url} |")
    return "\n".join(lines)


def render_plain(prs: List[Dict[str, Any]]) -> str:
    lines = ["PR#\tTitle\tAuthor\tStatus\tLink"]
    for pr in prs:
        number = pr.get("number", "")
        title = pr.get("title", "")
        repo = pr.get("_repo", "")
        if repo:
            title = f"[{repo}] {title}"
        author = (pr.get("author") or {}).get("login", "")
        status = summarize_checks(pr)
        url = pr.get("url", "")
        lines.append(f"{number}\t{title}\t{author}\t{status}\t{url}")
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    repos = DEFAULT_REPOS
    if args.repos:
        repos = [r.strip() for r in args.repos.split(",") if r.strip()]
        if not repos:
            print("[warn] No valid repos provided, using defaults.", file=sys.stderr)
            repos = DEFAULT_REPOS

    prs = collect_prs(repos)
    prs.sort(key=lambda p: (p.get("_repo", ""), p.get("number", 0)))

    if args.format == "plain":
        output = render_plain(prs)
    else:
        output = render_markdown(prs)

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
