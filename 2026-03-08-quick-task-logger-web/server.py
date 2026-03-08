#!/usr/bin/env python3
import datetime as dt
import html
import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

HOST = "127.0.0.1"
PORT = 8080
DAILY_DIR = Path.home() / "clawd" / "memory" / "daily"
MAX_RECENT = 25


def ensure_daily_dir() -> None:
    DAILY_DIR.mkdir(parents=True, exist_ok=True)


def daily_file_for_today() -> Path:
    return DAILY_DIR / f"{dt.date.today().isoformat()}.md"


def append_entry(text: str, category: str | None) -> dict:
    ensure_daily_dir()
    now = dt.datetime.now()
    timestamp = now.strftime("%H:%M:%S")
    date_str = now.date().isoformat()

    clean_text = " ".join(text.strip().split())
    clean_text = html.escape(clean_text, quote=False)

    if category:
        line = f"- [{timestamp}] ({category}) {clean_text}\n"
    else:
        line = f"- [{timestamp}] {clean_text}\n"

    path = DAILY_DIR / f"{date_str}.md"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)

    return {
        "date": date_str,
        "time": timestamp,
        "category": category,
        "text": clean_text,
        "file": str(path),
    }


def list_recent_entries(limit: int = MAX_RECENT) -> list[dict]:
    if not DAILY_DIR.exists():
        return []

    files = sorted(DAILY_DIR.glob("*.md"), reverse=True)
    entries: list[dict] = []

    for file_path in files:
        date_str = file_path.stem
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue

        for line in reversed(lines):
            line = line.strip()
            if not line.startswith("- ["):
                continue

            # Expected:
            # - [HH:MM:SS] (category) text
            # - [HH:MM:SS] text
            time_part_end = line.find("]")
            if time_part_end == -1:
                continue

            time_str = line[3:time_part_end]
            rest = line[time_part_end + 1 :].strip()
            category = None
            text = rest

            if rest.startswith("("):
                cat_end = rest.find(")")
                if cat_end != -1:
                    category = rest[1:cat_end].strip()
                    text = rest[cat_end + 1 :].strip()

            entries.append(
                {
                    "date": date_str,
                    "time": time_str,
                    "category": category,
                    "text": text,
                    "file": str(file_path),
                }
            )
            if len(entries) >= limit:
                return entries

    return entries


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/entries":
            data = {"entries": list_recent_entries()}
            body = json.dumps(data).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/":
            self.path = "/index.html"

        return super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/log":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        ctype = self.headers.get("Content-Type", "")

        text = ""
        category = None

        try:
            if "application/json" in ctype:
                payload = json.loads(raw.decode("utf-8"))
                text = str(payload.get("text", ""))
                category = payload.get("category") or None
            else:
                form = parse_qs(raw.decode("utf-8"))
                text = form.get("text", [""])[0]
                category = form.get("category", [""])[0] or None
        except Exception:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid payload")
            return

        text = text.strip()
        if not text:
            self.send_error(HTTPStatus.BAD_REQUEST, "text is required")
            return

        if category and category not in {"event", "idea", "todo"}:
            self.send_error(HTTPStatus.BAD_REQUEST, "invalid category")
            return

        entry = append_entry(text, category)
        body = json.dumps({"ok": True, "entry": entry}).encode("utf-8")
        self.send_response(HTTPStatus.CREATED)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    os.chdir(Path(__file__).resolve().parent)
    ensure_daily_dir()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()