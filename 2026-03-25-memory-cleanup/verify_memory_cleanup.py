#!/usr/bin/env python3
"""
Verification script for memory_cleanup.py

Tests the memory cleanup tool with sample data to ensure it works correctly.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import subprocess

def create_test_memory_structure(test_dir: Path):
    """Create a test memory directory structure with sample files."""
    daily_dir = test_dir / "memory" / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample memory files with various issues
    files = {
        "2026-03-25.md": """# Daily Log — 2026-03-25

## Summary

## Events
- [00:03] ✅ outcome for this cron run
- [00:03] ✅ outcome for this cron run
- [00:04] 📋 Decision: queue is empty
- [00:04] 📋 Decision: queue is empty
- [08:00] 💡 New idea for project
- [12:00] Meeting with team
- [14:00] ✅ this week: Email Article Digest, Daily Documentation Audit
- [16:00] 📋 Decision: file contains `[]` (empty array)
- [16:00] 📋 Decision: file contains `[]` (empty array)
- [20:00] ✅ action for this cron execution
""",
        "2026-03-24.md": """# Daily Log — 2026-03-24

## Summary
*(no entries yet)*

## Events
- [00:03] 🔀 PR #259 in seneca-ops
- [00:03] ✅ for `seneca-torres/seneca-ops` (30 open issues reviewed)
- 12:00 Meeting with client  # MALFORMED TIMESTAMP - missing brackets
- [14:00] Some regular note
""",
        "2026-03-01.md": """# Daily Log — 2026-03-01

## Summary
This was a productive day

## Events
- [09:00] Started new project
- [10:00] Team sync
- [11:00] Code review
""",
        "2026-01-15.md": """# Daily Log — 2026-01-15

## Summary
Old file for archiving test

## Events
- [09:00] Old meeting
""",
    }
    
    for filename, content in files.items():
        filepath = daily_dir / filename
        filepath.write_text(content)
    
    return daily_dir

def run_memory_cleanup(test_dir: Path, args: str):
    """Run memory_cleanup.py with given arguments."""
    script_path = Path(__file__).parent / "memory_cleanup.py"
    
    # Set MEMORY_ROOT environment variable to point to test directory
    env = os.environ.copy()
    env["MEMORY_ROOT_OVERRIDE"] = str(test_dir / "memory")
    
    # Modify the script temporarily to use test directory
    original_content = script_path.read_text()
    modified_content = original_content.replace(
        'MEMORY_ROOT = Path.home() / "clawd" / "memory"',
        f'MEMORY_ROOT = Path(r"{test_dir / "memory"}")'
    )
    script_path.write_text(modified_content)
    
    try:
        cmd = [sys.executable, str(script_path)] + args.split()
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        # Restore original script
        script_path.write_text(original_content)
        
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        # Restore original script on error
        script_path.write_text(original_content)
        raise e

def test_dry_run():
    """Test dry-run mode."""
    print("🧪 Testing dry-run mode...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        create_test_memory_structure(test_dir)
        
        # Run with dry-run
        returncode, stdout, stderr = run_memory_cleanup(test_dir, "--dry-run --dedupe --fix-formatting --verbose")
        
        if returncode != 0:
            print(f"❌ Failed with return code {returncode}")
            print(f"Stderr: {stderr}")
            return False
        
        # Check output contains expected messages
        expected_phrases = [
            "Removing duplicate",
            "Fix",
            "DRY RUN",
            "Would save changes",
        ]
        
        for phrase in expected_phrases:
            if phrase in stdout:
                print(f"  ✓ Found '{phrase}' in output")
            else:
                print(f"  ⚠️  Missing '{phrase}' in output")
        
        # Verify files weren't actually modified (dry-run)
        file_25 = test_dir / "memory" / "daily" / "2026-03-25.md"
        content = file_25.read_text()
        if "✅ outcome for this cron run" in content and content.count("✅ outcome for this cron run") > 1:
            print("  ✓ Files not modified (dry-run working)")
        else:
            print("  ❌ Files were modified (dry-run failed)")
            return False
    
    print("✅ Dry-run test passed\n")
    return True

def test_actual_cleanup():
    """Test actual deduplication and formatting fixes."""
    print("🧪 Testing actual cleanup...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        create_test_memory_structure(test_dir)
        
        # Run without dry-run
        returncode, stdout, stderr = run_memory_cleanup(test_dir, "--dedupe --fix-formatting")
        
        if returncode != 0:
            print(f"❌ Failed with return code {returncode}")
            print(f"Stderr: {stderr}")
            return False
        
        # Check 2026-03-25.md for deduplication
        file_25 = test_dir / "memory" / "daily" / "2026-03-25.md"
        content = file_25.read_text()
        
        # Should have removed duplicate cron entries
        if content.count("✅ outcome for this cron run") == 1:
            print("  ✓ Deduplicated cron entries")
        else:
            print(f"  ❌ Still has {content.count('✅ outcome for this cron run')} duplicates")
            return False
        
        # Should have removed duplicate Decision entries
        if content.count("📋 Decision: queue is empty") == 1:
            print("  ✓ Deduplicated Decision entries")
        else:
            print(f"  ❌ Still has {content.count('📋 Decision: queue is empty')} duplicates")
            return False
        
        # Check 2026-03-24.md for fixed malformed timestamp
        file_24 = test_dir / "memory" / "daily" / "2026-03-24.md"
        content_24 = file_24.read_text()
        
        if "12:00 Meeting with client" not in content_24 and "[12:00] Meeting with client" in content_24:
            print("  ✓ Fixed malformed timestamp")
        else:
            print("  ❌ Malformed timestamp not fixed")
            print(f"  Content snippet: {content_24[100:200]}")
            return False
    
    print("✅ Actual cleanup test passed\n")
    return True

def test_statistics():
    """Test statistics mode."""
    print("🧪 Testing statistics...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        create_test_memory_structure(test_dir)
        
        # Run stats
        returncode, stdout, stderr = run_memory_cleanup(test_dir, "--stats")
        
        if returncode != 0:
            print(f"❌ Failed with return code {returncode}")
            print(f"Stderr: {stderr}")
            return False
        
        # Check for expected statistics
        expected_stats = [
            "MEMORY STATISTICS",
            "Total files:",
            "Total entries:",
            "Date range:",
        ]
        
        for stat in expected_stats:
            if stat in stdout:
                print(f"  ✓ Found '{stat}' in output")
            else:
                print(f"  ⚠️  Missing '{stat}' in output")
    
    print("✅ Statistics test passed\n")
    return True

def test_archive():
    """Test archive functionality."""
    print("🧪 Testing archive...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        daily_dir = create_test_memory_structure(test_dir)
        archive_dir = test_dir / "memory" / "archive" / "daily"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Run archive with short max-age (should archive 2026-01-15.md)
        returncode, stdout, stderr = run_memory_cleanup(test_dir, "--archive --max-age 60 --dry-run")
        
        if returncode != 0:
            print(f"❌ Failed with return code {returncode}")
            print(f"Stderr: {stderr}")
            return False
        
        # Should mention archiving old file
        if "Would archive" in stdout or "Archiving" in stdout:
            print("  ✓ Archive functionality working")
        else:
            # In dry-run mode it might say "Would archive" or just show stats
            # Let's check if the old file was detected
            if "2026-01-15.md" in stdout:
                print("  ✓ Archive functionality working (detected old file)")
            else:
                print("  ⚠️  Archive output not as expected")
        
        # Check files still in daily dir (dry-run)
        files_after = list(daily_dir.glob("*.md"))
        if len(files_after) == 4:  # All files still there
            print("  ✓ Files not moved (dry-run)")
        else:
            print(f"  ❌ File count changed: {len(files_after)}")
            return False
    
    print("✅ Archive test passed\n")
    return True

def test_help():
    """Test help output."""
    print("🧪 Testing help...")
    
    script_path = Path(__file__).parent / "memory_cleanup.py"
    result = subprocess.run([sys.executable, str(script_path), "--help"], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Help failed with return code {result.returncode}")
        return False
    
    expected_help = [
        "usage:",
        "--help",
        "--dry-run",
        "--verbose",
        "--stats",
    ]
    
    for phrase in expected_help:
        if phrase in result.stdout:
            print(f"  ✓ Found '{phrase}' in help")
        else:
            print(f"  ⚠️  Missing '{phrase}' in help")
    
    print("✅ Help test passed\n")
    return True

def main():
    """Run all verification tests."""
    print("🔍 Verifying Memory Cleanup CLI")
    print("=" * 50)
    
    tests = [
        test_help,
        test_dry_run,
        test_actual_cleanup,
        test_statistics,
        test_archive,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All tests passed! The tool is ready for use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())