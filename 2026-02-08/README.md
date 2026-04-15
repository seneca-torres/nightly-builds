# Telegram Quick Reply System (YAML-driven)

A small Telegram bot that posts an inline-button “quick reply panel” from a YAML config and **audit-logs every button click**.

## Features

- YAML-defined reply templates (`standard`, `approve_reject`, `snooze`)
- Inline keyboard generation for quick actions
- Secure callback handling (HMAC-signed + expiring callback payloads)
- JSONL audit log of all interactions
- Easy to extend: add templates in YAML, or add a new template type in `bot/templates.py`

## Project layout

- `bot/main.py` – entrypoint
- `bot/handlers.py` – commands + callback handler
- `bot/templates.py` – template parsing + keyboard building
- `bot/security.py` – signed callback data (tamper-resistant + expiring)
- `bot/audit.py` – JSONL audit logger
- `config/templates.yml` – example templates
- `logs/` – created at runtime (audit log)

## Setup

### 1) Create a bot token

Use **@BotFather** to create a bot and copy the token.

### 2) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure environment

Set:

- `BOT_TOKEN` – your bot token from BotFather
- `CALLBACK_SECRET` – a long random secret used to sign callback payloads

Optional:

- `TEMPLATES_CONFIG` – path to YAML (default `config/templates.yml`)
- `AUDIT_LOG_PATH` – audit log path (default `logs/audit.jsonl`)
- `CALLBACK_TTL_SECONDS` – callback expiry (default `900`, min `60`)
- `ADMIN_USER_IDS` – comma-separated Telegram user ids allowed to run `/reload`

Example:

```bash
export BOT_TOKEN="123:abc..."
export CALLBACK_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ADMIN_USER_IDS="123456789"
```

## Run

```bash
python -m bot.main
```

## Usage

- In any chat, run `/panel` to post a “Quick replies” panel.
- If you **reply to a message** and run `/panel`, the panel message is posted as a reply; button clicks will reply in that thread.
- Tap a button to send the configured response.
- Edit `config/templates.yml` and run `/reload` (admin) to apply changes without restarting.

## YAML template format

See `config/templates.yml` for a working example.

Supported types:

- `standard`: one button that sends `message`
- `approve_reject`: two buttons, configured under `approve` and `reject`
- `snooze`: multiple buttons from `options`; replies use `message_template` with `{minutes}`

## Audit logging

All callback interactions append to a JSONL file (default `logs/audit.jsonl`), including:

- timestamp (UTC), user, chat, message id
- template/action ids and labels
- success/failure and error details

