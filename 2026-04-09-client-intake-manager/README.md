# Client Intake & Onboarding Manager

A CLI tool that helps Victor manage new client inquiries efficiently for his sports analytics business. Reduces context-switching by providing structured workflows for different client types.

## 🎯 Purpose

Victor receives inquiries from various sources (coaches, analysts, broadcasters, schools, agents) and needs to track them through the sales funnel. This tool:

1. **Tracks client inquiries** from initial contact through to onboarding
2. **Provides structured workflows** for different client types
3. **Generates professional client briefs** automatically
4. **Integrates with existing tools** (calendar, CRM, etc.)
5. **Creates follow-up tasks and reminders**
6. **Shows pipeline metrics** for business visibility

## ✨ Features

- **📋 Client Management**: Add, update, and search clients with contact info
- **📊 Status Tracking**: New → Contacted → Discovery Call → Proposal Sent → Onboarded → Archived
- **📅 Scheduling**: Schedule calls, meetings, and follow-ups
- **📝 Brief Generation**: Professional markdown briefs with all client info
- **✅ Task Management**: Priority-based follow-up tasks
- **📈 Dashboard**: Real-time pipeline metrics and recent activity
- **🔍 Search & Filter**: Find clients by type, status, or source
- **📤 Export**: Export client data to CSV for analysis

## 🚀 Quick Start

### Installation

```bash
# Clone the repository or copy files
cd ~/clawd/nightly-builds/2026-04-09-client-intake-manager

# Make the script executable
chmod +x client_intake_manager.py

# Run verification test
python3 verify.py
```

### Basic Usage

```bash
# Show help
python3 client_intake_manager.py --help

# Add a new client inquiry
python3 client_intake_manager.py add \
  --name "Coach John Smith" \
  --type coach \
  --source referral \
  --email john@example.com \
  --notes "Interested in QB analytics"

# Update client status
python3 client_intake_manager.py update-status 1 \
  --status discovery-call \
  --notes "Scheduled for Friday"

# Schedule an interaction
python3 client_intake_manager.py schedule 1 \
  --type call \
  --time "2026-04-12 15:00" \
  --notes "Discovery call"

# Generate a client brief
python3 client_intake_manager.py generate-brief 1 \
  --output ./briefs/

# Show dashboard
python3 client_intake_manager.py dashboard

# Search for clients
python3 client_intake_manager.py search --type coach --status new

# Export to CSV
python3 client_intake_manager.py export --output clients.csv
```

## 📊 Database Schema

The tool uses SQLite with the following tables:

```sql
clients          - Client information and status
interactions     - Record of all client interactions
tasks            - Follow-up tasks with priorities
briefs           - Generated client briefs
```

## 🧪 Verification

Run the verification script to test all functionality:

```bash
python3 verify.py
```

This will:
1. Test all major CLI commands
2. Create sample data
3. Generate test briefs
4. Verify database operations
5. Clean up test files

## 🔗 Integration with Existing Tools

### Coach CRM
The tool can be extended to read from `~/clawd/coach-crm/contacts/*.md` for existing contacts.

### Calendar Integration
Future enhancement: Use `gog` CLI to schedule Google Calendar events automatically.

### Obsidian Integration
Generated briefs are markdown files ready for Obsidian. Store them in `~/obsidian-vault/Clients/`.

### Slack Integration
Future enhancement: Post notifications to Slack when new inquiries arrive or status changes.

## 📋 Example Workflow

1. **New Inquiry**: Client emails Victor about analytics services
   ```bash
   python3 client_intake_manager.py add \
     --name "Alex Turner" \
     --type analyst \
     --source email \
     --email alex@team.com \
     --notes "Wants defensive scheme analysis"
   ```

2. **Initial Contact**: Send welcome email
   ```bash
   python3 client_intake_manager.py update-status 1 \
     --status contacted \
     --notes "Sent welcome email with portfolio"
   ```

3. **Schedule Discovery**: Set up a call
   ```bash
   python3 client_intake_manager.py schedule 1 \
     --type call \
     --time "2026-04-15 14:00" \
     --notes "30-minute discovery call"
   ```

4. **Prepare for Call**: Generate brief
   ```bash
   python3 client_intake_manager.py generate-brief 1 \
     --output ~/obsidian-vault/Clients/
   ```

5. **Post-Call Follow-up**: Update status and add tasks
   ```bash
   python3 client_intake_manager.py update-status 1 \
     --status proposal-sent \
     --notes "Call went well, sent proposal"
   
   python3 client_intake_manager.py add-task 1 \
     --description "Follow up on proposal in 3 days" \
     --priority 2
   ```

## 🎨 Dashboard Preview

The dashboard shows:
- Pipeline status counts
- Client type breakdown
- Recent inquiries
- Upcoming tasks with priorities

```
📊 CLIENT INTAKE DASHBOARD
============================================================

📈 Pipeline Status:
  🆕 New: 3
  📞 Contacted: 2
  📅 Discovery Call: 1
  📄 Proposal Sent: 1
  ✅ Onboarded: 0
  📁 Archived: 0

👥 Client Types:
  • Coach: 3
  • Analyst: 2
  • Broadcaster: 1

🆕 Recent Inquiries:
  #5: Mike Williams (new) - 2026-04-09
  #4: Sarah Johnson (contacted) - 2026-04-09
  #3: Coach John Smith (discovery-call) - 2026-04-08

✅ Upcoming Tasks:
  ⭐⭐⭐ Alex Turner: Follow up on proposal (2026-04-12)
  ⭐⭐ Sarah Johnson: Send case studies (2026-04-11)
```

## 🔧 Customization

### Client Types
Add new client types by modifying the `client_type` CHECK constraint in the database schema.

### Status Flow
The status flow can be customized by updating the valid status values in the code.

### Brief Templates
Modify the `generate_brief` method to customize the markdown output format.

## 📝 License

Part of Victor's nightly builds collection. Free to use and modify.

## 🤝 Contributing

This is a nightly build prototype. Feedback and improvements welcome!

---

*Built during Nightly Build #53 on April 9, 2026*