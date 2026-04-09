# Bot Launcher

This tool helps you quickly scaffold a new single-purpose Clawdbot bot instance with boilerplate, config and instructions.

## Usage

```
python bot_launcher.py create --name 'BotName' --purpose 'Short bot purpose' --telegram-bot-name 'bot_username'
```

- This creates a folder with the given bot name (sanitized: lowercased, spaces→dashes).
- Each file has sensible defaults with TODO markers for customization.
- After generation, fill in the placeholders and hook up your bot as needed.

## Files/directories generated

- `SOUL.md`, `AGENTS.md`, `IDENTITY.md`, `HEARTBEAT.md`, `USER.md`, `TOOLS.md`: Bot meta-instructions & placeholders.
- `config-template.json`: Example starter config for Clawdbot with TODOs.
- `<botname>.service`: Systemd template.
- `setup.sh`: Shell script to help install/configure.
