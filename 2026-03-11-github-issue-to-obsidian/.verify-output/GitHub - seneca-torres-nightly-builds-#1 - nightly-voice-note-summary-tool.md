---
title: 'nightly: voice note summary tool'
source: 'github'
repo: 'seneca-torres/nightly-builds'
issue_number: 1
state: 'MERGED'
created_at: '2026-02-13T09:02:28Z'
updated_at: '2026-02-19T18:15:31Z'
assignees: []
labels: []
milestone: ''
url: 'https://github.com/seneca-torres/nightly-builds/pull/1'
---

Python CLI that extracts voice message transcriptions from Clawdbot session JSONL files and archives them into daily Markdown logs.

Features:
- Reads session transcripts from ~/.clawdbot/sessions/*.jsonl
- Extracts voice messages with transcription text
- Writes daily logs to ~/clawd/voice-notes/YYYY-MM-DD.md
- CLI options: --date (specific date), --all (process all dates), --output-dir (custom location)
- Graceful handling of missing files/malformed lines
- No external dependencies (standard library only)

Each entry includes:
- Timestamp (UTC)
- Sender name
- Transcription text
- File path (if available)

Usage:
```bash
python3 voice_note_summary.py                    # Today
python3 voice_note_summary.py --date 2026-02-13 # Specific date
python3 voice_note_summary.py --all             # All dates
```

Can be run daily via cron to maintain an archive of voice notes.

## Comments
No comments fetched yet.
