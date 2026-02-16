#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate a daily standup summary for Victor.")
    p.add_argument("--date", help="Target date in YYYY-MM-DD (defaults to yesterday)")
    p.add_argument("--output", choices=["text", "markdown", "json"], default="markdown")
    p.add_argument("--verbose", action="store_true", help="Show full commit messages and memory content")
    return p.parse_args()


def parse_date(date_str: Optional[str]) -> dt.date:
    if date_str:
        return dt.date.fromisoformat(date_str)
    return dt.date.today() - dt.timedelta(days=1)


def date_window(target: dt.date) -> Tuple[str, str]:
    start = dt.datetime.combine(target, dt.time.min)
    end = start + dt.timedelta(days=1)
    return start.isoformat(), end.isoformat()


def read_memory(target: dt.date) -> Tuple[Optional[Path], Optional[str]]:
    path = Path.home() / "clawd" / "memory" / "daily" / f"{target.isoformat()}.md"
    if not path.exists():
        return None, None
    try:
        return path, path.read_text(encoding="utf-8")
    except Exception:
        return path, None


def extract_memory_highlights(content: str, verbose: bool) -> List[str]:
    if verbose:
        return [content.strip()] if content.strip() else []

    lines = [ln.strip() for ln in content.splitlines()]
    bullets = [ln for ln in lines if ln.startswith(("- ", "* ", "• "))]
    numbered = [ln for ln in lines if ln[:3].strip().endswith(".") and ln[:3].strip()[:-1].isdigit()]

    picks: List[str] = []
    for ln in bullets + numbered:
        if ln and ln not in picks:
            picks.append(ln)
        if len(picks) >= 5:
            return picks

    for ln in lines:
        if not ln or ln.startswith("#"):
            continue
        picks.append(ln)
        if len(picks) >= 5:
            break
    return picks


def find_git_repos(base: Path) -> List[Path]:
    repos: List[Path] = []
    for root, dirs, _files in os.walk(base):
        if ".git" in dirs:
            repos.append(Path(root))
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d != ".git"]
    return repos


def git_commits_for_date(repo: Path, target: dt.date, verbose: bool) -> List[Dict[str, str]]:
    since, until = date_window(target)
    fmt = "%H%x1f%an%x1f%ad%x1f%B" if verbose else "%H%x1f%an%x1f%ad%x1f%s"
    cmd = [
        "git",
        "-C",
        str(repo),
        "log",
        f"--since={since}",
        f"--until={until}",
        "--date=iso",
        f"--pretty=format:{fmt}%x1e",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception:
        return []
    if res.returncode != 0 or not res.stdout.strip():
        return []

    commits: List[Dict[str, str]] = []
    for rec in res.stdout.split("\x1e"):
        if not rec.strip():
            continue
        parts = rec.split("\x1f")
        if len(parts) < 4:
            continue
        sha, author, date_str, msg = parts[0], parts[1], parts[2], parts[3].strip()
        commits.append({"sha": sha, "author": author, "date": date_str, "message": msg})
    return commits


def parse_timestamp(value: Any) -> Optional[dt.datetime]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return dt.datetime.fromtimestamp(value)
        except Exception:
            return None
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return None
        v = v.replace("Z", "+00:00")
        try:
            return dt.datetime.fromisoformat(v)
        except Exception:
            pass
        # Fallback: date-only
        try:
            d = dt.date.fromisoformat(v[:10])
            return dt.datetime.combine(d, dt.time.min)
        except Exception:
            return None
    return None


def cron_runs_for_date(target: dt.date) -> List[Dict[str, Any]]:
    base = Path.home() / ".clawdbot" / "cron_runs"
    if not base.exists():
        return []

    runs: List[Dict[str, Any]] = []
    for path in sorted(base.glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue

            ts = None
            for key in ("timestamp", "started_at", "run_at", "time", "datetime"):
                if key in obj:
                    ts = parse_timestamp(obj.get(key))
                    if ts:
                        break
            if not ts:
                continue
            if ts.date() != target:
                continue

            name = (
                obj.get("job")
                or obj.get("name")
                or obj.get("task")
                or obj.get("command")
                or obj.get("cron")
                or "(unknown)"
            )

            status = "unknown"
            if isinstance(obj.get("success"), bool):
                status = "success" if obj.get("success") else "failure"
            elif "status" in obj:
                status = str(obj.get("status"))
            elif "exit_code" in obj:
                status = "success" if obj.get("exit_code") == 0 else "failure"
            elif "result" in obj:
                status = str(obj.get("result"))

            runs.append({
                "name": str(name),
                "status": status,
                "timestamp": ts.isoformat(),
            })
    return runs


def derive_active_projects(memory_content: Optional[str], git_activity: Dict[str, List[Dict[str, str]]]) -> List[str]:
    projects = set()
    for repo in git_activity:
        projects.add(Path(repo).name)

    if memory_content:
        for line in memory_content.splitlines():
            line = line.strip()
            if line.lower().startswith("project:"):
                name = line.split(":", 1)[1].strip()
                if name:
                    projects.add(name)
            if "#" in line:
                for token in line.split():
                    if token.startswith("#") and len(token) > 1:
                        projects.add(token[1:])
    return sorted(p for p in projects if p)


def render_markdown(target: dt.date, memory: List[str], git_activity: Dict[str, List[Dict[str, str]]], cron_runs: List[Dict[str, Any]], projects: List[str], verbose: bool) -> str:
    out: List[str] = []
    out.append(f"# Daily Standup - {target.isoformat()}")

    out.append("\n## 📝 Memory Highlights")
    if not memory:
        out.append(f"_No memory file found for {target.isoformat()}._")
    else:
        for item in memory:
            if verbose and "\n" in item:
                out.append("```")
                out.append(item)
                out.append("```")
            else:
                out.append(f"- {item}")

    out.append("\n## 💻 Git Activity")
    if not git_activity:
        out.append("_No commits found._")
    else:
        for repo, commits in sorted(git_activity.items()):
            out.append(f"- **{Path(repo).name}** ({len(commits)} commits)")
            for c in commits:
                msg = c["message"].strip()
                if verbose and "\n" in msg:
                    msg = msg.replace("\n", " ").strip()
                out.append(f"  - {c['author']}: {msg}")

    out.append("\n## 🤖 Cron Jobs")
    if not cron_runs:
        out.append("_No cron runs found._")
    else:
        for run in cron_runs:
            out.append(f"- {run['name']} - {run['status']} ({run['timestamp']})")

    out.append("\n## 🎯 Active Projects")
    if not projects:
        out.append("_No active projects detected._")
    else:
        for p in projects:
            out.append(f"- {p}")
    return "\n".join(out)


def render_text(target: dt.date, memory: List[str], git_activity: Dict[str, List[Dict[str, str]]], cron_runs: List[Dict[str, Any]], projects: List[str], verbose: bool) -> str:
    out: List[str] = []
    out.append(f"Daily Standup - {target.isoformat()}")
    out.append("\nMemory Highlights")
    if not memory:
        out.append(f"  No memory file found for {target.isoformat()}.")
    else:
        for item in memory:
            if verbose and "\n" in item:
                out.append(item)
            else:
                out.append(f"  - {item}")

    out.append("\nGit Activity")
    if not git_activity:
        out.append("  No commits found.")
    else:
        for repo, commits in sorted(git_activity.items()):
            out.append(f"  {Path(repo).name} ({len(commits)} commits)")
            for c in commits:
                msg = c["message"].strip().replace("\n", " ")
                out.append(f"    - {c['author']}: {msg}")

    out.append("\nCron Jobs")
    if not cron_runs:
        out.append("  No cron runs found.")
    else:
        for run in cron_runs:
            out.append(f"  - {run['name']} - {run['status']} ({run['timestamp']})")

    out.append("\nActive Projects")
    if not projects:
        out.append("  No active projects detected.")
    else:
        for p in projects:
            out.append(f"  - {p}")
    return "\n".join(out)


def render_json(target: dt.date, memory: List[str], git_activity: Dict[str, List[Dict[str, str]]], cron_runs: List[Dict[str, Any]], projects: List[str]) -> str:
    payload = {
        "date": target.isoformat(),
        "memory_highlights": memory,
        "git_activity": [
            {"repo": Path(repo).name, "path": repo, "commits": commits}
            for repo, commits in sorted(git_activity.items())
        ],
        "cron_jobs": cron_runs,
        "active_projects": projects,
    }
    return json.dumps(payload, indent=2)


def main() -> int:
    args = parse_args()
    target = parse_date(args.date)

    memory_path, memory_content = read_memory(target)
    memory_highlights: List[str] = []
    if memory_content is not None:
        memory_highlights = extract_memory_highlights(memory_content, args.verbose)

    git_base = Path.home() / "clawd"
    repos = find_git_repos(git_base) if git_base.exists() else []
    git_activity: Dict[str, List[Dict[str, str]]] = {}
    for repo in repos:
        commits = git_commits_for_date(repo, target, args.verbose)
        if commits:
            git_activity[str(repo)] = commits

    cron_runs = cron_runs_for_date(target)
    projects = derive_active_projects(memory_content, git_activity)

    if args.output == "markdown":
        print(render_markdown(target, memory_highlights, git_activity, cron_runs, projects, args.verbose))
    elif args.output == "text":
        print(render_text(target, memory_highlights, git_activity, cron_runs, projects, args.verbose))
    else:
        print(render_json(target, memory_highlights, git_activity, cron_runs, projects))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
