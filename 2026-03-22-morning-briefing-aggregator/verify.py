#!/usr/bin/env python3
"""
Verification script for morning_briefing.py.
Runs the tool in demo mode and checks that output files are created.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_verification():
    script_dir = Path(__file__).parent
    briefing_script = script_dir / "morning_briefing.py"
    if not briefing_script.exists():
        print("❌ morning_briefing.py not found")
        return False

    # Run with --demo
    cmd = [sys.executable, str(briefing_script), "--demo", "--output", "briefing_demo.md"]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir)

    if result.returncode != 0:
        print(f"❌ morning_briefing.py exited with code {result.returncode}")
        print("stdout:", result.stdout)
        print("stderr:", result.stderr)
        return False

    # Check that output file exists and has content
    output_file = script_dir / "briefing_demo.md"
    if not output_file.exists():
        print("❌ Output file briefing_demo.md not created")
        return False

    content = output_file.read_text()
    if len(content.strip()) == 0:
        print("❌ Output file is empty")
        return False

    print(f"✅ Verification passed: {output_file} ({len(content)} chars)")
    print("--- Sample of output ---")
    print(content[:500])
    print("---")
    return True

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)