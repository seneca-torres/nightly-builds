# Meeting Assistant

A CLI tool that helps Victor prepare for meetings with coaches and analysts by pulling together information from multiple sources.

## 🎯 Purpose

Victor frequently meets with coaches, analysts, and clients for his sports analytics business. Preparing for these meetings involves checking:
- Contact information from the CRM
- Upcoming calendar events
- Recent interactions from memory files
- Relevant GitHub issues/PRs
- Project context

This tool automates that preparation, saving time and ensuring Victor is well-informed before each meeting.

## ✨ Features

- **📇 Contact Integration**: Reads from the existing coach-crm at `~/clawd/coach-crm/contacts/*.md`
- **📅 Calendar Check**: Pulls upcoming meetings from Google Calendar via `gog` CLI
- **🗣️ Interaction History**: Searches memory files for recent mentions (last 30 days)
- **🐙 GitHub Activity**: Finds relevant issues and PRs via `gh` CLI
- **📝 Quick Notes**: Provides a template for meeting notes
- **💾 Report Saving**: Saves meeting prep reports as markdown files
- **🚀 Demo Mode**: Works without external dependencies using sample data

## 📁 Project Structure

```
2026-04-07-meeting-assistant/
├── meeting_assistant.py      # Main CLI tool
├── verify.py                 # Verification script
└── README.md                 # This file
```

## 🚀 Installation & Setup

The tool has **zero external dependencies** - it uses only Python's standard library.

### Optional Dependencies (for full functionality):

1. **gog CLI** - For Google Calendar integration:
   ```bash
   # Install gog if not already installed
   npm install -g gog-cli
   gog auth login
   ```

2. **gh CLI** - For GitHub integration:
   ```bash
   # Install gh CLI
   brew install gh
   gh auth login
   ```

3. **Coach CRM** - Should be at `~/clawd/coach-crm/`

## 🛠️ Usage

### Basic Commands

```bash
# Prepare for a meeting with a specific contact
python3 meeting_assistant.py prepare "Coach Name"

# Save the report to a file
python3 meeting_assistant.py prepare "Coach Name" --save

# List all contacts in the CRM
python3 meeting_assistant.py list

# Search for contacts and interactions
python3 meeting_assistant.py search "query"

# Run in demo mode with sample data
python3 meeting_assistant.py demo
```

### Example Workflow

```bash
# 1. See who's in your CRM
python3 meeting_assistant.py list

# 2. Prepare for meeting with Dan Casey
python3 meeting_assistant.py prepare "Dan Casey" --save

# 3. Check what's saved
ls meeting_prep_*.md
```

## 📋 Output Format

The tool generates a color-coded terminal report with these sections:

```
╔═══════════════════════════════════════════════════╗
║           MEETING PREPARATION REPORT             ║
╚═══════════════════════════════════════════════════╝

📇 CONTACT INFORMATION
────────────────────────────────────────
Name: Coach John Smith
Title: Offensive Coordinator
Organization: University of Arizona
...

📅 UPCOMING MEETINGS
────────────────────────────────────────
1. Weekly Sync with Coach
   Time: 2026-04-07 10:00:00
...

🗣️ RECENT INTERACTIONS (Last 30 days)
────────────────────────────────────────
1. Date: 2026-03-15
   Context: Had call with Coach Smith about...

🐙 GITHUB ACTIVITY
────────────────────────────────────────
1. ⏳ PR #42 Add coach profile page
   Repo: seneca-torres/coach-database

📝 QUICK NOTES (Add your own notes below)
────────────────────────────────────────
1. 
2. 
3. 
```

## 🔧 Integration Points

### 1. Coach CRM
- Location: `~/clawd/coach-crm/contacts/*.md`
- Format: Markdown with YAML frontmatter
- Required fields: `name`, `email` (for calendar lookup)

### 2. Google Calendar (via gog CLI)
- Command: `gog calendar events list --attendees <email> --from now --to +7d --format json`
- Fallback: Demo data if gog not available

### 3. Memory Files
- Searches: `~/clawd/memory/daily/*.md` (last 30 days)
- Looks for: Contact name mentions in daily logs

### 4. GitHub (via gh CLI)
- Searches: Issues/PRs mentioning or assigned to contact
- Repos: seneca-torres/nightly-builds, coach-database, pbp-parser, pbp-analysis

## 🧪 Testing

Run the verification script to test all features:

```bash
python3 verify.py
```

The verification script tests:
- Basic CLI functionality
- Demo mode
- Search functionality  
- File creation
- Import dependencies
- Code style

## ⚠️ Error Handling

The tool gracefully handles missing dependencies:
- **Missing gog CLI**: Shows warning, uses demo calendar data
- **Missing gh CLI**: Shows warning, skips GitHub check
- **Missing CRM**: Shows warning, continues with name-only search
- **Missing calendar access**: Shows warning, uses demo data

## 🔒 Security

- **Read-only**: Never modifies existing files (unless saving reports)
- **No API keys**: Uses existing CLI tools (gog, gh) for authentication
- **Local only**: All data stays on your machine
- **Demo mode**: Can test without external dependencies

## 🤝 Integration with Existing Tools

This tool complements several existing nightly-build tools:

1. **Coach CRM** (2026-02-01) - Provides contact data
2. **Calendar Quick Add** (2026-03-02) - Related calendar tool
3. **Calendar Conflict Detector** (2026-03-12) - Complementary calendar analysis
4. **Project Context Switcher** (2026-03-27) - Could integrate for project context

## 🎨 Design Decisions

1. **Zero Dependencies**: Uses only Python standard library for reliability
2. **Graceful Degradation**: Works even when external tools are missing
3. **Color-coded Output**: Easy to scan in terminal
4. **File-based Storage**: Simple markdown files for reports
5. **Fuzzy Matching**: Finds contacts with partial name matches

## 📈 Future Enhancements

Potential improvements (if this proves useful):

1. **Web Interface**: Flask/Dash dashboard version
2. **Calendar Integration**: Direct Google Calendar API (not just gog)
3. **Email Integration**: Check recent email threads
4. **Project Context**: Pull from project context switcher
5. **Meeting Notes**: Post-meeting note taking and follow-up tracking
6. **Integration with Daily Check-in**: Morning briefing inclusion

## 🙏 Credits

Built as part of the nightly "Surprise Me" build series. Addresses Victor's need for efficient meeting preparation across his coaching/analyst network.

---

**Last Updated**: 2026-04-07  
**Built By**: Seneca (Victor's AI Assistant)  
**Category**: Productivity, Meeting Preparation