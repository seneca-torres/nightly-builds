#!/bin/bash
# Simple test script for Client Intake Manager

echo "🧪 Testing Client Intake Manager..."
echo "=================================="

# Make script executable
chmod +x client_intake_manager.py

# Test 1: Show help
echo -e "\n1. Testing help command..."
python3 client_intake_manager.py --help | head -20

# Test 2: Add a sample client
echo -e "\n2. Adding sample client..."
python3 client_intake_manager.py add \
  --name "Test Coach" \
  --type coach \
  --source test \
  --email test@example.com \
  --notes "Test client for verification"

# Test 3: Show dashboard
echo -e "\n3. Showing dashboard..."
python3 client_intake_manager.py dashboard

# Test 4: Generate brief
echo -e "\n4. Generating brief..."
python3 client_intake_manager.py generate-brief 1 --output ./

# Test 5: Clean up
echo -e "\n5. Cleaning up..."
rm -f client_intake.db
rm -f client_1_test_coach.md
rm -rf briefs/

echo -e "\n✅ Simple tests complete!"
echo "Run 'python3 verify.py' for comprehensive testing."