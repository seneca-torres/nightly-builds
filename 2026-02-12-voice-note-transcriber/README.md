# Voice Note Transcriber

This script transcribes voice notes with OpenAI Whisper and appends them to a daily markdown log in your Obsidian vault.

## Requirements

- Python 3.10+
- ffmpeg (required by Whisper)
- Whisper package: `pip install -U openai-whisper`

## Usage

Basic usage (files or folders):

```
python transcribe_voice_notes.py ~/voice-notes
python transcribe_voice_notes.py note1.m4a note2.wav
```

Specify a model or language:

```
python transcribe_voice_notes.py ~/voice-notes --model medium --language en
```

Dry run:

```
python transcribe_voice_notes.py ~/voice-notes --dry-run
```

Log to a file:

```
python transcribe_voice_notes.py ~/voice-notes --log-file ~/transcribe.log
```

## Output

Entries are appended to a daily note in:

```
~/obsidian-vault/Daily-Notes/YYYY-MM-DD.md
```

Each entry includes:
- original filename
- recording timestamp (based on file modified time)
- transcription text

## Supported formats

- .m4a
- .wav
- .mp3

## Notes

- Recording timestamps use file modification time.
- If you want a different Obsidian vault, pass `--obsidian-dir`.
