#!/bin/bash
cd "$(dirname "$0")"

echo "=== Testing Meeting Assistant ==="
echo ""

echo "1. Testing --help:"
python3 meeting_assistant.py --help
echo ""

echo "2. Testing list command:"
python3 meeting_assistant.py list
echo ""

echo "3. Testing demo mode (first 30 lines):"
python3 meeting_assistant.py demo | head -30
echo ""

echo "4. Testing search for 'Dan':"
python3 meeting_assistant.py search Dan
echo ""

echo "=== Test Complete ==="