# Google Docs to Markdown

`google_docs_to_markdown.py` is a zero-dependency Python CLI that converts a Google Doc into Obsidian-ready markdown with YAML frontmatter.

It uses:

- `gog docs info --json` for metadata
- `gog docs cat` for plain text content

## Features

- Accepts either a Google Doc ID or a full Google Docs URL
- Emits YAML frontmatter with title, author, creation date, and modification date
- Outputs plain text body content that works well in Obsidian
- Includes `--demo` mode for offline smoke testing
- Includes a verification script
- Uses only the Python standard library

## Requirements

- Python 3.9+
- `gog` installed and authenticated
- Google Docs API access available to the `gog` OAuth project used on your machine

If `gog` returns a `403 accessNotConfigured` error, enable the Google Docs API for the underlying project and retry.

## Usage

Print markdown to stdout from a raw doc ID:

```bash
python3 google_docs_to_markdown.py 1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
```

Print markdown to stdout from a Google Docs URL:

```bash
python3 google_docs_to_markdown.py "https://docs.google.com/document/d/1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890/edit"
```

Write the converted markdown to a file:

```bash
python3 google_docs_to_markdown.py 1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890 --output note.md
```

Run demo mode without calling `gog`:

```bash
python3 google_docs_to_markdown.py --demo
```

## Example output

```markdown
---
title: "Demo Project Brief"
google_doc_id: "1DemoDocIdAbCdEfGhIjKlMnOpQrStUvWxYz123456"
google_doc_url: "https://docs.google.com/document/d/1DemoDocIdAbCdEfGhIjKlMnOpQrStUvWxYz123456/edit"
author: "Alex Example"
created: "2026-04-10T15:22:01Z"
modified: "2026-04-13T08:45:19Z"
---

Project Brief

Goal
Ship the Google Docs to Markdown converter this week.
```

## Verification

Run the included verification script:

```bash
python3 verify_google_docs_to_markdown.py
```

The verification script checks:

- Demo mode output structure
- `--output` file writing
- Google Doc ID extraction from both IDs and URLs

## Notes

- The tool preserves the plain text returned by `gog docs cat` rather than attempting additional markdown formatting.
- Metadata field extraction is intentionally tolerant of multiple JSON shapes so it can handle future `gog` response variations.
- Runtime failures from `gog` are surfaced clearly, including missing CLI, API errors, and timeouts.
