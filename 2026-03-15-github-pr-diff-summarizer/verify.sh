#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$(python3 "$ROOT/pr_diff_summarizer.py" --demo --demo-diff "$ROOT/sample_diff.txt")"

echo "$OUT" | grep -q '^# PR Diff Summary$'
echo "$OUT" | grep -q '^| File | Status | Additions | Deletions |$'
echo "$OUT" | grep -q '^\- \*\*Total additions:\*\* '
echo "$OUT" | grep -q 'src/new_feature.py'
echo "$OUT" | grep -q '^## Suspicious Patterns$'

echo "verify.sh: OK"