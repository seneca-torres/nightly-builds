# Voice Notes to Obsidian Logger

Automatically saves transcribed voice messages from Telegram and Signal to a daily log in your Obsidian vault.

## Features
- Supports Telegram and Signal
- Transcribes voice notes with Whisper (local + OpenAI fallback)
- Writes transcripts to daily markdown log
- Attaches original audio file

## Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration
Set environment variables:
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_PHONE`
- `SIGNAL_PHONE`
- `OPENAI_API_KEY`
- `OBSIDIAN_VAULT_PATH`

## Usage
```bash
# Telegram
python3 -m voicenotes --platform telegram

# Signal
python3 -m voicenotes --platform signal
```

