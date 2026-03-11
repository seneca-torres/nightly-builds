#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL="$SCRIPT_DIR/github_issue_to_obsidian.py"
OUT_DIR="$SCRIPT_DIR/.verify-output"
URL="https://github.com/seneca-torres/nightly-builds/issues/1"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

python3 "$TOOL" --url "$URL" --output-dir "$OUT_DIR"

created_file_count=$(find "$OUT_DIR" -maxdepth 1 -type f -name 'GitHub - *.md' | wc -l | tr -d ' ')
if [[ "$created_file_count" != "1" ]]; then
  echo "Verification failed: expected 1 markdown file, found $created_file_count"
  exit 1
fi

created_file=$(find "$OUT_DIR" -maxdepth 1 -type f -name 'GitHub - *.md' | head -n1)

grep -q "^title:" "$created_file" || { echo "Verification failed: missing title in frontmatter"; exit 1; }
grep -q "^source: 'github'$" "$created_file" || { echo "Verification failed: missing source in frontmatter"; exit 1; }
grep -q "^repo: 'seneca-torres/nightly-builds'$" "$created_file" || { echo "Verification failed: wrong repo"; exit 1; }
grep -q "^issue_number: 1$" "$created_file" || { echo "Verification failed: wrong issue_number"; exit 1; }
grep -q "^url: 'https://github.com/seneca-torres/nightly-builds/" "$created_file" || { echo "Verification failed: url mismatch"; exit 1; }
grep -q "^## Comments$" "$created_file" || { echo "Verification failed: missing comments header"; exit 1; }
grep -q "^No comments fetched yet\.$" "$created_file" || { echo "Verification failed: missing comments placeholder"; exit 1; }

echo "Verification passed: $created_file"