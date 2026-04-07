import os
import sys
import argparse
from pathlib import Path

SOUL_MD = """# Personality\nTODO: Define the bot's personality and quirks here.\n"""

AGENTS_MD = """# Bot Instructions\nTODO: Describe bot-specific behavior, goals, and constraints here.\n"""

IDENTITY_MD = """# Identity\nemoji: 🤖\nname: {bot_name}\n"""

HEARTBEAT_MD = """# Heartbeat\nTODO: Describe how/when your bot should signal it's healthy.\n"""

USER_MD = """# USER\nTODO: Customize user-related instructions.\n"""

TOOLS_MD = """# TOOLS\nTODO: List and describe supported tools for this bot.\n"""

def get_config_template(bot_name, purpose, telegram_bot_name):
    return f'''{{"bot_name": "{bot_name}",
  "purpose": "{purpose}",
  "telegram_bot_name": "{telegram_bot_name}",
  "// TODO": "Fill out Clawdbot config fields"
}}'''

def get_systemd_service(bot_name, user):
    return f'''[Unit]
Description={bot_name} Clawdbot
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/bot  # TODO: Set full path
ExecStart=/usr/bin/clawdbot gateway start
Restart=always
User={user}

[Install]
WantedBy=multi-user.target
'''

SETUP_SH = """#!/bin/bash\n# Setup script for your new Clawdbot bot\n\necho \"[TODO] Install dependencies and configure your bot here.\"\n"""

def sanitize(name):
    # Lowercase, replace spaces with dashes, basic clean
    return name.strip().replace(' ', '-').replace('_', '-').lower()

def create_bot(args):
    bot_name = args.name
    bot_dirname = sanitize(bot_name)
    purpose = args.purpose
    telegram_bot_name = args.telegram_bot_name
    cwd = os.getcwd()
    user = os.getenv('USER', 'botuser')

    target_path = Path(bot_dirname)
    if target_path.exists():
        print(f"[Error] Directory '{bot_dirname}' already exists.")
        sys.exit(1)
    target_path.mkdir()

    # Main files
    (target_path / 'SOUL.md').write_text(SOUL_MD)
    (target_path / 'AGENTS.md').write_text(AGENTS_MD)
    (target_path / 'IDENTITY.md').write_text(IDENTITY_MD.format(bot_name=bot_name))
    (target_path / 'HEARTBEAT.md').write_text(HEARTBEAT_MD)
    (target_path / 'USER.md').write_text(USER_MD)
    (target_path / 'TOOLS.md').write_text(TOOLS_MD)
    (target_path / 'config-template.json').write_text(get_config_template(bot_name, purpose, telegram_bot_name))
    (target_path / f"{bot_dirname}.service").write_text(get_systemd_service(bot_name, user))
    (target_path / 'setup.sh').write_text(SETUP_SH)
    os.chmod(target_path / 'setup.sh', 0o755)

    print(f"[OK] Created bot in '{bot_dirname}/'.\nFill the placeholders (TODO) as needed.")

def main():
    parser = argparse.ArgumentParser(description='Bot Launcher: Clawdbot scaffolding tool')
    subparsers = parser.add_subparsers(dest='command')
    create_p = subparsers.add_parser('create', help='Create new bot project')
    create_p.add_argument('--name', required=True, help='Bot name')
    create_p.add_argument('--purpose', required=True, help='Short description')
    create_p.add_argument('--telegram-bot-name', required=True, help='Telegram Bot @username')

    args = parser.parse_args()
    if args.command == 'create':
        create_bot(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
