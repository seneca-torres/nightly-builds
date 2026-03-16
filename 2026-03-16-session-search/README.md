# session_search

`session_search.py` is a Python 3.9+ CLI tool to search OpenClaw session JSONL files for matching messages, with filters and context.

It scans:

`~/.openclaw/agents/main/sessions/*.jsonl`

Each line is expected to be a JSON object (for example: `role`, `content`, `timestamp`, `sessionId`).

## Features

- Case-insensitive search by default
- Optional case-sensitive mode
- Optional regex mode
- Filters by `sessionId` and `role`
- Context lines before/after a match
- Output formats: `text`, `json`, `markdown`
- Handles malformed JSON lines gracefully
- `--demo` mode with generated sample data
- No external dependencies (standard library only)

## Installation

No installation needed beyond Python 3.9+.

Optional:
```bash
chmod +x session_search.py
```

## Usage

Basic:
```bash
python3 session_search.py "health check"
```

Case-sensitive:
```bash
python3 session_search.py "Health Check" --case-sensitive
```

Regex search:
```bash
python3 session_search.py "health\\s+check" --regex
```

Limit results and context:
```bash
python3 session_search.py "release" --limit 5 --context 2
```

Filter by role/session:
```bash
python3 session_search.py "deploy" --role assistant --session-id abc123
```

JSON output:
```bash
python3 session_search.py "incident" --output-format json
```

Markdown output:
```bash
python3 session_search.py "incident" --output-format markdown
```

Verbose logging:
```bash
python3 session_search.py "release" --verbose
```

Demo mode:
```bash
python3 session_search.py "health" --demo
```

## Testing

Use demo mode:
```bash
python3 session_search.py "health" --demo
```

Or run the verification script:
```bash
bash verify.sh
```