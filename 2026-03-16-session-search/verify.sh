#!/usr/bin/env bash
set -euo pipefail

OUT="$(python3 session_search.py health --demo)"
echo "$OUT"

if echo "$OUT" | grep -qi "health"; then
  echo "verify.sh: PASS"
  exit 0
else
  echo "verify.sh: FAIL (expected output to contain 'health')" >&2
  exit 1
fi