#!/usr/bin/env python3
import json
import sys
import datetime

file_path = '/Users/vicmacmini/clawd/daily-digest/digest_notes.json'
with open(file_path, 'r') as f:
    data = json.load(f)

new_entry = {
    "id": "client-bot-framework-2026-03-04",
    "expires": "2026-03-06",
    "section": "new_feature",
    "title": "🤖 New: Client-facing Bot Framework",
    "body": "Minimal Python framework for building client-facing bots that handle HTTP webhook requests, authenticate via API key, route commands to registered handlers, and log interactions.",
    "examples": [
        "Run sample bot: `python sample_bot.py`",
        "Send command: `curl -X POST http://127.0.0.1:8000/ -H 'Content-Type: application/json' -H 'X-API-Key: test-api-key' -d '{\"command\":\"/start\"}'`",
        "Add new commands: `@bot.command(\"/custom\")`"
    ],
    "tip": "Use this to quickly spin up a client-facing bot for a new sports analytics product (like ShaqDiesel). No external dependencies."
}

data.append(new_entry)

with open(file_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')

print('Added digest note')