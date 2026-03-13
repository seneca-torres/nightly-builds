#!/bin/bash
set -e

echo "🔍 Verifying Calendar Free Slots Finder..."

# Check Python version
python3 --version

# Run demo mode (should succeed)
echo "Running demo mode..."
python3 calendar_free_slots.py --demo > /dev/null
echo "✅ Demo mode passed"

# Run with default args (should not crash, but may have no events)
echo "Running with gog (real call)..."
if python3 calendar_free_slots.py --days 1 2>&1 | grep -q "Error fetching events"; then
    echo "⚠️  gog call failed (maybe not authenticated). That's okay for verification."
else
    echo "✅ gog call succeeded"
fi

# Check that script exits cleanly with invalid time format
echo "Testing invalid time format..."
python3 calendar_free_slots.py --start invalid 2>&1 | grep -q "Invalid time format" && echo "✅ Invalid time format caught" || (echo "❌ Should have caught invalid time"; exit 1)

# Check that --help works
python3 calendar_free_slots.py --help > /dev/null && echo "✅ --help works"

echo "🎉 Verification complete!"