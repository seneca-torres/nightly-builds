#!/usr/bin/env python3
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

SUPPORTED_EXTS = {".m4a", ".wav", ".mp3"}
DEFAULT_MODEL = "base"
DEFAULT_OBSIDIAN_DIR = Path.home() / "obsidian-vault" / "Daily-Notes"


def configure_logging(log_path: Path | None, verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handlers: List[logging.Handler] = [logging.StreamHandler()]
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe voice notes with Whisper and append to an Obsidian daily log.",
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Audio files or directories containing voice notes.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Whisper model name (default: base).",
    )
    parser.add_argument(
        "--obsidian-dir",
        default=str(DEFAULT_OBSIDIAN_DIR),
        help="Path to Obsidian Daily-Notes directory.",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Language code hint (e.g., en). Optional.",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Optional log file path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Transcribe but do not write to the daily log.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def iter_audio_files(paths: Iterable[str]) -> List[Path]:
    files: List[Path] = []
    for entry in paths:
        path = Path(entry).expanduser().resolve()
        if path.is_dir():
            for file_path in sorted(path.rglob("*")):
                if file_path.suffix.lower() in SUPPORTED_EXTS:
                    files.append(file_path)
        elif path.is_file():
            if path.suffix.lower() in SUPPORTED_EXTS:
                files.append(path)
            else:
                logging.warning("Skipping unsupported file: %s", path)
        else:
            logging.warning("Path not found: %s", path)
    return files


def get_recording_timestamp(path: Path) -> datetime:
    stat = path.stat()
    return datetime.fromtimestamp(stat.st_mtime)


def load_whisper_model(model_name: str):
    try:
        import whisper
    except ImportError as exc:
        logging.error(
            "OpenAI Whisper is not installed. Install with `pip install -U openai-whisper`."
        )
        raise exc
    logging.info("Loading Whisper model: %s", model_name)
    return whisper.load_model(model_name)


def transcribe_file(model, path: Path, language: str | None) -> str:
    logging.info("Transcribing: %s", path)
    result = model.transcribe(str(path), language=language)
    text = (result.get("text") or "").strip()
    if not text:
        logging.warning("Empty transcription for: %s", path)
    return text


def daily_log_path(obsidian_dir: Path, timestamp: datetime) -> Path:
    filename = timestamp.strftime("%Y-%m-%d") + ".md"
    return obsidian_dir / filename


def append_entry(
    log_path: Path,
    source_path: Path,
    recorded_at: datetime,
    transcript: str,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = []
    entry.append("## Voice Note")
    entry.append(f"- File: {source_path}")
    entry.append(f"- Recorded: {recorded_at.isoformat(sep=' ', timespec='seconds')}")
    entry.append("")
    entry.append(transcript if transcript else "_(No transcription produced)_")
    entry.append("")
    log_path.write_text(
        log_path.read_text(encoding="utf-8") + "\n".join(entry) + "\n",
        encoding="utf-8",
    ) if log_path.exists() else log_path.write_text(
        "\n".join(entry) + "\n", encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    log_file = Path(args.log_file).expanduser().resolve() if args.log_file else None
    configure_logging(log_file, args.verbose)

    obsidian_dir = Path(args.obsidian_dir).expanduser().resolve()
    audio_files = iter_audio_files(args.inputs)
    if not audio_files:
        logging.error("No supported audio files found.")
        return 1

    try:
        model = load_whisper_model(args.model)
    except Exception:
        return 1

    failures = 0
    for audio_path in audio_files:
        try:
            recorded_at = get_recording_timestamp(audio_path)
            transcript = transcribe_file(model, audio_path, args.language)
            if args.dry_run:
                logging.info("Dry-run: skipping write for %s", audio_path)
                continue
            log_path = daily_log_path(obsidian_dir, recorded_at)
            append_entry(log_path, audio_path, recorded_at, transcript)
            logging.info("Appended to %s", log_path)
        except Exception as exc:
            failures += 1
            logging.exception("Failed to process %s: %s", audio_path, exc)

    if failures:
        logging.error("Completed with %d failure(s).", failures)
        return 1

    logging.info("Completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
