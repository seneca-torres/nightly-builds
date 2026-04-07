# Telegram Quick Reply Buttons (Python)

Single-file Telegram bot + CLI that lets you define reusable **button templates** in YAML and use **one-tap** inline buttons for actions like **approve / reject / snooze**.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure

```bash
python telegram_quick_replies.py config init --path config.yml
```

Edit `config.yml` and set `bot.token`.

## Run

```bash
python telegram_quick_replies.py --config config.yml run
```

In Telegram, send:

```text
/qr approve_reject_snooze
```

## Manage templates (CLI)

List:
```bash
python telegram_quick_replies.py --config config.yml template list
```

Show (JSON):
```bash
python telegram_quick_replies.py --config config.yml template show approve_reject_snooze
```

Upsert from snippet file:
```bash
python telegram_quick_replies.py --config config.yml template set my_template --file my_template.yml
```

Export to snippet file:
```bash
python telegram_quick_replies.py --config config.yml template export approve_reject_snooze --out snippet.yml
```

## Template format

Templates live under `templates:`:

- `text`: message text (supports `{user_first_name}`, `{user_name}`, `{now_iso}` and friends)
- `buttons[]`: each with:
  - `id`: stable identifier used for callbacks
  - `text`: button label
  - `style`: style name mapped via `styles:`
  - `action`:
    - `type: message` → send a new message
    - `type: edit` → edit the template message
    - `type: delete` → delete the template message

