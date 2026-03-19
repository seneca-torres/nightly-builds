#!/usr/bin/env python3
"""Generate a daily GitHub PR digest across configured repositories."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple


SECTIONS = [
    ("new", "New PRs"),
    ("updated", "Updated PRs"),
    ("merged", "Merged PRs"),
    ("closed", "Closed PRs"),
    ("review_requests", "Review Requests"),
]


@dataclass
class PRDigestEntry:
    repo: str
    number: int
    title: str
    author: str
    status: str  # open, merged, closed
    labels: List[str]
    assignees: List[str]
    link: str
    section: str  # one of SECTIONS keys
    updated_at: str  # ISO format

    def to_dict(self) -> dict:
        return asdict(self)


class GitHubDailyPRDigest:
    def __init__(self, repos: List[str], date: dt.date, demo: bool = False):
        self.repos = repos
        self.date = date
        self.demo = demo
        self.gh_path = shutil.which("gh")
        self.results: Dict[str, List[PRDigestEntry]] = {key: [] for key, _ in SECTIONS}

    def run(self):
        if not self.gh_path and not self.demo:
            print("Warning: gh CLI not found. Skipping real data.", file=sys.stderr)
            self.demo = True

        for repo in self.repos:
            self.process_repo(repo)

    def process_repo(self, repo: str):
        if self.demo:
            self.add_demo_entries(repo)
            return

        # Calculate date range for the day (local time)
        start = dt.datetime.combine(self.date, dt.time.min).isoformat() + "Z"
        end = dt.datetime.combine(self.date, dt.time.max).isoformat() + "Z"

        # Fetch PRs created on date
        self.fetch_prs(repo, "created", start, end, "new")
        # Fetch PRs updated on date
        self.fetch_prs(repo, "updated", start, end, "updated")
        # Fetch PRs merged on date
        self.fetch_prs(repo, "merged", start, end, "merged")
        # Fetch PRs closed on date (excluding merged)
        self.fetch_prs(repo, "closed", start, end, "closed")
        # Fetch PRs where review requested
        self.fetch_review_requests(repo)

    def fetch_prs(self, repo: str, filter_type: str, start: str, end: str, section: str):
        """Fetch PRs using gh pr list with search filter."""
        # Build search query
        query = f"repo:{repo} {filter_type}:{start}..{end}"
        cmd = [self.gh_path, "pr", "list", "--json", "number,title,author,labels,assignees,state,url,updatedAt", "--search", query]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"Warning: gh command failed for {repo} {filter_type}: {result.stderr}", file=sys.stderr)
                return
            data = json.loads(result.stdout)
            for item in data:
                entry = PRDigestEntry(
                    repo=repo,
                    number=item["number"],
                    title=item["title"],
                    author=item["author"]["login"] if item.get("author") else "unknown",
                    status=item["state"].lower(),
                    labels=[label["name"] for label in item.get("labels", [])],
                    assignees=[assignee["login"] for assignee in item.get("assignees", [])],
                    link=item["url"],
                    section=section,
                    updated_at=item["updatedAt"]
                )
                self.results[section].append(entry)
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            print(f"Error processing {repo} {filter_type}: {e}", file=sys.stderr)

    def fetch_review_requests(self, repo: str):
        """Fetch PRs where the current user is requested for review."""
        # Use gh pr list --review-requested @me
        cmd = [self.gh_path, "pr", "list", "--repo", repo, "--review-requested", "@me",
               "--json", "number,title,author,labels,assignees,state,url,updatedAt"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"Warning: gh review request failed for {repo}: {result.stderr}", file=sys.stderr)
                return
            data = json.loads(result.stdout)
            for item in data:
                entry = PRDigestEntry(
                    repo=repo,
                    number=item["number"],
                    title=item["title"],
                    author=item["author"]["login"] if item.get("author") else "unknown",
                    status=item["state"].lower(),
                    labels=[label["name"] for label in item.get("labels", [])],
                    assignees=[assignee["login"] for assignee in item.get("assignees", [])],
                    link=item["url"],
                    section="review_requests",
                    updated_at=item["updatedAt"]
                )
                self.results["review_requests"].append(entry)
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            print(f"Error processing review requests for {repo}: {e}", file=sys.stderr)

    def add_demo_entries(self, repo: str):
        """Add sample demo data for testing."""
        demo_entries = [
            PRDigestEntry(repo, 123, "Sample PR", "octocat", "open", ["bug"], ["user1"], f"https://github.com/{repo}/pull/123", "new", "2026-03-19T10:00:00Z"),
            PRDigestEntry(repo, 456, "Another PR", "victorres11", "merged", ["enhancement"], [], f"https://github.com/{repo}/pull/456", "merged", "2026-03-19T15:30:00Z"),
            PRDigestEntry(repo, 789, "Fix bug", "seneca-torres", "open", [], ["victorres11"], f"https://github.com/{repo}/pull/789", "review_requests", "2026-03-19T12:00:00Z"),
        ]
        for entry in demo_entries:
            self.results[entry.section].append(entry)

    def output_markdown(self) -> str:
        """Generate markdown report."""
        lines = [f"# GitHub PR Digest for {self.date.isoformat()}", ""]
        total = sum(len(entries) for entries in self.results.values())
        lines.append(f"**Total PRs:** {total}")
        lines.append("")

        for key, heading in SECTIONS:
            entries = self.results[key]
            if not entries:
                continue
            lines.append(f"## {heading} ({len(entries)})")
            lines.append("")
            for entry in entries:
                labels = ", ".join(f"`{l}`" for l in entry.labels) if entry.labels else "*none*"
                assignees = ", ".join(f"@{a}" for a in entry.assignees) if entry.assignees else "*unassigned*"
                lines.append(f"- **[{entry.repo}#{entry.number}]({entry.link})** {entry.title}")
                lines.append(f"  - Author: @{entry.author} | Status: {entry.status} | Labels: {labels} | Assignees: {assignees}")
                lines.append(f"  - Updated: {entry.updated_at}")
                lines.append("")
            lines.append("")

        return "\n".join(lines).strip()

    def output_text(self) -> str:
        """Generate plain text report."""
        lines = [f"GitHub PR Digest for {self.date.isoformat()}", ""]
        for key, heading in SECTIONS:
            entries = self.results[key]
            if not entries:
                continue
            lines.append(f"=== {heading} ({len(entries)}) ===")
            for entry in entries:
                lines.append(f"  {entry.repo}#{entry.number}: {entry.title}")
                lines.append(f"    Author: @{entry.author}, Status: {entry.status}")
                lines.append(f"    Link: {entry.link}")
                lines.append("")
        return "\n".join(lines).strip()

    def output_json(self) -> str:
        """Generate JSON report."""
        output = {
            "date": self.date.isoformat(),
            "repos": self.repos,
            "results": {key: [entry.to_dict() for entry in entries] for key, entries in self.results.items()}
        }
        return json.dumps(output, indent=2)


def load_repos_from_file(path: str) -> List[str]:
    """Load repos from a file, one per line."""
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        lines = f.readlines()
    repos = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
    return repos


def main():
    parser = argparse.ArgumentParser(description="Generate daily GitHub PR digest")
    parser.add_argument("--repos-file", default=os.path.expanduser("~/.github_daily_pr_digest/repos.txt"),
                        help="Path to repos list file (default: ~/.github_daily_pr_digest/repos.txt)")
    parser.add_argument("--repos", nargs="+", help="Space-separated list of repos (overrides file)")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--output", choices=["markdown", "text", "json"], default="markdown",
                        help="Output format")
    parser.add_argument("--demo", action="store_true", help="Use demo data (no API calls)")
    args = parser.parse_args()

    # Determine repos
    if args.repos:
        repos = args.repos
    else:
        repos = load_repos_from_file(args.repos_file)
        if not repos:
            print("No repositories configured. Use --repos or create config file.", file=sys.stderr)
            sys.exit(1)

    # Determine date
    if args.date:
        try:
            date = dt.datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD.", file=sys.stderr)
            sys.exit(1)
    else:
        date = dt.date.today()

    digest = GitHubDailyPRDigest(repos, date, demo=args.demo)
    digest.run()

    if args.output == "markdown":
        print(digest.output_markdown())
    elif args.output == "text":
        print(digest.output_text())
    elif args.output == "json":
        print(digest.output_json())


if __name__ == "__main__":
    main()