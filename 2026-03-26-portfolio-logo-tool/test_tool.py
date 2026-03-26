#!/usr/bin/env python3
"""
Quick test for the Portfolio Logo Tool.
"""

import subprocess
import sys
import os

def test_list():
    """Test the list command."""
    print("Testing 'list' command...")
    result = subprocess.run(
        [sys.executable, "logo_tool.py", "list"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ List command works")
        print(f"Output preview:\n{result.stdout[:500]}...")
        return True
    else:
        print(f"✗ List command failed: {result.stderr}")
        return False

def test_scan():
    """Test logo scanning directly."""
    print("\nTesting logo scanning...")
    
    # Import the module directly
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from logo_tool import scan_logos
        logos = scan_logos()
        print(f"✓ Found {len(logos)} logos")
        for i, logo in enumerate(logos[:3], 1):
            print(f"  {i}. {logo['name']} ({logo['type']})")
        if len(logos) > 3:
            print(f"  ... and {len(logos)-3} more")
        return True
    except Exception as e:
        print(f"✗ Scanning failed: {e}")
        return False

def test_html_generation():
    """Test HTML generation."""
    print("\nTesting HTML generation...")
    
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from logo_tool import scan_logos, create_logo_preview_html
        logos = scan_logos()
        html = create_logo_preview_html(logos)
        
        # Check HTML contains expected elements
        checks = [
            ("<!DOCTYPE html" in html, "Has DOCTYPE"),
            ("<title>" in html, "Has title"),
            (str(len(logos)) in html, "Shows logo count"),
        ]
        
        all_passed = True
        for check_passed, description in checks:
            if check_passed:
                print(f"✓ {description}")
            else:
                print(f"✗ {description}")
                all_passed = False
        
        # Write test output
        test_html = "test_output.html"
        with open(test_html, "w") as f:
            f.write(html[:5000] + "\n... [truncated]")
        print(f"  Test HTML written to {test_html}")
        
        return all_passed
    except Exception as e:
        print(f"✗ HTML generation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Portfolio Logo Tool Tests ===\n")
    
    tests = [
        ("List Command", test_list),
        ("Logo Scanning", test_scan),
        ("HTML Generation", test_html_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n=== Test Summary ===")
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n{passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✅ All tests passed! Tool is ready.")
        print("\nNext steps:")
        print("1. Run: python logo_tool.py preview")
        print("2. Browse logos in web interface")
        print("3. Try applying a logo: python logo_tool.py apply 1")
    else:
        print("\n❌ Some tests failed. Check above for errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()