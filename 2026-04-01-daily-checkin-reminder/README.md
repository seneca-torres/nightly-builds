# Daily Check-in Reminder CLI 🦉

A friendly Python CLI tool to help Victor structure his day and maintain focus across context switches.

## What It Does

Victor context-switches a lot between day job and experimental projects. This tool provides a lightweight, structured way to start the day by:

1. **Reflecting on yesterday's wins** (builds momentum)
2. **Setting clear priorities** (reduces decision fatigue)
3. **Identifying blockers early** (prevents surprises)
4. **Tracking energy & focus** (helps with pacing)

All responses are saved to your daily memory file (`~/clawd/memory/daily/YYYY-MM-DD.md`) and can be easily copied to Slack/Telegram.

## Features

- **Three modes**: `full` (all questions), `quick` (just priorities), `review` (last 3 days)
- **Calendar integration**: Shows today's events (uses `gog` CLI if available, demo fallback)
- **Zero dependencies**: Standard library only
- **Human-friendly**: Emojis, clear prompts, no corporate jargon
- **Memory-compatible**: Appends to existing daily log format

## Installation

```bash
# Make executable (optional)
chmod +x daily_checkin.py

# Or run directly with Python
python3 daily_checkin.py [mode]
```

## Usage

### Full Check-in (recommended for mornings)
```bash
./daily_checkin.py full
```
Asks about:
- Yesterday's accomplishments (3-5 bullet points)
- Today's top 3 priorities
- Any blockers or decisions needed
- Energy level (1-5 scale)
- Primary focus area (Day Job, Sports Analytics, Personal, etc.)

### Quick Check-in (when time is short)
```bash
./daily_checkin.py quick
```
Just asks for today's top 3 priorities.

### Review Mode
```bash
./daily_checkin.py review
```
Shows check-ins from the last 3 days.

### With Calendar
```bash
./daily_checkin.py --calendar full
```
Shows today's calendar events before starting check-in.

### Specific Date
```bash
./daily_checkin.py --date 2026-04-01 full
```
Use a specific date instead of today.

## Example Output

```
🦉 Daily Check-in — Full Mode
========================================

🌟 What did you accomplish yesterday?
(Enter 3-5 bullet points, one per line. Empty line to finish)
  1. Fixed bug in PBP parser
  2. Reviewed PR #42
  3. Scheduled client call

🎯 Top 3 priorities for today:
  1. Finish coaching database schema
  2. Write project update email
  3. Research rental listings

🚧 Any blockers or decisions needed?
  Need to decide between React vs Vue for frontend

⚡ Energy level (1-5, where 5 = fully charged):
   [3]: 4

🎯 Primary focus area today:
  (Day Job, Sports Analytics, Personal, etc.) [Day Job]: Sports Analytics

✅ Check-in saved!

📋 Summary (copy to Slack/Telegram):
========================================
## Daily Check-in
### Yesterday's Wins
- Fixed bug in PBP parser
- Reviewed PR #42
- Scheduled client call

### Today's Priorities
1. Finish coaching database schema
2. Write project update email
3. Research rental listings

### Blockers/Decisions
- Need to decide between React vs Vue for frontend

### Energy & Focus
- Energy: 4/5
- Focus: Sports Analytics
========================================
```

## How It Works

1. **File Storage**: Entries are appended to `~/clawd/memory/daily/YYYY-MM-DD.md` in the existing format:
   ```
   - [09:15] 🎯 Daily check-in: Sports Analytics focus, energy 4/5
   ```

2. **Calendar Integration**: Uses the `gog` CLI if installed and authenticated. Falls back to demo events if not available.

3. **Error Handling**: Creates daily file if it doesn't exist, handles missing directories gracefully.

## Why This Helps

- **Context switching**: Explicitly declaring focus area helps mental transition
- **Decision fatigue**: Having priorities set reduces "what should I work on?" questions
- **Progress tracking**: Yesterday's wins build momentum and combat imposter syndrome
- **Blockers visibility**: Early identification prevents wasted time
- **Energy awareness**: Helps pace work and avoid burnout

## Integration Ideas

- **Morning routine**: Add to `.zshrc` alias: `alias morning="./daily_checkin.py full --calendar"`
- **Cron job**: Run automatically at 9 AM (though manual reflection is more valuable)
- **Team standups**: Copy-paste summary to Slack/Telegram
- **Weekly reviews**: Use `review` mode to see patterns

## Verification

Run the test to ensure everything works:

```bash
# Test basic functionality
python3 daily_checkin.py --help

# Test quick mode with demo
echo -e "Task 1\nTask 2\nTask 3" | python3 daily_checkin.py quick

# Test review mode
python3 daily_checkin.py review

# Test with calendar (will show demo if gog not authenticated)
python3 daily_checkin.py --calendar quick
```

## Files Created

- `daily_checkin.py` - Main CLI tool
- `README.md` - This file

## Notes

- Uses Victor's existing memory system (`~/clawd/memory/daily/`)
- Compatible with other tools like `quicklog.py` and `update_daily_log.py`
- No external dependencies = safe to run anywhere
- Demo calendar events shown if `gog` CLI not available/authenticated

## Future Enhancements

1. **Slack/Telegram auto-post**: Option to send summary directly
2. **Weekly summary**: Generate week-in-review from daily check-ins
3. **Focus time tracking**: Track how long spent in each focus area
4. **Integration with project context switcher**: Auto-set environment based on focus area

---

Built as part of Nightly Builds 🌙 | 2026-04-01