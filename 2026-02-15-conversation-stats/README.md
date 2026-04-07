# 📊 Conversation Stats Analyzer

A Python CLI tool that parses Clawdbot session JSONL files and generates fun analytics about your conversations.

## What It Does

This tool analyzes your Clawdbot conversation history and extracts insights like:

- **Message Counts** — Total messages, user vs assistant breakdown
- **Response Times** — Average and median response time for assistant replies
- **Active Hours** — When you have the most conversations
- **Top Keywords** — Most frequently discussed topics
- **Message Lengths** — Average length of user vs assistant messages
- **Token Usage** — Total tokens used and daily trends
- **Daily Breakdown** — Activity patterns over time

## How It Works

The analyzer:
1. Scans `~/.clawdbot/sessions/` for JSONL session files
2. Parses messages with timestamps, roles, and metadata
3. Computes statistics across your selected time range
4. Outputs formatted text or JSON data

### Statistics Calculations

- **Response Time**: Time between a user message and the next assistant reply (only counts replies within 5 minutes to avoid counting async work)
- **Keywords**: Word frequency analysis with common stop words filtered out
- **Active Hours**: Messages grouped by hour of day (24-hour format)
- **Daily Breakdown**: Messages and tokens per day

## Usage

### Basic Commands

```bash
# Analyze today's conversations
python3 conversation_stats.py

# Analyze a specific date
python3 conversation_stats.py --date 2026-02-14

# Analyze last 7 days
python3 conversation_stats.py --week

# Analyze all time
python3 conversation_stats.py --all

# Output as JSON (for scripting/integration)
python3 conversation_stats.py --week --output json
```

### Custom Sessions Directory

```bash
python3 conversation_stats.py --sessions-dir ~/custom/sessions/path
```

## Sample Output

```
📊 Conversation Stats

==================================================

📅 Date Range: 2026-02-08 to 2026-02-15

💬 Total Messages: 847
   👤 User: 312
   🤖 Assistant: 535

⚡ Response Times:
   Average: 8.3s
   Median: 4.2s

📏 Average Message Length:
   User: 156 chars
   Assistant: 623 chars

🎫 Total Tokens: 234,567

🕐 Most Active Hours:
   14:00 - 89 messages
   10:00 - 76 messages
   16:00 - 68 messages

🔑 Top Keywords:
   codex: 45
   trello: 38
   build: 34
   session: 31
   project: 29
   deploy: 27
   error: 24
   data: 22
   file: 21
   script: 19

📆 Daily Breakdown:
   2026-02-09: 118 messages (42 user, 76 assistant) | 31,245 tokens
   2026-02-10: 94 messages (35 user, 59 assistant) | 28,901 tokens
   2026-02-11: 156 messages (58 user, 98 assistant) | 42,387 tokens
   2026-02-12: 103 messages (39 user, 64 assistant) | 29,672 tokens
   2026-02-13: 127 messages (47 user, 80 assistant) | 35,219 tokens
   2026-02-14: 89 messages (32 user, 57 assistant) | 24,508 tokens
   2026-02-15: 160 messages (59 user, 101 assistant) | 42,635 tokens
```

## JSON Output Format

```json
{
  "total_messages": 847,
  "user_messages": 312,
  "assistant_messages": 535,
  "date_range": {
    "start": "2026-02-08T08:23:14+00:00",
    "end": "2026-02-15T23:45:31+00:00"
  },
  "avg_response_time": 8.3,
  "median_response_time": 4.2,
  "avg_user_message_length": 156,
  "avg_assistant_message_length": 623,
  "total_tokens": 234567,
  "messages_by_day": {
    "2026-02-09": {"user": 42, "assistant": 76},
    "2026-02-10": {"user": 35, "assistant": 59}
  },
  "messages_by_hour": {
    "0": 12,
    "1": 8,
    "14": 89
  },
  "tokens_by_day": {
    "2026-02-09": 31245,
    "2026-02-10": 28901
  },
  "keywords": [
    ["codex", 45],
    ["trello", 38],
    ["build", 34]
  ]
}
```

## Dependencies

None! Uses only Python 3 standard library:
- `json` - JSONL parsing
- `argparse` - CLI interface
- `pathlib` - File system operations
- `datetime` - Timestamp handling
- `collections` - Data structures
- `re` - Text processing

## Use Cases

- **Daily Reviews** — See what you talked about today
- **Weekly Reports** — Track conversation patterns over time
- **Topic Analysis** — Discover what you discuss most
- **Activity Patterns** — Find your most productive hours
- **Token Monitoring** — Track API usage trends
- **Data Export** — Use JSON output for dashboards or further analysis

## Tips

- Run weekly to spot conversation trends
- Compare stats across different date ranges
- Use keywords to identify focus areas
- Track token usage to optimize costs
- Export JSON for custom visualizations

---

Built with ❤️ during nightly builds. Have fun exploring your conversation patterns! 🦉
