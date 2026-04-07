# Telegram Quick Reply Bot

## 🤖 Overview

A flexible Telegram bot that generates quick reply buttons for common actions and messages. Useful for rapid task management, standardized responses, and interaction tracking.

## ✨ Features

- Define custom reply templates in YAML
- Generate inline keyboard buttons
- Audit logging of all interactions
- Easy to extend with new templates

## 🚀 Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/victorres11/quick-reply-bot.git
   cd quick-reply-bot
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Telegram Bot Token**
   ```bash
   export TELEGRAM_BOT_TOKEN='your_bot_token_here'
   ```

5. **Customize Templates**
   Edit `config.yaml` to add or modify reply templates

## 🕹️ Usage

### Starting the Bot
```bash
python3 quick_reply_bot.py
```

### Telegram Commands
- `/start`: List available quick reply templates
- `/quick template_name`: Generate quick reply buttons for a specific template

## 📋 Customization

Modify `config.yaml` to add new templates:

```yaml
templates:
  my_template:
    type: inline_keyboard
    buttons:
      - text: "Option 1"
        action: option1_action
      - text: "Option 2"
        action: option2_action
```

## 🔍 Audit Logging

All button interactions are logged to `~/.clawdbot/quick_reply_audit.log`

## 🛡️ Security

- Secure callback handling
- Minimal external dependencies
- Configurable through YAML

## 🔧 TODO
- Add more template types
- Implement persistent storage for templates
- Create admin commands for template management

---

**Nightly Build:** 2026-02-08
**Creator:** Seneca (Victor's AI Assistant)