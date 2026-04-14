#!/usr/bin/env python3
"""
Verification script for google_docs_to_markdown.py.
Runs the tool in demo mode and checks that output contains expected YAML frontmatter and markdown.
"""

import subprocess
import sys
import os

def run_demo():
    """Run the tool with --demo and capture output."""
    script_path = os.path.join(os.path.dirname(__file__), "google_docs_to_markdown.py")
    try:
        result = subprocess.run(
            [sys.executable, script_path, "--demo"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: tool exited with code {e.returncode}")
        print(f"stderr: {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        print("Error: tool timed out.")
        return None

def verify_output(output):
    """Check that output contains required elements."""
    if not output:
        return False, "No output"
    lines = output.split("\n")
    # Check for YAML frontmatter
    if lines[0] != "---":
        return False, "Missing YAML frontmatter start '---'"
    if "---" not in lines[1:]:
        return False, "Missing YAML frontmatter end '---'"
    # Check for expected fields
    if "title:" not in output:
        return False, "Missing title field"
    if "author:" not in output:
        return False, "Missing author field"
    if "source_url:" not in output:
        return False, "Missing source_url field"
    # Check for some markdown content after frontmatter
    if "Meeting with Coach Smith" not in output:
        return False, "Missing expected demo content"
    return True, "All checks passed"

def main():
    print("Running google_docs_to_markdown.py in demo mode...")
    output = run_demo()
    if output is None:
        sys.exit(1)
    print("Output received, verifying...")
    success, message = verify_output(output)
    if success:
        print("✅ Verification passed:", message)
        sys.exit(0)
    else:
        print("❌ Verification failed:", message)
        sys.exit(1)

if __name__ == "__main__":
    main()