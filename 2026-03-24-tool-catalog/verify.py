#!/usr/bin/env python3
"""
Verification script for Tool Catalog CLI.
Tests basic functionality and ensures the tool works correctly.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd):
    """Run a command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def test_help():
    """Test that help command works."""
    print("Testing --help flag...")
    returncode, stdout, stderr = run_command("python3 tool-catalog.py --help")
    if returncode == 0 and "usage:" in stdout.lower():
        print("✓ Help command works")
        return True
    else:
        print("✗ Help command failed")
        print(f"  stdout: {stdout[:200]}")
        print(f"  stderr: {stderr}")
        return False

def test_scan():
    """Test scanning functionality."""
    print("\nTesting scan command...")
    returncode, stdout, stderr = run_command("python3 tool-catalog.py scan")
    if returncode == 0 and "Scanning nightly-builds directory..." in stdout:
        print("✓ Scan command works")
        
        # Check if catalog file was created
        catalog_file = os.path.join(os.path.expanduser("~/clawd/nightly-builds"), "tool_catalog.json")
        if os.path.exists(catalog_file):
            print(f"✓ Catalog file created: {catalog_file}")
            
            # Try to parse it
            try:
                with open(catalog_file, 'r') as f:
                    catalog = json.load(f)
                tool_count = catalog.get('count', 0)
                print(f"✓ Catalog contains {tool_count} tools")
                return True
            except json.JSONDecodeError as e:
                print(f"✗ Catalog JSON is invalid: {e}")
                return False
        else:
            print(f"✗ Catalog file not found at {catalog_file}")
            return False
    else:
        print("✗ Scan command failed")
        print(f"  stdout: {stdout[:200]}")
        print(f"  stderr: {stderr}")
        return False

def test_list():
    """Test list command."""
    print("\nTesting list command...")
    returncode, stdout, stderr = run_command("python3 tool-catalog.py list")
    if returncode == 0 and len(stdout.strip()) > 0:
        print("✓ List command works")
        
        # Check verbose mode
        returncode_v, stdout_v, stderr_v = run_command("python3 tool-catalog.py list --verbose")
        if returncode_v == 0:
            print("✓ Verbose list works")
            return True
        else:
            print("✗ Verbose list failed")
            return False
    else:
        print("✗ List command failed")
        print(f"  stdout: {stdout[:200]}")
        print(f"  stderr: {stderr}")
        return False

def test_search():
    """Test search command."""
    print("\nTesting search command...")
    # Try searching for common terms
    test_queries = ["calendar", "github", "tool"]
    
    for query in test_queries:
        returncode, stdout, stderr = run_command(f"python3 tool-catalog.py search {query}")
        if returncode == 0:
            print(f"✓ Search for '{query}' works")
        else:
            print(f"✗ Search for '{query}' failed")
            print(f"  stderr: {stderr}")
            return False
    
    return True

def test_info():
    """Test info command."""
    print("\nTesting info command...")
    
    # First, get a tool from the catalog
    catalog_file = os.path.join(os.path.expanduser("~/clawd/nightly-builds"), "tool_catalog.json")
    if not os.path.exists(catalog_file):
        print("✗ Catalog file missing - run scan first")
        return False
    
    try:
        with open(catalog_file, 'r') as f:
            catalog = json.load(f)
        
        if catalog.get('tools'):
            # Try to get info for the first tool
            first_tool = catalog['tools'][0]
            tool_id = first_tool.get('directory', '')
            
            if tool_id:
                returncode, stdout, stderr = run_command(f"python3 tool-catalog.py info {tool_id}")
                if returncode == 0 and "Tool:" in stdout:
                    print(f"✓ Info command works for '{tool_id}'")
                    return True
                else:
                    print(f"✗ Info command failed for '{tool_id}'")
                    print(f"  stdout: {stdout[:200]}")
                    return False
            else:
                print("✗ Could not find tool ID in catalog")
                return False
        else:
            print("✗ No tools in catalog")
            return False
    except Exception as e:
        print(f"✗ Error reading catalog: {e}")
        return False

def test_markdown():
    """Test markdown generation."""
    print("\nTesting markdown generation...")
    returncode, stdout, stderr = run_command("python3 tool-catalog.py generate-markdown")
    if returncode == 0 and "# Tool Catalog Reference" in stdout:
        print("✓ Markdown generation works")
        
        # Try to save to file
        with open("test_catalog.md", "w") as f:
            f.write(stdout)
        print("✓ Test catalog saved to test_catalog.md")
        
        # Clean up
        if os.path.exists("test_catalog.md"):
            os.remove("test_catalog.md")
            print("✓ Test file cleaned up")
        
        return True
    else:
        print("✗ Markdown generation failed")
        print(f"  stdout: {stdout[:200]}")
        print(f"  stderr: {stderr}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Tool Catalog CLI Verification")
    print("=" * 60)
    
    tests = [
        ("Help Command", test_help),
        ("Scan Command", test_scan),
        ("List Command", test_list),
        ("Search Command", test_search),
        ("Info Command", test_info),
        ("Markdown Generation", test_markdown),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test_name} raised exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ All tests passed! Tool Catalog CLI is ready.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())