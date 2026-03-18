#!/usr/bin/env python3
import subprocess
import sys

cmd = [sys.executable, "calendar_duration_analyzer.py", "--demo", "--date", "2026-03-18", "--days", "2"]
proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

if proc.returncode != 0:
    print("verify failed: analyzer exited non-zero")
    print(proc.stderr)
    sys.exit(1)

required = [
    "Calendar Duration Analyzer",
    "Total meeting time:",
    "Free time:",
    "Number of meetings:",
    "Hourly meeting distribution:",
    "Workday timeline:",
    "Pie (Meeting vs Free):",
]

missing = [s for s in required if s not in proc.stdout]
if missing:
    print("verify failed: missing expected strings")
    for m in missing:
        print(f"- {m}")
    sys.exit(1)

print("verify passed")