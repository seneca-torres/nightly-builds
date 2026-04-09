
import asyncio
import os
from telethon import TelegramClient
from voicenotes.transcribe import transcribe_audio
from voicenotes.obsidian import write_daily_log

class TelegramVoiceHandler:
    def __init__(self, vault_path="~/obsidian-vault"):
        self.vault_path = os.path.expanduser(vault_path)
        # Load credentials
        self.api_id = os.environ.get("TELEGRAM_API_ID")
        self.api_hash = os.environ.get("TELEGRAM_API_HASH")
        self.phone_number = os.environ.get("TELEGRAM_PHONE")

    async def start(self):
        async with TelegramClient(f"{self.phone_number}.session", self.api_id, self.api_hash) as client:
            @client.on(events.NewMessage(pattern=r"(?i).*voice note.*"))
            async def voice_handler(event):
                if event.voice:
                    # Download voice note
                    audio_path = await event.download_media()
                    
                    # Transcribe
                    transcript = transcribe_audio(audio_path)
                    
                    # Write to daily log
                    write_daily_log(self.vault_path, "Telegram Voice Note", transcript, audio_path)
                    
                    # Optional: cleanup audio file
                    os.unlink(audio_path)

            await client.run_until_disconnected()

