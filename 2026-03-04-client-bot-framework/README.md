# Minimal Python Client Bot Framework

This is a minimal Python framework for building client-facing bots that handle HTTP webhook requests, authenticate via API key, route commands, and log all interactions. No external dependencies are required; only the standard library is used.

## Features

- Webhook endpoint for JSON-based commands
- API key authentication via HTTP header
- Command routing via Python decorators
- Centralized logging
- Easy to extend

## Files

- `bot_framework.py` - The reusable bot framework
- `sample_bot.py` - Example bot with `/start` and `/help` commands

## Usage

### Setup

1. Ensure you have Python 3.7+.
2. Clone or copy both `bot_framework.py` and `sample_bot.py` into a folder.

### Running the Bot

```sh
python sample_bot.py
```

The bot will run on `http://127.0.0.1:8000`.

### Sending Commands (Testing Locally)

You can test the bot using `curl`:

```sh
curl -X POST http://127.0.0.1:8000/ \
     -H 'Content-Type: application/json' \
     -H 'X-API-Key: test-api-key' \
     -d '{"command":"/start"}'
```

Expected response:

```json
{"result": "Welcome! Type /help to see available commands."}
```

Try `/help` as well. Invalid or missing API keys, or unknown commands, will result in error JSON.

## Customizing

- Define new commands using the `@bot.command("/yourcmd")` decorator in your bot script.
- The handler receives the incoming request JSON as a dictionary and should return something JSON-serializable.

## Security

- Change `API_KEY` in `sample_bot.py` to something secret for real use.
- For production, consider using a more robust server instead of Python's basic HTTPServer.

## License

This example is released to the public domain.