#!/usr/bin/env python3
"""Verification script for github_daily_pr_digest.py"""

import subprocess
import json
import sys
import os

SCRIPT = "./github_daily_pr_digest.py"

def run_cmd(args):
    """Run command and capture stdout, stderr, exit code."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"

def test_demo_markdown():
    """Test demo mode with markdown output."""
    print("Testing demo mode (markdown)...")
    code, out, err = run_cmd([SCRIPT, "--demo", "--repos", "owner/repo", "--output", "markdown"])
    if code != 0:
        print(f"  FAILED: exit code {code}")
        print(f"  stderr: {err}")
        return False
    if "# GitHub PR Digest for" not in out:
        print("  FAILED: expected markdown header not found")
        return False
    if "Sample PR" not in out:
        print("  FAILED: demo content missing")
        return False
    print("  OK")
    return True

def test_demo_text():
    """Test demo mode with text output."""
    print("Testing demo mode (text)...")
    code, out, err = run_cmd([SCRIPT, "--demo", "--repos", "owner/repo", "--output", "text"])
    if code != 0:
        print(f"  FAILED: exit code {code}")
        print(f"  stderr: {err}")
        return False
    if "GitHub PR Digest for" not in out:
        print("  FAILED: expected text header not found")
        return False
    print("  OK")
    return True

def test_demo_json():
    """Test demo mode with JSON output."""
    print("Testing demo mode (JSON)...")
    code, out, err = run_cmd([SCRIPT, "--demo", "--repos", "owner/repo", "--output", "json"])
    if code != 0:
        print(f"  FAILED: exit code {code}")
        print(f"  stderr: {err}")
        return False
    try:
        data = json.loads(out)
        assert "date" in data
        assert "repos" in data
        assert "results" in data
        # Check that results keys exist
        for key in ["new", "updated", "merged", "closed", "review_requests"]:
            assert key in data["results"]
        # Ensure at least one demo entry present
        total = sum(len(entries) for entries in data["results"].values())
        assert total > 0
    except (json.JSONDecodeError, AssertionError) as e:
        print(f"  FAILED: invalid JSON or missing fields: {e}")
        return False
    print("  OK")
    return True

def test_date_param():
    """Test date parameter."""
    print("Testing date parameter...")
    code, out, err = run_cmd([SCRIPT, "--demo", "--repos", "owner/repo", "--date", "2026-01-01"])
    if code != 0:
        print(f"  FAILED: exit code {code}")
        print(f"  stderr: {err}")
        return False
    if "2026-01-01" not in out:
        print("  FAILED: date not reflected in output")
        return False
    print("  OK")
    return True

def test_missing_repos():
    """Test error handling when no repos are provided."""
    print("Testing missing repos (expect error)...")
    # Create a temporary empty config file
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt") as f:
        f.write("# empty\n")
        f.flush()
        code, out, err = run_cmd([SCRIPT, "--repos-file", f.name])
        if code == 0:
            print("  FAILED: expected non-zero exit code")
            return False
        if "No repositories configured" not in err:
            print("  FAILED: expected error message missing")
            return False
    print("  OK")
    return True

def main():
    if not os.path.exists(SCRIPT):
        print(f"Error: {SCRIPT} not found")
        sys.exit(1)

    # Make script executable
    os.chmod(SCRIPT, 0o755)

    tests = [
        test_demo_markdown,
        test_demo_text,
        test_demo_json,
        test_date_param,
        test_missing_repos,
    ]

    passed = 0
    failed = 0
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)
    else:
        print("All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()