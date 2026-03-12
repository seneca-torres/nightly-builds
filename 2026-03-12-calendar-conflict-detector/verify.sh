#!/usr/bin/env bash
set -euo pipefail

set +e
OUTPUT="$(python3 calendar_conflict_detector.py --demo --days 7 --min-break 5 2>&1)"
STATUS=$?
set -e

if [[ $STATUS -ne 0 ]]; then
  echo "Verification failed: expected exit code 0, got $STATUS"
  echo "$OUTPUT"
  exit 1
fi

if ! grep -q "| Type | Events | Conflict Details | Suggested Action |" <<<"$OUTPUT"; then
  echo "Verification failed: markdown table header not found."
  echo "$OUTPUT"
  exit 1
fi

if ! grep -q "Overlap" <<<"$OUTPUT"; then
  echo "Verification failed: expected an overlap conflict in demo mode."
  echo "$OUTPUT"
  exit 1
fi

if ! grep -q "Back-to-back" <<<"$OUTPUT"; then
  echo "Verification failed: expected a back-to-back conflict in demo mode."
  echo "$OUTPUT"
  exit 1
fi

echo "Verification passed."
