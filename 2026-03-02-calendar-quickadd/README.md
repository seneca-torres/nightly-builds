# Calendar Quick Add CLI

A lightweight Python CLI that adds Google Calendar events using natural language via the Google Calendar API's `quickAdd` endpoint.

## What it does
- Takes a natural language string (e.g., "Lunch with John tomorrow at 1pm for 1 hour")
- Calls Google Calendar API `events.quickAdd`
- Returns the created event's HTML link and details
- Falls back to structured creation if quickAdd fails

## Why it's useful
Victor's pain point: calendar management is cumbersome. This script reduces friction by accepting plain‑English descriptions instead of requiring separate date/time/attendee arguments.

## How to test
1. Ensure you have `~/clawd/config/gcp-oauth.keys.json` (Google OAuth credentials) and `~/clawd/config/calendar_token.json` (existing token) — if not, run `calendar_manager.py` once to generate the token.
2. If you see a `RefreshError`, your token may have expired. Re‑authenticate by running:
   ```bash
   cd ~/clawd && source venv/bin/activate && python3 scripts/calendar_manager.py --summary "Test" --date "2026-03-02" --start "10am" --end "10:30am"
   ```
   This will open a browser for OAuth approval. After that, the token will be refreshed and `calendar_quickadd.py` will work.
3. Run:
   ```bash
   cd ~/clawd/nightly-builds/2026-03-02-calendar-quickadd
   python3 calendar_quickadd.py "Meeting with team tomorrow 3pm for 30 minutes"
   ```
4. Check your Google Calendar for the new event.

## Dependencies
- `google-api-python-client`
- `google-auth-oauthlib`
- `google-auth-httplib2`

Already installed in `~/clawd/venv`.

## Safety
- No external packages beyond the trusted Google API client.
- Uses the same OAuth flow as existing `calendar_manager.py`.
- No production config changes.
- Only creates events in the primary calendar (no deletion/modification).

## Future improvements
- Integration with Telegram bot for one‑command calendar adds.
- Support for recurring events ("every Monday at 9am").
- Time‑zone detection from string (e.g., "EST").
- Attendee parsing ("with john@example.com").

## Files
- `calendar_quickadd.py` – main script
- `README.md` – this file