
import subprocess
import os
from voicenotes.transcribe import transcribe_audio
from voicenotes.obsidian import write_daily_log

class SignalVoiceHandler:
    def __init__(self, vault_path="~/obsidian-vault"):
        self.vault_path = os.path.expanduser(vault_path)
        self.phone_number = os.environ.get("SIGNAL_PHONE")

    def start(self):
        # Use signal-cli to receive JSON-formatted messages
        command = [
            "signal-cli", 
            "-u", self.phone_number, 
            "receive", 
            "--json"
        ]
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
        
        for line in process.stdout:
            try:
                message = json.loads(line)
                if message.get("attachments"):
                    for attachment in message["attachments"]:
                        if attachment.get("contentType", "").startswith("audio/"):
                            # Download and transcribe
                            audio_path = self._download_attachment(attachment)
                            transcript = transcribe_audio(audio_path)
                            
                            # Write to daily log
                            write_daily_log(
                                self.vault_path, 
                                "Signal Voice Note", 
                                transcript, 
                                audio_path
                            )
                            
                            # Optional: cleanup
                            os.unlink(audio_path)
            except json.JSONDecodeError:
                print(f"Could not parse message: {line}")

    def _download_attachment(self, attachment):
        # Implementation depends on signal-cli JSON attachment structure
        pass

