#!/usr/bin/env python3
"""Git Activity Report CLI.

Scans a root directory for git repositories and builds a report of commits
within the past N days.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Tuple, Optional


RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"


@dataclass
class Commit:
    repo: str
    sha: str
    author_name: str
    author_email: str
    authored_at: datetime
    message: str

    @property
    def day(self) -> str:
        return self.authored_at.date().isoformat()


@dataclass
class RepoReport:
    name: str
    path: str
    commits: List[Commit]
    error: Optional[str] = None


@dataclass
class Report:
    root: str
    since: str
    days: int
    generated_at: str
    total_commits: int
    repos: List[RepoReport]


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Git activity report across repositories."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back for commits (default: 7).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        help="Output format (text, markdown, json).",
    )
    parser.add_argument(
        "--repos",
        default="",
        help=(
            "Comma-separated list of repo names or paths. "
            "If omitted, scan all repos under ~/clawd."
        ),
    )
    parser.add_argument(
        "--root",
        default=str(Path.home() / "clawd"),
        help="Root directory to scan (default: ~/clawd).",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Write output to a file instead of stdout.",
    )
    return parser.parse_args(argv)


def find_git_repos(root: Path) -> List[Path]:
    if not root.exists():
        return []
    repos: List[Path] = []
    for current_root, dirs, _ in os.walk(root):
        if ".git" in dirs:
            repos.append(Path(current_root))
            # Do not descend into subdirectories of a git repo
            dirs[:] = []
            continue
        # Skip common large or irrelevant folders if encountered
        for skip in ["node_modules", ".venv", ".tox", "dist", "build"]:
            if skip in dirs:
                dirs.remove(skip)
    return repos


def resolve_repos(root: Path, repo_arg: str) -> Tuple[List[Path], List[str]]:
    if not repo_arg.strip():
        return find_git_repos(root), []

    repos: List[Path] = []
    errors: List[str] = []
    for raw in repo_arg.split(","):
        item = raw.strip()
        if not item:
            continue
        candidate = Path(item).expanduser()
        if not candidate.exists():
            candidate = root / item
        if candidate.exists():
            repos.append(candidate)
        else:
            errors.append(item)
    return repos, errors


def run_git(repo: Path, args: List[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            args=["git", *args],
            returncode=1,
            stdout="",
            stderr="git not found on PATH",
        )


def is_git_repo(repo: Path) -> bool:
    result = run_git(repo, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0


def get_commits(repo: Path, since: datetime) -> Tuple[List[Commit], Optional[str]]:
    since_arg = since.isoformat()
    pretty = f"%H{FIELD_SEP}%an{FIELD_SEP}%ae{FIELD_SEP}%ad{FIELD_SEP}%s{RECORD_SEP}"
    result = run_git(
        repo,
        [
            "log",
            f"--since={since_arg}",
            "--date=iso-strict",
            f"--pretty=format:{pretty}",
        ],
    )

    if result.returncode != 0:
        return [], result.stderr.strip() or "git log failed"

    output = result.stdout.strip()
    if not output:
        return [], None

    commits: List[Commit] = []
    for record in output.split(RECORD_SEP):
        if not record.strip():
            continue
        parts = record.split(FIELD_SEP)
        if len(parts) != 5:
            continue
        sha, name, email, authored_at, message = parts
        try:
            authored_dt = datetime.fromisoformat(authored_at)
        except ValueError:
            continue
        commits.append(
            Commit(
                repo=repo.name,
                sha=sha,
                author_name=name,
                author_email=email,
                authored_at=authored_dt,
                message=message,
            )
        )

    return commits, None


def build_report(root: Path, days: int, repos: List[Path]) -> Report:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    repo_reports: List[RepoReport] = []
    total_commits = 0

    for repo in sorted(repos):
        if not is_git_repo(repo):
            repo_reports.append(
                RepoReport(name=repo.name, path=str(repo), commits=[], error="Not a git repository")
            )
            continue
        commits, error = get_commits(repo, since)
        total_commits += len(commits)
        repo_reports.append(
            RepoReport(name=repo.name, path=str(repo), commits=commits, error=error)
        )

    return Report(
        root=str(root),
        since=since.isoformat(),
        days=days,
        generated_at=now.isoformat(),
        total_commits=total_commits,
        repos=repo_reports,
    )


def format_text(report: Report) -> str:
    lines: List[str] = []
    lines.append("Git Activity Report")
    lines.append("=" * 20)
    lines.append(f"Root: {report.root}")
    lines.append(f"Days: {report.days}")
    lines.append(f"Since: {report.since}")
    lines.append(f"Generated: {report.generated_at}")
    lines.append("")
    lines.append(f"Total commits: {report.total_commits}")
    lines.append("")

    lines.append("By repository:")
    for repo in report.repos:
        if repo.error:
            lines.append(f"- {repo.name}: error: {repo.error}")
            continue
        lines.append(f"- {repo.name}: {len(repo.commits)} commits")
    lines.append("")

    day_groups: Dict[str, List[Commit]] = defaultdict(list)
    author_counts: Dict[str, int] = defaultdict(int)

    for repo in report.repos:
        for commit in repo.commits:
            day_groups[commit.day].append(commit)
            author_key = f"{commit.author_name} <{commit.author_email}>"
            author_counts[author_key] += 1

    if not day_groups:
        lines.append("No commits found in the specified timeframe.")
        return "\n".join(lines)

    lines.append("Commits by day:")
    for day in sorted(day_groups.keys()):
        lines.append(f"- {day} ({len(day_groups[day])} commits)")
        for commit in sorted(day_groups[day], key=lambda c: c.authored_at):
            timestamp = commit.authored_at.isoformat()
            lines.append(f"  [{timestamp}] {commit.repo} - {commit.message} ({commit.author_name})")
    lines.append("")

    lines.append("Author stats:")
    for author, count in sorted(author_counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- {author}: {count}")
    lines.append("")

    return "\n".join(lines)


def format_markdown(report: Report) -> str:
    lines: List[str] = []
    lines.append("# Git Activity Report")
    lines.append("")
    lines.append(f"- **Root:** {report.root}")
    lines.append(f"- **Days:** {report.days}")
    lines.append(f"- **Since:** {report.since}")
    lines.append(f"- **Generated:** {report.generated_at}")
    lines.append("")
    lines.append(f"## Total commits: {report.total_commits}")
    lines.append("")

    lines.append("## Breakdown by repository")
    lines.append("")
    for repo in report.repos:
        if repo.error:
            lines.append(f"- **{repo.name}**: error: {repo.error}")
        else:
            lines.append(f"- **{repo.name}**: {len(repo.commits)} commits")
    lines.append("")

    day_groups: Dict[str, List[Commit]] = defaultdict(list)
    author_counts: Dict[str, int] = defaultdict(int)

    for repo in report.repos:
        for commit in repo.commits:
            day_groups[commit.day].append(commit)
            author_key = f"{commit.author_name} <{commit.author_email}>"
            author_counts[author_key] += 1

    if not day_groups:
        lines.append("No commits found in the specified timeframe.")
        return "\n".join(lines)

    lines.append("## Commits grouped by day")
    lines.append("")
    for day in sorted(day_groups.keys()):
        lines.append(f"### {day} ({len(day_groups[day])} commits)")
        for commit in sorted(day_groups[day], key=lambda c: c.authored_at):
            timestamp = commit.authored_at.isoformat()
            lines.append(f"- `{timestamp}` **{commit.repo}** — {commit.message} ({commit.author_name})")
        lines.append("")

    lines.append("## Author stats")
    lines.append("")
    for author, count in sorted(author_counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- **{author}**: {count}")
    lines.append("")

    return "\n".join(lines)


def format_json(report: Report) -> str:
    data = asdict(report)
    data["repos"] = [
        {
            **asdict(repo),
            "commits": [
                {
                    **asdict(commit),
                    "authored_at": commit.authored_at.isoformat(),
                }
                for commit in repo.commits
            ],
        }
        for repo in report.repos
    ]
    return json.dumps(data, indent=2)


def write_output(content: str, output_path: str) -> None:
    if not output_path:
        print(content)
        return
    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if args.days < 0:
        print("--days must be >= 0", file=sys.stderr)
        return 2

    root = Path(args.root).expanduser()
    repos, missing = resolve_repos(root, args.repos)

    if missing:
        print(f"Warning: repo(s) not found: {', '.join(missing)}", file=sys.stderr)

    if not repos:
        print("No repositories found.", file=sys.stderr)
        return 1

    report = build_report(root, args.days, repos)

    if args.format == "text":
        content = format_text(report)
    elif args.format == "markdown":
        content = format_markdown(report)
    else:
        content = format_json(report)

    write_output(content, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
