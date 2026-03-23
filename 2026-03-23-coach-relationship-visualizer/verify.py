#!/usr/bin/env python3
"""
Verification script for Coach Relationship Visualizer
Tests that all components work correctly.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def test_parser():
    """Test the parser with demo data."""
    print("🧪 Testing parser with demo data...")
    
    try:
        # Run parser with demo flag
        result = subprocess.run(
            [sys.executable, "parser.py", "--demo", "--output", "test_output.json"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode != 0:
            print(f"❌ Parser failed: {result.stderr}")
            return False
        
        # Check if output file was created
        output_file = Path(__file__).parent / "test_output.json"
        if not output_file.exists():
            print("❌ Output file not created")
            return False
        
        # Validate JSON structure
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        required_keys = ['nodes', 'edges', 'metadata']
        for key in required_keys:
            if key not in data:
                print(f"❌ Missing key in JSON: {key}")
                return False
        
        print(f"✅ Parser test passed: {len(data['nodes'])} nodes, {len(data['edges'])} edges")
        
        # Clean up
        output_file.unlink()
        web_output = output_file.parent / "web_graph.json"
        if web_output.exists():
            web_output.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Parser test failed with exception: {e}")
        return False

def test_web_files():
    """Test that web files exist and have correct structure."""
    print("🧪 Testing web files...")
    
    web_dir = Path(__file__).parent / "visualizer"
    required_files = ['index.html', 'style.css', 'app.js']
    
    for file in required_files:
        file_path = web_dir / file
        if not file_path.exists():
            print(f"❌ Missing web file: {file}")
            return False
    
    # Check that index.html contains required elements
    index_content = (web_dir / "index.html").read_text()
    required_elements = ['graph-container', 'graph-svg', 'search']
    for element in required_elements:
        if element not in index_content:
            print(f"❌ Missing element in index.html: {element}")
            return False
    
    print("✅ Web files test passed")
    return True

def test_directory_structure():
    """Test that directory structure is correct."""
    print("🧪 Testing directory structure...")
    
    base_dir = Path(__file__).parent
    required_dirs = ['visualizer']
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            print(f"❌ Missing directory: {dir_name}")
            return False
    
    required_files = ['README.md', 'parser.py', 'verify.py', 'requirements.txt']
    for file in required_files:
        file_path = base_dir / file
        if not file_path.exists():
            print(f"❌ Missing file: {file}")
            return False
    
    print("✅ Directory structure test passed")
    return True

def test_demo_mode_integration():
    """Test full integration with demo mode."""
    print("🧪 Testing full demo mode integration...")
    
    try:
        # First, generate demo data
        result = subprocess.run(
            [sys.executable, "parser.py", "--demo", "--verbose"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode != 0:
            print(f"❌ Demo generation failed: {result.stderr}")
            return False
        
        # Check output mentions demo data
        if "Generating demo data" not in result.stdout:
            print("❌ Demo mode output incorrect")
            return False
        
        print("✅ Demo mode integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Demo integration test failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("🔍 Starting verification for Coach Relationship Visualizer")
    print("=" * 60)
    
    tests = [
        test_directory_structure,
        test_web_files,
        test_parser,
        test_demo_mode_integration
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
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All tests passed! The visualizer is ready to use.")
        
        # Show next steps
        print("\n🚀 Next steps:")
        print("1. Generate demo data: python3 parser.py --demo")
        print("2. Start web server: python3 -m http.server 8000")
        print("3. Open browser: http://localhost:8000/visualizer/")
        print("4. Explore the coach-school relationships!")
        
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())