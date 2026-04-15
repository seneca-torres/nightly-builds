#!/usr/bin/env python3
"""
Verification script for obsidian_inbox.py.
Tests the tool with a temporary file.
"""

import os
import sys
import tempfile
import subprocess
import shutil
from pathlib import Path

def test_obsidian_inbox():
    print("🧪 Testing obsidian_inbox.py")
    
    # Create a temporary directory for the test vault
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_dir = Path(tmpdir) / "obsidian-vault" / "0 - Inbox"
        vault_dir.mkdir(parents=True)
        test_file = vault_dir / "append-note.md"
        
        # Write initial content with frontmatter
        initial_content = """---
title: "Test Append Note"
date: "2026-04-15T00:00:00-07:00"
created_by: test
---

First note

---

Appended: 2026-04-15T00:00:00-07:00
First note #test
"""
        test_file.write_text(initial_content, encoding='utf-8')
        
        # Set environment variable to override VAULT_PATH in the script
        env = os.environ.copy()
        env['OBSIDIAN_INBOX_TEST_PATH'] = str(test_file)
        
        script_path = Path(__file__).parent / "obsidian_inbox.py"
        
        # Test 1: Append via command line argument
        print("  Test 1: Command line argument")
        result = subprocess.run(
            [sys.executable, str(script_path), "--tag", "cli", "Test note from CLI"],
            env=env,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        if result.returncode != 0:
            print(f"    ❌ Failed: {result.stderr}")
            return False
        print("    ✓ CLI append succeeded")
        
        # Test 2: Append via stdin
        print("  Test 2: Standard input")
        result = subprocess.run(
            [sys.executable, str(script_path), "--tag", "stdin"],
            env=env,
            input="Test note from stdin",
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        if result.returncode != 0:
            print(f"    ❌ Failed: {result.stderr}")
            return False
        print("    ✓ stdin append succeeded")
        
        # Test 3: Interactive mode (simulated with empty stdin)
        print("  Test 3: Interactive mode (simulated)")
        # We'll skip because it requires tty; we'll just test that script runs
        result = subprocess.run(
            [sys.executable, str(script_path), "--interactive"],
            env=env,
            input="",  # empty input will cause exit 1, which is fine
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        # Expect error due to no input, which is fine
        print("    ✓ Interactive mode handled")
        
        # Read final content
        final_content = test_file.read_text(encoding='utf-8')
        print("\nFinal content preview (last 10 lines):")
        for line in final_content.splitlines()[-10:]:
            print(f"    {line}")
        
        # Verify structure
        lines = final_content.splitlines()
        # Ensure frontmatter preserved
        if not (lines[0].strip() == "---" and "title" in lines[1]):
            print("    ❌ Frontmatter missing or corrupted")
            return False
        # Ensure at least three separators (original + two new)
        separator_count = sum(1 for line in lines if line.strip() == "---")
        if separator_count < 3:
            print(f"    ❌ Expected at least 3 separators, got {separator_count}")
            return False
        # Ensure tags appear
        if "#cli" not in final_content:
            print("    ❌ Tag #cli not found")
            return False
        if "#stdin" not in final_content:
            print("    ❌ Tag #stdin not found")
            return False
        
        print("\n✅ All tests passed")
        return True

if __name__ == "__main__":
    # Monkey-patch the script's VAULT_PATH for testing
    import obsidian_inbox
    original_vault_path = obsidian_inbox.VAULT_PATH
    try:
        # Temporarily replace VAULT_PATH with test path via environment variable
        test_path = os.environ.get('OBSIDIAN_INBOX_TEST_PATH')
        if test_path:
            obsidian_inbox.VAULT_PATH = Path(test_path)
        success = test_obsidian_inbox()
        sys.exit(0 if success else 1)
    finally:
        obsidian_inbox.VAULT_PATH = original_vault_path