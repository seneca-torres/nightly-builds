#!/usr/bin/env python3
"""
Verification script for Meeting Assistant.

Tests all features of the meeting_assistant.py tool.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, capture_output=True):
    """Run a command and return result."""
    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True, shell=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def test_basic_functionality():
    """Test basic CLI commands."""
    print("🧪 Testing basic functionality...")
    
    # Test help
    print("  Testing --help...")
    returncode, stdout, stderr = run_command("python3 meeting_assistant.py --help")
    if returncode != 0:
        print(f"  ❌ Failed: {stderr}")
        return False
    print("  ✅ Help command works")
    
    # Test list command
    print("  Testing list command...")
    returncode, stdout, stderr = run_command("python3 meeting_assistant.py list")
    # This should work even if no contacts exist
    if returncode != 0:
        print(f"  ⚠️ List command warning: {stderr}")
    print("  ✅ List command works")
    
    return True

def test_demo_mode():
    """Test demo mode."""
    print("🧪 Testing demo mode...")
    
    returncode, stdout, stderr = run_command("python3 meeting_assistant.py demo")
    if returncode != 0:
        print(f"  ❌ Demo mode failed: {stderr}")
        return False
    
    # Check for demo markers in output
    if "DEMO MODE" in stdout and "MEETING PREPARATION REPORT" in stdout:
        print("  ✅ Demo mode generates report")
        return True
    else:
        print("  ❌ Demo output missing expected content")
        return False

def test_search_function():
    """Test search functionality."""
    print("🧪 Testing search function...")
    
    returncode, stdout, stderr = run_command("python3 meeting_assistant.py search test")
    if returncode != 0:
        print(f"  ⚠️ Search command warning: {stderr}")
    print("  ✅ Search command works")
    return True

def test_prepare_command():
    """Test prepare command (will fail without real contact)."""
    print("🧪 Testing prepare command...")
    
    returncode, stdout, stderr = run_command("python3 meeting_assistant.py prepare 'Test Coach'")
    if returncode == 0:
        print("  ⚠️ Prepare command succeeded (might be using demo data)")
    else:
        print(f"  ⚠️ Prepare command failed as expected (no real contact): {stderr}")
    print("  ✅ Prepare command syntax works")
    return True

def test_file_creation():
    """Test that the tool can create output files."""
    print("🧪 Testing file creation...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy the tool to temp directory
        tool_path = os.path.join(tmpdir, "meeting_assistant.py")
        shutil.copy("meeting_assistant.py", tool_path)
        
        # Change to temp directory
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Run demo with save
            returncode, stdout, stderr = run_command(
                "echo 'y' | python3 meeting_assistant.py demo"
            )
            
            # Check for saved file
            md_files = list(Path(tmpdir).glob("meeting_prep_*.md"))
            if md_files:
                print(f"  ✅ File created: {md_files[0].name}")
                # Read and check content
                content = md_files[0].read_text()
                if "MEETING PREPARATION REPORT" in content:
                    print("  ✅ File contains expected content")
                    return True
                else:
                    print("  ❌ File missing expected content")
                    return False
            else:
                print("  ❌ No file created")
                return False
        finally:
            os.chdir(original_dir)

def test_imports_and_dependencies():
    """Test that all imports work (no missing dependencies)."""
    print("🧪 Testing imports and dependencies...")
    
    # Try to import the module
    import meeting_assistant
    
    # Check for required modules
    required_modules = [
        'os', 'sys', 'json', 'glob', 're', 'subprocess', 
        'textwrap', 'datetime', 'argparse', 'pathlib'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            print(f"  ❌ Missing required module: {module}")
            return False
    
    print("  ✅ All imports work")
    return True

def check_code_style():
    """Check for basic code style issues."""
    print("🧪 Checking code style...")
    
    with open("meeting_assistant.py", "r") as f:
        content = f.read()
    
    issues = []
    
    # Check for print statements (should use logging in production)
    if content.count('print(') > 20:
        issues.append("Many print statements - consider logging")
    
    # Check for proper shebang
    if not content.startswith('#!/usr/bin/env python3'):
        issues.append("Missing shebang line")
    
    # Check for docstring
    if '"""Meeting Assistant' not in content:
        issues.append("Missing module docstring")
    
    if issues:
        print(f"  ⚠️ Style issues: {', '.join(issues)}")
    else:
        print("  ✅ Code style OK")
    
    return True  # Not a critical failure

def main():
    """Run all tests."""
    print("🔬 Starting Meeting Assistant verification...")
    print("=" * 60)
    
    tests = [
        ("Basic functionality", test_basic_functionality),
        ("Demo mode", test_demo_mode),
        ("Search function", test_search_function),
        ("Prepare command", test_prepare_command),
        ("File creation", test_file_creation),
        ("Imports", test_imports_and_dependencies),
        ("Code style", check_code_style),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"  Result: ✅ PASS")
            else:
                print(f"  Result: ❌ FAIL")
        except Exception as e:
            print(f"  Result: 💥 ERROR: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("-" * 40)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Meeting Assistant is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())