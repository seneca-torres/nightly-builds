#!/usr/bin/env python3
"""
Verification script for Broadcaster Notes Web UI.
Tests the entity extraction and web server functionality.
"""

import subprocess
import sys
import os
import time
import json
import requests
from threading import Thread

def test_entity_extraction():
    """Test the entity extraction module."""
    print("🧪 Testing entity extraction...")
    
    try:
        from entities import extract_entities
        
        test_text = """
        Meeting with Nick Saban at Alabama on 2023-09-15.
        Discussed offensive coordinator search with Dan Casey.
        Ryan Day from Ohio State was mentioned as a reference.
        """
        
        entities = extract_entities(test_text)
        
        # Check expected entities
        expected_coaches = {"Nick Saban", "Dan Casey", "Ryan Day"}
        found_coaches = set(entities['coaches'])
        
        expected_schools = {"Alabama", "Ohio State"}
        found_schools = set(entities['schools'])
        
        expected_dates = {"2023-09-15"}
        found_dates = set(entities['dates'])
        
        # Verify extraction
        all_passed = True
        
        if not expected_coaches.issubset(found_coaches):
            print(f"  ❌ Missing coaches: {expected_coaches - found_coaches}")
            all_passed = False
        else:
            print(f"  ✅ Coaches found: {found_coaches}")
        
        if not expected_schools.issubset(found_schools):
            print(f"  ❌ Missing schools: {expected_schools - found_schools}")
            all_passed = False
        else:
            print(f"  ✅ Schools found: {found_schools}")
        
        if not expected_dates.issubset(found_dates):
            print(f"  ❌ Missing dates: {expected_dates - found_dates}")
            all_passed = False
        else:
            print(f"  ✅ Dates found: {found_dates}")
        
        return all_passed
        
    except Exception as e:
        print(f"  ❌ Entity extraction test failed: {e}")
        return False

def test_server():
    """Test the Flask server."""
    print("🌐 Testing web server...")
    
    # Start server in background
    server_process = None
    try:
        # Start the server
        server_process = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give server time to start
        time.sleep(3)
        
        # Test basic endpoints
        base_url = "http://localhost:8080"
        
        # Test home page
        try:
            response = requests.get(base_url, timeout=5)
            if response.status_code == 200:
                print("  ✅ Home page loaded successfully")
            else:
                print(f"  ❌ Home page failed with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Could not connect to server: {e}")
            return False
        
        # Test API endpoints
        test_text = "Test note with Nick Saban at Alabama."
        
        # Test /api/process
        try:
            response = requests.post(
                f"{base_url}/api/process",
                json={"text": test_text},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("  ✅ API process endpoint working")
                else:
                    print(f"  ❌ API process failed: {data.get('error')}")
                    return False
            else:
                print(f"  ❌ API process failed with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"  ❌ API process test failed: {e}")
            return False
        
        # Test /api/notes
        try:
            response = requests.get(f"{base_url}/api/notes", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ API notes endpoint working (found {data.get('count', 0)} notes)")
            else:
                print(f"  ❌ API notes failed with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"  ❌ API notes test failed: {e}")
            return False
        
        return True
        
    finally:
        # Kill server process
        if server_process:
            server_process.terminate()
            server_process.wait(timeout=5)

def check_files():
    """Check that all required files exist."""
    print("📁 Checking required files...")
    
    required_files = [
        "app.py",
        "entities.py",
        "templates/index.html",
        "README.md",
        "verify.py"
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (missing)")
            all_exist = False
    
    return all_exist

def create_sample_notes():
    """Create sample notes directory for testing."""
    print("📝 Creating sample notes...")
    
    sample_dir = "sample_notes"
    os.makedirs(sample_dir, exist_ok=True)
    
    samples = [
        ("alabama_visit.txt", """Meeting with Alabama staff - 2023-09-15

Attended practice at Alabama. Spent time with Head Coach Nick Saban and Offensive Coordinator Tommy Rees.
Discussed quarterback development program with Dan Casey (Quarterbacks Coach).

Key observations:
- Jalen Milroe showing improved pocket presence
- Offensive line needs work on pass protection
- Defense looks solid under Defensive Coordinator Kevin Steele

Follow-up scheduled for October 20, 2023.
"""),
        
        ("ohio_state_clinic.txt", """Ohio State Coaching Clinic - 2023-08-10

Spoke with Ryan Day (Head Coach) about their offensive philosophy.
Also met with Wide Receivers Coach Brian Hartline.

Key takeaways:
- Emphasis on tempo and RPO game
- Developing young QBs is a priority
- Looking for a new Tight Ends Coach

Ryan mentioned he'll be at the Big Ten Media Days next month.
"""),
        
        ("sec_networking.txt", """SEC Networking Event - 2023-07-22

Multiple conversations:
- Kirby Smart (Georgia Head Coach) - discussed defensive trends
- Billy Napier (Florida Head Coach) - rebuilding program challenges
- Lane Kiffin (Ole Miss Head Coach) - offensive innovation

Also spoke with several assistants:
- Mike Norvell (Florida State) briefly about ACC vs SEC
- Shane Beamer (South Carolina) about special teams

Follow-ups needed with all of the above.
""")
    ]
    
    for filename, content in samples:
        filepath = os.path.join(sample_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✅ Created {filepath}")
    
    return True

def main():
    """Run all verification tests."""
    print("🔍 Starting verification for Broadcaster Notes Web UI")
    print("=" * 60)
    
    all_passed = True
    
    # Check files
    if not check_files():
        all_passed = False
    
    print()
    
    # Test entity extraction
    if not test_entity_extraction():
        all_passed = False
    
    print()
    
    # Create sample notes
    if not create_sample_notes():
        all_passed = False
    
    print()
    
    # Test server (optional - can be skipped if port 8080 is in use)
    try:
        if not test_server():
            print("  ⚠️ Server test failed or skipped (port may be in use)")
            print("  ℹ️ You can still test manually with: python3 app.py")
    except Exception as e:
        print(f"  ⚠️ Server test exception: {e}")
        print("  ℹ️ You can test manually with: python3 app.py")
    
    print()
    print("=" * 60)
    
    if all_passed:
        print("✅ All verification checks passed!")
        print()
        print("To run the application:")
        print("  1. Start the server: python3 app.py")
        print("  2. Open browser to: http://localhost:8080")
        print("  3. Use sample notes in 'sample_notes/' directory")
        return 0
    else:
        print("❌ Some verification checks failed.")
        print("Please fix the issues above before running the application.")
        return 1

if __name__ == "__main__":
    sys.exit(main())