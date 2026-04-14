#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent
CLI_PATH = REPO_DIR / "google_docs_to_markdown.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_cli_module():
    spec = importlib.util.spec_from_file_location("google_docs_to_markdown", CLI_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import google_docs_to_markdown.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_demo_cli() -> str:
    completed = subprocess.run(
        [sys.executable, str(CLI_PATH), "--demo"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def verify_demo_output() -> None:
    output = run_demo_cli()
    require(output.startswith("---\n"), "Demo output should start with YAML frontmatter.")
    require('title: "Demo Project Brief"' in output, "Frontmatter should include the demo title.")
    require('author: "Alex Example"' in output, "Frontmatter should include the demo author.")
    require("Goal\nShip the Google Docs to Markdown converter this week." in output, "Body content should be present.")


def verify_output_file() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "demo.md"
        subprocess.run(
            [sys.executable, str(CLI_PATH), "--demo", "--output", str(output_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        require(output_path.exists(), "--output should create the requested file.")
        contents = output_path.read_text(encoding="utf-8")
        require('google_doc_id: "1DemoDocIdAbCdEfGhIjKlMnOpQrStUvWxYz123456"' in contents, "Output file should contain the demo doc ID.")


def verify_id_extraction() -> None:
    module = load_cli_module()
    raw_id = "1AbCdEfGhIjKlMnOpQrStUvWxYz9876543210"
    require(module.extract_doc_id(raw_id) == raw_id, "Raw doc IDs should pass through unchanged.")
    url = f"https://docs.google.com/document/d/{raw_id}/edit"
    require(module.extract_doc_id(url) == raw_id, "Doc URLs should yield the embedded doc ID.")
    alt_url = f"https://docs.google.com/document/u/0/d/{raw_id}/edit?tab=t.0"
    require(module.extract_doc_id(alt_url) == raw_id, "Doc URLs with /u/0/ should be supported.")


def main() -> int:
    verify_demo_output()
    verify_output_file()
    verify_id_extraction()
    print("Verification passed: demo mode, output writing, and URL parsing all work.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
