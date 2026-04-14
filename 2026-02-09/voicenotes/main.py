#!/usr/bin/env python3
import argparse
import asyncio
from voicenotes.telegram import TelegramVoiceHandler
from voicenotes.signal import SignalVoiceHandler
from voicenotes.transcribe import transcribe_audio
from voicenotes.obsidian import write_daily_log

def main():
    parser = argparse.ArgumentParser(description="Voice Notes to Obsidian Logger")
    parser.add_argument("--platform", choices=["telegram", "signal"], required=True)
    parser.add_argument("--vault-path", default="~/obsidian-vault", help="Path to Obsidian vault")
    args = parser.parse_args()

    if args.platform == "telegram":
        asyncio.run(TelegramVoiceHandler(vault_path=args.vault_path).start())
    elif args.platform == "signal":
        SignalVoiceHandler(vault_path=args.vault_path).start()

if __name__ == "__main__":
    main()

