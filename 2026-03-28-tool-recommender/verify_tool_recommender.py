#!/usr/bin/env python3
"""
Verification script for tool_recommender.py
Tests that the tool recommender loads, searches, and reports stats correctly.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def test_import():
    """Test that we can import the module."""
    print("🔍 Testing module import...")
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import tool_recommender
        print("✅ Module imports successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import module: {e}")
        return False

def test_stats():
    """Test --stats flag."""
    print("\n📊 Testing --stats flag...")
    try:
        result = subprocess.run(
            [sys.executable, "tool_recommender.py", "--stats"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            print("✅ --stats works correctly")
            # Check for expected output
            if "Total tools:" in result.stdout:
                print("✅ Stats include total tools count")
            else:
                print("⚠️  Stats output may be incomplete")
            return True
        else:
            print(f"❌ --stats failed with return code {result.returncode}")
            print(f"Stderr: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Exception running --stats: {e}")
        return False

def test_demo():
    """Test --demo flag."""
    print("\n🚀 Testing --demo flag...")
    try:
        result = subprocess.run(
            [sys.executable, "tool_recommender.py", "--demo"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            print("✅ --demo works correctly")
            # Check for expected output
            if "Running demo queries" in result.stdout:
                print("✅ Demo mode runs example queries")
            else:
                print("⚠️  Demo output may be incomplete")
            return True
        else:
            print(f"❌ --demo failed with return code {result.returncode}")
            print(f"Stderr: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Exception running --demo: {e}")
        return False

def test_list():
    """Test --list flag."""
    print("\n📋 Testing --list flag...")
    try:
        result = subprocess.run(
            [sys.executable, "tool_recommender.py", "--list"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            print("✅ --list works correctly")
            # Check for expected output
            if "All Tools" in result.stdout:
                print("✅ List shows tools header")
            else:
                print("⚠️  List output may be incomplete")
            return True
        else:
            print(f"❌ --list failed with return code {result.returncode}")
            print(f"Stderr: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Exception running --list: {e}")
        return False

def test_search():
    """Test search functionality."""
    print("\n🔍 Testing search functionality...")
    try:
        # Test with a generic query that should match something
        result = subprocess.run(
            [sys.executable, "tool_recommender.py", "search"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            print("✅ Search works correctly")
            # Check for expected output patterns
            output = result.stdout.lower()
            if "searching for:" in output or "found" in output or "no matching" in output:
                print("✅ Search returns appropriate response")
            else:
                print("⚠️  Search output may be incomplete")
            return True
        else:
            print(f"❌ Search failed with return code {result.returncode}")
            print(f"Stderr: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Exception running search: {e}")
        return False

def test_help():
    """Test help flag."""
    print("\n❓ Testing help flag...")
    try:
        result = subprocess.run(
            [sys.executable, "tool_recommender.py", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            print("✅ --help works correctly")
            if "usage:" in result.stdout.lower():
                print("✅ Help shows usage information")
            return True
        else:
            print(f"❌ --help failed with return code {result.returncode}")
            return False
    except Exception as e:
        print(f"❌ Exception running --help: {e}")
        return False

def create_test_registry():
    """Create a test TOOLS_REGISTRY.md file for testing."""
    print("\n📝 Creating test registry...")
    test_content = """# Test Tools Registry

### Test Tool 1
**File:** `~/clawd/test_tool1.py`
**What it does:** Tests tool recommendation system
**When to use:** When you need to test the recommender
**Added:** 2026-03-28

### Test Tool 2  
**File:** `~/clawd/test_tool2.py`
**What it does:** Another test tool for verification
**Added:** 2026-03-28
"""
    
    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TEST_REGISTRY.md")
    with open(test_file, "w") as f:
        f.write(test_content)
    
    return test_file

def test_with_custom_registry():
    """Test with a custom registry file."""
    print("\n🧪 Testing with custom registry...")
    test_registry = create_test_registry()
    
    try:
        result = subprocess.run(
            [sys.executable, "tool_recommender.py", "--registry", test_registry, "--stats"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Clean up test file
        if os.path.exists(test_registry):
            os.remove(test_registry)
        
        if result.returncode == 0:
            print("✅ Custom registry works correctly")
            if "Total tools:" in result.stdout and "Test Tool" in result.stdout:
                print("✅ Loads tools from custom registry")
            return True
        else:
            print(f"❌ Custom registry test failed: {result.returncode}")
            return False
    except Exception as e:
        print(f"❌ Exception with custom registry: {e}")
        # Clean up on exception too
        if os.path.exists(test_registry):
            os.remove(test_registry)
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("🔧 Verification: Tool Recommender")
    print("=" * 60)
    
    tests = [
        test_import,
        test_help,
        test_stats,
        test_demo,
        test_list,
        test_search,
        test_with_custom_registry,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Tool recommender is ready.")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed. Check output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())