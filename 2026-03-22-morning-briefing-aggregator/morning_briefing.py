#!/usr/bin/env python3
"""
Morning Briefing Aggregator
Runs existing nightly build tools and combines their outputs into a single markdown report.
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

def run_command(cmd, cwd=None):
    """Run a command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return (
            result.returncode == 0,
            result.stdout.strip(),
            result.stderr.strip()
        )
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 30 seconds"
    except Exception as e:
        return False, "", str(e)

def run_standup(output_format="markdown"):
    """Run the daily standup generator."""
    script_path = Path(__file__).parent.parent / "2026-02-16-daily-standup" / "standup.py"
    if not script_path.exists():
        return None, "Standup script not found"
    cmd = f"python3 {script_path} --output {output_format}"
    success, out, err = run_command(cmd, cwd=script_path.parent)
    if not success:
        return None, f"Standup failed: {err}"
    return out, None

def run_gh_pr_status(format="markdown"):
    """Run the GitHub PR status tool."""
    script_path = Path(__file__).parent.parent / "2026-02-19-github-pr-status" / "gh_pr_status.py"
    if not script_path.exists():
        return None, "GitHub PR status script not found"
    cmd = f"python3 {script_path} --format {format}"
    success, out, err = run_command(cmd, cwd=script_path.parent)
    if not success:
        return None, f"GitHub PR status failed: {err}"
    return out, None

def run_rental_finder(demo=False):
    """Run the rental finder tool."""
    script_path = Path(__file__).parent.parent / "2026-01-30" / "rental_finder.py"
    if not script_path.exists():
        return None, "Rental finder script not found"
    if demo:
        cmd = f"python3 {script_path} --report --demo"
    else:
        cmd = f"python3 {script_path} --report"
    success, out, err = run_command(cmd, cwd=script_path.parent)
    if not success:
        return None, f"Rental finder failed: {err}"
    return out, None

def run_gog_calendar():
    """Run gog calendar today (if gog is available)."""
    cmd = "gog calendar today --format=json"
    success, out, err = run_command(cmd)
    if not success:
        return None, f"gog calendar failed: {err}"
    # TODO: parse JSON and format as markdown
    # For now, just return raw output
    return out, None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate a morning briefing report.")
    parser.add_argument("--demo", action="store_true", help="Run tools in demo mode where possible.")
    parser.add_argument("--output", default="briefing.md", help="Output markdown file path.")
    args = parser.parse_args()

    sections = []
    warnings = []

    # 1. Daily Standup
    print("Running daily standup...")
    standup_out, err = run_standup()
    if standup_out is not None:
        sections.append(("📅 Daily Standup", standup_out))
    else:
        warnings.append(f"Standup skipped: {err}")

    # 2. GitHub PR Status
    print("Running GitHub PR status...")
    pr_out, err = run_gh_pr_status()
    if pr_out is not None:
        sections.append(("🔁 GitHub PR Status", pr_out))
    else:
        warnings.append(f"GitHub PR status skipped: {err}")

    # 3. Rental Alerts
    print("Running rental finder...")
    rental_out, err = run_rental_finder(demo=args.demo)
    if rental_out is not None:
        sections.append(("🏠 Rental Alerts", rental_out))
    else:
        warnings.append(f"Rental finder skipped: {err}")

    # 4. Calendar (optional)
    print("Checking calendar...")
    calendar_out, err = run_gog_calendar()
    if calendar_out is not None:
        sections.append(("📅 Calendar", calendar_out))
    else:
        warnings.append(f"Calendar skipped: {err}")

    # Combine sections
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = f"# Morning Briefing – {timestamp}\n\n"
    for title, body in sections:
        content += f"## {title}\n\n{body}\n\n"

    if warnings:
        content += "## ⚠️ Warnings\n\n"
        for w in warnings:
            content += f"- {w}\n"
        content += "\n"

    # Write output
    with open(args.output, "w") as f:
        f.write(content)
    print(f"Briefing written to {args.output}")

    # Print warnings to stderr
    if warnings:
        print("\nWarnings:", file=sys.stderr)
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)

if __name__ == "__main__":
    main()