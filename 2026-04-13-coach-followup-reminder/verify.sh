#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
TMP_HOME=$(mktemp -d)
CONTACTS_DIR="$TMP_HOME/clawd/coach-crm/contacts"
mkdir -p "$CONTACTS_DIR"
trap 'rm -rf "$TMP_HOME"' EXIT

python3 - <<'PY' "$CONTACTS_DIR"
from datetime import date, timedelta
from pathlib import Path
import sys

contacts_dir = Path(sys.argv[1])
today = date.today()

samples = {
    "overdue.md": f"""---
name: Overdue Coach
role: Head Coach
school: Redwood Prep
next_followup: {(today - timedelta(days=3)).isoformat()}
---
# Overdue Coach
""",
    "due_today.md": f"""---
name: Today Coach
role: Assistant Coach
school: Lakeside High
next_followup: {today.isoformat()}
---
# Today Coach
""",
    "due_soon.md": f"""---
name: Soon Coach
role: Recruiting Coordinator
school: Summit College
next_followup: {(today + timedelta(days=4)).isoformat()}
---
# Soon Coach
""",
    "later.md": f"""---
name: Later Coach
role: Director
school: Valley Academy
next_followup: {(today + timedelta(days=12)).isoformat()}
---
# Later Coach
""",
    "missing_followup.md": """---
name: Missing Followup
role: Coach
school: Example School
---
# Missing Followup
""",
    "malformed.md": """---
name Malformed Coach
next_followup: 2026-01-01
---
# Malformed
""",
    "invalid_date.md": """---
name: Invalid Date Coach
role: Coach
school: Example School
next_followup: 2026-99-99
---
# Invalid Date
""",
}

for filename, content in samples.items():
    (contacts_dir / filename).write_text(content, encoding="utf-8")
PY

TEXT_OUTPUT=$(HOME="$TMP_HOME" python3 "$ROOT_DIR/coach_followup_reminder.py")
JSON_OUTPUT=$(HOME="$TMP_HOME" python3 "$ROOT_DIR/coach_followup_reminder.py" --output-format json)
VERBOSE_STDERR=$(mktemp)
HOME="$TMP_HOME" python3 "$ROOT_DIR/coach_followup_reminder.py" --verbose >/dev/null 2>"$VERBOSE_STDERR"

printf '%s\n' "$TEXT_OUTPUT"
printf '\n--- JSON verification ---\n'
printf '%s\n' "$JSON_OUTPUT"

printf '%s\n' "$TEXT_OUTPUT" | grep -F "Overdue Coach"
printf '%s\n' "$TEXT_OUTPUT" | grep -F "Today Coach"
printf '%s\n' "$TEXT_OUTPUT" | grep -F "Soon Coach"
if printf '%s\n' "$TEXT_OUTPUT" | grep -F "Later Coach" >/dev/null; then
  echo "Verification failed: Later Coach should not appear in reminders." >&2
  exit 1
fi
printf '%s\n' "$TEXT_OUTPUT" | grep -F "Summary: 1 overdue, 2 due soon, 3 total"
grep -F "Processing" "$VERBOSE_STDERR" >/dev/null

JSON_PAYLOAD="$JSON_OUTPUT" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["JSON_PAYLOAD"])
assert payload["summary"] == {"overdue": 1, "due_soon": 2, "total": 3}
assert len(payload["contacts"]) == 3
statuses = {item["name"]: item["status"] for item in payload["contacts"]}
assert statuses["Overdue Coach"] == "overdue"
assert statuses["Today Coach"] == "due soon"
assert statuses["Soon Coach"] == "due soon"
assert payload["scan_stats"]["parse_errors"] == 2
PY

rm -f "$VERBOSE_STDERR"
echo "Verification passed."
