#!/usr/bin/env python3
"""Extract and archive voice message transcriptions from Clawdbot session JSONL."""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Optional


VOICE_TYPES = {
    "voice",
    "voice_message",
    "voice-message",
    "voice_note",
    "voice-note",
    "voiceNote",
}


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract voice message transcriptions from Clawdbot session JSONL files."
    )
    parser.add_argument(
        "--date",
        help="Date to process in YYYY-MM-DD (default: today)",
        default=None,
    )
    parser.add_argument(
        "--all",
        help="Process all dates found in sessions",
        action="store_true",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for daily logs (default: ~/clawd/voice-notes)",
        default="~/clawd/voice-notes",
    )
    return parser.parse_args(argv)


def expand(path_str: str) -> Path:
    return Path(os.path.expanduser(path_str)).resolve()


def _get_first(dct: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in dct and dct[key] not in (None, ""):
            return dct[key]
    return None


def _find_in_nested_voice(dct: dict[str, Any], keys: Iterable[str]) -> Any:
    voice_obj = dct.get("voice")
    if isinstance(voice_obj, dict):
        value = _get_first(voice_obj, keys)
        if value is not None:
            return value
    return None


def parse_datetime(value: Any) -> Optional[dt.datetime]:
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            return dt.datetime.fromtimestamp(value, tz=dt.timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        raw = raw.replace("Z", "+00:00")
        try:
            return dt.datetime.fromisoformat(raw)
        except ValueError:
            pass
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
        ):
            try:
                return dt.datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return None


def is_voice_message(dct: dict[str, Any]) -> bool:
    type_value = _get_first(dct, ["type", "message_type", "msg_type", "kind"])
    if isinstance(type_value, str) and type_value in VOICE_TYPES:
        return True
    if "voice" in dct and dct.get("voice") not in (None, ""):
        return True
    return False


def extract_transcription(dct: dict[str, Any]) -> Optional[str]:
    value = _get_first(
        dct,
        [
            "transcription",
            "transcript",
            "voice_transcription",
            "text",
            "caption",
        ],
    )
    if value is None:
        value = _find_in_nested_voice(
            dct,
            ["transcription", "transcript", "text", "caption"],
        )
    if isinstance(value, str):
        return value.strip() or None
    return None


def extract_sender(dct: dict[str, Any]) -> str:
    value = _get_first(
        dct,
        ["sender", "from", "user", "username", "author", "name"],
    )
    if isinstance(value, dict):
        nested = _get_first(value, ["name", "username", "id", "display_name"])
        if nested:
            return str(nested)
    return str(value) if value is not None else "Unknown"


def extract_file_path(dct: dict[str, Any]) -> Optional[str]:
    value = _get_first(
        dct,
        [
            "file_path",
            "path",
            "file",
            "audio_path",
            "voice_path",
            "filePath",
        ],
    )
    if value is None:
        value = _find_in_nested_voice(
            dct,
            ["file_path", "path", "file", "audio_path", "voice_path", "filePath"],
        )
    if isinstance(value, str):
        return value.strip() or None
    return None


def extract_timestamp(dct: dict[str, Any]) -> Optional[dt.datetime]:
    value = _get_first(
        dct,
        ["timestamp", "time", "date", "created_at", "createdAt", "ts"],
    )
    if value is None:
        value = _find_in_nested_voice(
            dct,
            ["timestamp", "time", "date", "created_at", "createdAt", "ts"],
        )
    return parse_datetime(value)


def iter_session_files() -> list[Path]:
    session_glob = os.path.expanduser("~/.clawdbot/sessions/*.jsonl")
    return [Path(path).resolve() for path in glob.glob(session_glob)]


def format_entry(entry: dict[str, Any]) -> str:
    timestamp = entry.get("timestamp") or "Unknown time"
    sender = entry.get("sender") or "Unknown"
    text = entry.get("text") or ""
    file_path = entry.get("file_path")

    lines = [f"- `{timestamp}` **{sender}**", f"  {text}"]
    if file_path:
        lines.append(f"  File: `{file_path}`")
    return "\n".join(lines) + "\n"


def write_daily_log(output_dir: Path, date_str: str, entries: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{date_str}.md"
    with out_path.open("a", encoding="utf-8") as handle:
        if out_path.stat().st_size == 0:
            handle.write(f"# Voice Notes - {date_str}\n\n")
        for entry in entries:
            handle.write(format_entry(entry))
            handle.write("\n")


def build_entry(dct: dict[str, Any]) -> Optional[dict[str, Any]]:
    if not is_voice_message(dct):
        return None
    transcription = extract_transcription(dct)
    if not transcription:
        return None
    timestamp = extract_timestamp(dct)
    sender = extract_sender(dct)
    file_path = extract_file_path(dct)

    timestamp_str = "Unknown time"
    date_str = "unknown-date"
    if timestamp:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=dt.timezone.utc)
        timestamp_str = timestamp.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        date_str = timestamp.date().isoformat()

    return {
        "date": date_str,
        "timestamp": timestamp_str,
        "sender": sender,
        "text": transcription,
        "file_path": file_path,
    }


def collect_entries(session_files: list[Path]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for session_file in session_files:
        try:
            with session_file.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(payload, dict):
                        continue
                    entry = build_entry(payload)
                    if entry:
                        entries.append(entry)
        except FileNotFoundError:
            continue
        except OSError:
            continue
    return entries


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)

    if args.all and args.date:
        print("Error: --all and --date cannot be used together.", file=sys.stderr)
        return 2

    if args.date:
        try:
            target_date = dt.date.fromisoformat(args.date)
        except ValueError:
            print("Error: --date must be in YYYY-MM-DD format.", file=sys.stderr)
            return 2
    else:
        target_date = dt.date.today()

    session_files = iter_session_files()
    if not session_files:
        print("No session files found in ~/.clawdbot/sessions/", file=sys.stderr)
        return 0

    entries = collect_entries(session_files)
    if not entries:
        print("No voice transcriptions found.", file=sys.stderr)
        return 0

    output_dir = expand(args.output_dir)

    if args.all:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for entry in entries:
            grouped.setdefault(entry["date"], []).append(entry)
        for date_str, date_entries in sorted(grouped.items()):
            write_daily_log(output_dir, date_str, date_entries)
        print(f"Wrote {sum(len(v) for v in grouped.values())} entries to {output_dir}")
        return 0

    date_str = target_date.isoformat()
    filtered = [entry for entry in entries if entry["date"] == date_str]
    if not filtered:
        print(f"No voice transcriptions found for {date_str}.", file=sys.stderr)
        return 0

    write_daily_log(output_dir, date_str, filtered)
    print(f"Wrote {len(filtered)} entries to {output_dir / f'{date_str}.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
