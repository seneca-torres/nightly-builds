# Tool Recommender 🛠️

Prevents tool duplication by recommending existing tools when someone describes what they need.

## The Problem

Victor has built **46+ nightly tools** (as of March 2026) plus numerous utilities in `TOOLS_REGISTRY.md`. It's easy to:
1. Forget an existing tool that already solves the problem
2. Build a duplicate with slightly different features
3. Waste time reinventing the wheel

This tool helps enforce the **DRY Rule** from `AGENTS.md`: "Before building anything new: check `TOOLS_REGISTRY.md` — does this already exist?"

## How It Works

1. **Scans** `TOOLS_REGISTRY.md` and the `nightly-builds` directory
2. **Indexes** tool names, descriptions, and usage contexts
3. **Matches** natural language queries using TF-IDF similarity
4. **Recommends** the top 3 most relevant existing tools
5. **Shows** location, description, and usage examples

## Installation

No installation needed — it's a standalone Python script.

```bash
cd ~/clawd/nightly-builds/2026-03-28-tool-recommender
python3 tool_recommender.py --help
```

## Usage

### Basic Search
```bash
# Search for existing tools
python3 tool_recommender.py "search session logs"
python3 tool_recommender.py "calendar management"
python3 tool_recommender.py "github pull requests"
python3 tool_recommender.py "football data"
```

### Tool Statistics
```bash
# See how many tools we have, by category
python3 tool_recommender.py --stats
```

### List All Tools
```bash
# Browse everything we've built
python3 tool_recommender.py --list
```

### Add New Tools
```bash
# When you build something new, add it to the registry
python3 tool_recommender.py --learn
```

### Demo Mode
```bash
# See example queries and results
python3 tool_recommender.py --demo
```

## Example Output

```
🔍 Searching for: 'search session logs'
✅ Found 2 matching tools:

1. session_search.py (score: 0.85)
   📍 Source: nightly-builds/2026-03-16-session-search
   📝 Searches OpenClaw session JSONL files for matching messages with filters
   🕐 When to use: Finding past conversations, decisions, or references
   📂 Location: ~/clawd/nightly-builds/2026-03-16-session-search/session_search.py
   📅 Added: 2026-03-16

2. conversation_stats.py (score: 0.42)
   📍 Source: nightly-builds/2026-03-15-conversation-stats
   📝 Analyzes session JSONL files for conversation analytics
   📂 Location: ~/clawd/nightly-builds/2026-03-15-conversation-stats/conversation_stats.py
   📅 Added: 2026-02-15
```

## How It Prevents Duplication

Before building something new, ask the Tool Recommender:

```bash
# Before: "I need a tool to analyze calendar events"
python3 tool_recommender.py "analyze calendar events"

# Output might show:
# 1. calendar_duration_analyzer.py (already exists!)
# 2. calendar_conflict_detector.py (also exists!)
# 3. calendar_quickadd.py (exists too!)

# Result: Don't build — use what we already have!
```

## Integration with Workflow

Add to your pre-build checklist:

1. **Hear a need**: "I need a tool to X"
2. **Check first**: `python3 tool_recommender.py "X"`
3. **If matches exist**: Extend existing tool instead of building new
4. **If no matches**: Build new, then `--learn` to register it

## Features

- **Natural language search**: Uses TF-IDF to match queries
- **Multiple sources**: Scans both TOOLS_REGISTRY.md and nightly-builds/
- **Category filtering**: Tools grouped by purpose (Visualization, Data, Calendar, etc.)
- **Statistics dashboard**: See what categories dominate
- **Learning mode**: Add new tools to keep registry current
- **Demo mode**: Example queries to test the system
- **Zero dependencies**: Standard library only

## Verification

Run the verification script to ensure everything works:

```bash
python3 verify_tool_recommender.py
```

This tests:
- Loading tools from TOOLS_REGISTRY.md
- Scanning nightly-builds directory
- Search functionality
- Statistics reporting

## Why This Matters

Victor's time is limited. Every duplicate tool:
- ⏰ Wastes build time
- 📦 Adds maintenance burden
- 🤯 Creates cognitive load ("which tool do I use?")
- 📈 Dilutes focus from core projects

This tool embodies Seneca's **DRY Rule** and helps Victor's sports analytics business stay lean and focused.

## Future Improvements

Potential enhancements:
- Track actual usage frequency (which tools get run most)
- Suggest deprecated tools that should be removed
- Integration with Codex prompts ("before you code, check for existing tools")
- Web interface for browsing tools
- Auto-suggest when Victor types "I need a tool to..." in chat

---

*Built as Nightly Build #47 on March 28, 2026*