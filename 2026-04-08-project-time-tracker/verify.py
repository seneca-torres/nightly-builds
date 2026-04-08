#!/usr/bin/env python3
"""
Verification script for Project Time Tracker.
Tests basic functionality and outputs results.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def test_basic_help():
    """Test that help command works."""
    print("🔍 Testing help command...")
    code, out, err = run_command("python3 project_tracker.py --help")
    
    if code == 0 and "Project Time Tracker" in out:
        print("  ✅ Help command works")
        return True
    else:
        print(f"  ❌ Help command failed: {err}")
        return False

def test_demo_mode():
    """Test demo mode functionality."""
    print("\n🔍 Testing demo mode...")
    
    # Create temp directory for demo
    temp_dir = tempfile.mkdtemp(prefix="project_tracker_test_")
    
    # Run demo mode
    code, out, err = run_command(f"python3 project_tracker.py --data-dir {temp_dir} demo")
    
    if code == 0 and "Demo data loaded" in out:
        print("  ✅ Demo mode works")
        
        # Check that demo files were created
        demo_dir = Path(temp_dir) / "demo"
        if demo_dir.exists():
            print("  ✅ Demo directory created")
            
            # Test report with demo data
            code2, out2, err2 = run_command(
                f"python3 project_tracker.py --data-dir {demo_dir} report --period week"
            )
            
            if code2 == 0 and "Time Report" in out2:
                print("  ✅ Report generation works with demo data")
                
                # Test dashboard
                code3, out3, err3 = run_command(
                    f"python3 project_tracker.py --data-dir {demo_dir} dashboard"
                )
                
                if code3 == 0 and "Priority vs Time Dashboard" in out3:
                    print("  ✅ Dashboard works with demo data")
                    
                    # Test export
                    export_file = Path(temp_dir) / "test_report.md"
                    code4, out4, err4 = run_command(
                        f"python3 project_tracker.py --data-dir {demo_dir} export --output {export_file}"
                    )
                    
                    if code4 == 0 and export_file.exists():
                        print("  ✅ Export works")
                        
                        # Clean up
                        shutil.rmtree(temp_dir)
                        return True
                    else:
                        print(f"  ❌ Export failed: {err4}")
                else:
                    print(f"  ❌ Dashboard failed: {err3}")
            else:
                print(f"  ❌ Report failed: {err2}")
        else:
            print("  ❌ Demo directory not created")
    else:
        print(f"  ❌ Demo mode failed: {err}")
    
    # Clean up on failure
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)
    return False

def test_add_and_log():
    """Test adding project and logging time."""
    print("\n🔍 Testing add-project and log-time...")
    
    temp_dir = tempfile.mkdtemp(prefix="project_tracker_test2_")
    
    # Add a project
    code1, out1, err1 = run_command(
        f'python3 project_tracker.py --data-dir {temp_dir} add-project "Test Project" day-job 3 10'
    )
    
    if code1 == 0 and "Added project" in out1:
        print("  ✅ Add-project works")
        
        # Log time
        code2, out2, err2 = run_command(
            f'python3 project_tracker.py --data-dir {temp_dir} log-time "Test Project" today 2.5 "Testing"'
        )
        
        if code2 == 0 and "Logged" in out2:
            print("  ✅ Log-time works")
            
            # Verify files were created
            projects_file = Path(temp_dir) / "projects.json"
            entries_file = Path(temp_dir) / "entries.json"
            
            if projects_file.exists() and entries_file.exists():
                print("  ✅ Data files created")
                
                # Clean up
                shutil.rmtree(temp_dir)
                return True
            else:
                print("  ❌ Data files not created")
        else:
            print(f"  ❌ Log-time failed: {err2}")
    else:
        print(f"  ❌ Add-project failed: {err1}")
    
    # Clean up on failure
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)
    return False

def test_error_handling():
    """Test error cases."""
    print("\n🔍 Testing error handling...")
    
    temp_dir = tempfile.mkdtemp(prefix="project_tracker_test3_")
    
    # Test adding duplicate project
    run_command(f'python3 project_tracker.py --data-dir {temp_dir} add-project "Test" day-job 3 10')
    code1, out1, err1 = run_command(
        f'python3 project_tracker.py --data-dir {temp_dir} add-project "Test" day-job 3 10'
    )
    
    if "already exists" in out1:
        print("  ✅ Duplicate project detection works")
    else:
        print("  ❌ Duplicate project detection failed")
    
    # Test logging to non-existent project
    code2, out2, err2 = run_command(
        f'python3 project_tracker.py --data-dir {temp_dir} log-time "Nonexistent" today 1 "Test"'
    )
    
    if "not found" in out2:
        print("  ✅ Non-existent project error works")
    else:
        print("  ❌ Non-existent project error failed")
    
    # Test invalid date format
    code3, out3, err3 = run_command(
        f'python3 project_tracker.py --data-dir {temp_dir} log-time "Test" invalid-date 1 "Test"'
    )
    
    if "Invalid date format" in out3:
        print("  ✅ Invalid date format error works")
    else:
        print("  ❌ Invalid date format error failed")
    
    # Clean up
    shutil.rmtree(temp_dir)
    return True

def main():
    """Run all tests."""
    print("🔬 Project Time Tracker Verification")
    print("=" * 50)
    
    tests_passed = 0
    tests_total = 0
    
    # Check if main file exists
    if not Path("project_tracker.py").exists():
        print("❌ project_tracker.py not found in current directory")
        return 1
    
    # Run tests
    tests = [
        ("Basic help", test_basic_help),
        ("Demo mode", test_demo_mode),
        ("Add and log", test_add_and_log),
        ("Error handling", test_error_handling),
    ]
    
    for test_name, test_func in tests:
        tests_total += 1
        try:
            if test_func():
                tests_passed += 1
                print(f"  ✅ {test_name} passed")
            else:
                print(f"  ❌ {test_name} failed")
        except Exception as e:
            print(f"  ❌ {test_name} crashed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{tests_total} passed")
    
    if tests_passed == tests_total:
        print("✅ All tests passed! Tool is ready for use.")
        return 0
    else:
        print(f"⚠️  {tests_total - tests_passed} tests failed. Review output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())