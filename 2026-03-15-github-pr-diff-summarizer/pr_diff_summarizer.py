#!/usr/bin/env python3
"""Fetch and summarize a GitHub PR diff as Markdown."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SUSPICIOUS_PATTERNS = ("TODO", "FIXME", "console.log")
DEFAULT_LARGE_THRESHOLD = 500
DEMO_TITLE = "Demo PR: Offline sample diff"
DEMO_URL = "https://github.com/example/repo/pull/123"


@dataclass
class FileStat:
    path: str
    status: str = "modified"
    additions: int = 0
    deletions: int = 0
    binary: bool = False
    suspicious: dict[str, int] = field(default_factory=dict)


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def run_gh(args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["gh"] + args,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        die("`gh` CLI is not installed or not on PATH.")
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or "unknown gh error"
        die(stderr)
    return proc.stdout


def parse_pr_ref(arg1: str, arg2: str | None) -> tuple[str, int]:
    if arg2 is not None:
        repo = arg1.strip()
        if not re.fullmatch(r"[^/\s]+/[^/\s]+", repo):
            die("repo must look like `owner/repo`.")
        try:
            pr_number = int(arg2)
        except ValueError:
            die("PR number must be an integer.")
        return repo, pr_number

    m = re.match(
        r"^https?://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)(?:/.*)?$",
        arg1.strip(),
    )
    if not m:
        die("provide a PR URL or `owner/repo <pr_number>`.")
    repo = f"{m.group(1)}/{m.group(2)}"
    pr_number = int(m.group(3))
    return repo, pr_number


def fetch_pr_meta(repo: str, pr_number: int) -> tuple[str, str]:
    out = run_gh(["pr", "view", "--repo", repo, str(pr_number), "--json", "title,url"])
    try:
        data = json.loads(out)
        return data["title"], data["url"]
    except (json.JSONDecodeError, KeyError):
        die("failed to parse `gh pr view` output.")


def fetch_pr_diff(repo: str, pr_number: int) -> str:
    return run_gh(["pr", "diff", "--repo", repo, str(pr_number)])


def parse_diff(diff_text: str) -> list[FileStat]:
    files: list[FileStat] = []
    cur: FileStat | None = None

    def flush_current() -> None:
        nonlocal cur
        if cur is not None:
            files.append(cur)
            cur = None

    for raw in diff_text.splitlines():
        if raw.startswith("diff --git "):
            flush_current()
            m = re.match(r"^diff --git a/(.*?) b/(.*)$", raw)
            if m:
                old_path, new_path = m.group(1), m.group(2)
                path = new_path if new_path != "/dev/null" else old_path
            else:
                old_path, new_path, path = "", "", "unknown"
            cur = FileStat(path=path)
            continue

        if cur is None:
            continue

        if raw.startswith("new file mode "):
            cur.status = "added"
            continue
        if raw.startswith("deleted file mode "):
            cur.status = "deleted"
            continue
        if raw.startswith("Binary files ") or raw.startswith("GIT binary patch"):
            cur.binary = True
            continue

        if raw.startswith("--- "):
            if raw[4:].strip() == "/dev/null":
                cur.status = "added"
            continue
        if raw.startswith("+++ "):
            if raw[4:].strip() == "/dev/null":
                cur.status = "deleted"
            continue

        if raw.startswith("+") and not raw.startswith("+++"):
            cur.additions += 1
            lower = raw[1:].lower()
            for p in SUSPICIOUS_PATTERNS:
                if p.lower() in lower:
                    cur.suspicious[p] = cur.suspicious.get(p, 0) + 1
            continue

        if raw.startswith("-") and not raw.startswith("---"):
            cur.deletions += 1

    flush_current()
    return files


def md_escape_cell(s: str) -> str:
    return s.replace("|", r"\|")


def render_markdown(
    title: str,
    url: str,
    files: list[FileStat],
    large_threshold: int = DEFAULT_LARGE_THRESHOLD,
) -> str:
    total_add = sum(f.additions for f in files)
    total_del = sum(f.deletions for f in files)

    lines: list[str] = []
    lines.append("# PR Diff Summary")
    lines.append("")
    lines.append(f"## [{title}]({url})")
    lines.append("")
    lines.append("| File | Status | Additions | Deletions |")
    lines.append("|---|---:|---:|---:|")

    if not files:
        lines.append("| _No files_ | - | 0 | 0 |")
    else:
        for f in files:
            lines.append(
                f"| `{md_escape_cell(f.path)}` | {f.status} | {f.additions} | {f.deletions} |"
            )

    lines.append("")
    lines.append("## Totals")
    lines.append("")
    lines.append(f"- **Files changed:** {len(files)}")
    lines.append(f"- **Total additions:** {total_add}")
    lines.append(f"- **Total deletions:** {total_del}")

    large_files = [f for f in files if (f.additions + f.deletions) > large_threshold]
    if large_files:
        lines.append("")
        lines.append(f"## Large Files (>{large_threshold} lines changed)")
        lines.append("")
        for f in large_files:
            changed = f.additions + f.deletions
            lines.append(f"- `{f.path}` ({changed} changed: +{f.additions}/-{f.deletions})")

    binary_files = [f for f in files if f.binary]
    if binary_files:
        lines.append("")
        lines.append("## Binary Files")
        lines.append("")
        for f in binary_files:
            lines.append(f"- `{f.path}`")

    suspicious_rows: list[tuple[str, str, int]] = []
    for f in files:
        for pat, count in f.suspicious.items():
            suspicious_rows.append((f.path, pat, count))
    if suspicious_rows:
        lines.append("")
        lines.append("## Suspicious Patterns")
        lines.append("")
        lines.append("| File | Pattern | Count |")
        lines.append("|---|---|---:|")
        for path, pat, count in suspicious_rows:
            lines.append(f"| `{md_escape_cell(path)}` | `{pat}` | {count} |")

    return "\n".join(lines) + "\n"


def read_demo_diff(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    die(f"demo diff file not found: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch a GitHub PR diff and summarize it as Markdown."
    )
    parser.add_argument("arg1", nargs="?", help="PR URL or owner/repo")
    parser.add_argument("arg2", nargs="?", help="PR number (when arg1 is owner/repo)")
    parser.add_argument("--demo", action="store_true", help="Use local sample_diff.txt")
    parser.add_argument(
        "--demo-diff",
        default="sample_diff.txt",
        help="Path to sample diff file for demo mode (default: sample_diff.txt)",
    )
    parser.add_argument(
        "--large-threshold",
        type=int,
        default=DEFAULT_LARGE_THRESHOLD,
        help=f"Highlight files with more than this many changed lines (default: {DEFAULT_LARGE_THRESHOLD})",
    )
    args = parser.parse_args()

    if args.demo:
        diff_text = read_demo_diff(Path(args.demo_diff))
        title, url = DEMO_TITLE, DEMO_URL
    else:
        if not args.arg1:
            parser.print_help(sys.stderr)
            raise SystemExit(2)
        repo, pr_number = parse_pr_ref(args.arg1, args.arg2)
        title, url = fetch_pr_meta(repo, pr_number)
        diff_text = fetch_pr_diff(repo, pr_number)

    files = parse_diff(diff_text)
    print(render_markdown(title, url, files, args.large_threshold), end="")


if __name__ == "__main__":
    main()