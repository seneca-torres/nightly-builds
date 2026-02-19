# Voice Note Summary

A simple Python CLI that extracts voice message transcriptions from Clawdbot Telegram session JSONL files and archives them into daily Markdown logs. The goal: you can look back and see what you said in voice messages without re-listening to audio files.

## What it does

- Reads session transcripts from `~/.clawdbot/sessions/*.jsonl`
- Extracts voice messages with transcription text
- Writes daily logs to `~/clawd/voice-notes/YYYY-MM-DD.md`
- Each entry includes timestamp, sender, transcription text, and file path (if available)

## Requirements

- Python 3.8+
- Standard library only (no external dependencies)

## Usage

```bash
python3 voice_note_summary.py
```

Process a specific date:

```bash
python3 voice_note_summary.py --date 2026-02-13
```

Process all dates found in the sessions:

```bash
python3 voice_note_summary.py --all
```

Custom output directory:

```bash
python3 voice_note_summary.py --output-dir ~/notes/voice-archive
```

## Sample output

Example content of `~/clawd/voice-notes/2026-02-13.md`:

```markdown
# Voice Notes - 2026-02-13

- `2026-02-13 08:14:03 UTC` **Victor**
  Walking through the launch plan for next week—need to finalize the metrics dashboard.
  File: `~/Downloads/voice_2026-02-13_081403.ogg`

- `2026-02-13 14:57:22 UTC` **Victor**
  Reminder: follow up with Ben about the storage budget for Q2.
```

## Cron setup (daily)

Run every day at 9:05 PM local time:

```bash
crontab -e
```

Add:

```bash
5 21 * * * /usr/bin/env python3 /Users/vicmacmini/clawd/nightly-builds/2026-02-13-voice-note-summary/voice_note_summary.py >> /Users/vicmacmini/clawd/voice-notes/cron.log 2>&1
```

Tip: If you want to always use the default output directory, the command above is sufficient. If you prefer a custom output directory, add `--output-dir` to the cron command.

## Notes

- The tool is resilient to missing or malformed lines in JSONL files.
- If a voice message doesn’t include transcription text, it’s skipped.
- If no session files are found, the tool exits gracefully.
