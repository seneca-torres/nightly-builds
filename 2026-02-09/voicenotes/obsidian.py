
import os
from datetime import datetime

def write_daily_log(vault_path, source, transcript, audio_path):
    """Write voice note transcript to daily Obsidian markdown log"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(os.path.expanduser(vault_path), "daily", f"{today}.md")
    
    # Create daily directory if not exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Audio file stored with timestamp
    timestamp = datetime.now().strftime("%H%M%S")
    audio_filename = f"{today}-{timestamp}.mp3"
    audio_dest = os.path.join(os.path.dirname(log_path), audio_filename)
    
    os.rename(audio_path, audio_dest)
    
    # Append to daily log
    with open(log_path, "a") as f:
        f.write(f"\n\n## Voice Note ({source}) - {timestamp}\n")
        f.write(f"🎙️ **Transcript:**\n{transcript}\n\n")
        f.write(f"🔗 **Audio:** [[{audio_filename}]]\n")

