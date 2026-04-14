# Google Docs to Obsidian Markdown Converter

A Python CLI tool that converts Google Docs to Obsidian‑ready markdown with YAML frontmatter, using the `gog` CLI for authentication and data fetching.

Built as part of the Nightly Builds “Surprise Me” series, this tool serves as a pipeline step for the **Broadcaster Notes Intelligence System** half‑baked idea, enabling conversion of broadcaster notes (stored in Google Docs) into structured Obsidian markdown with entity detection and backlinking.

## Features

- **Zero dependencies** – uses only the Python standard library and the already‑installed `gog` CLI.
- **Flexible input** – accepts either a Google Doc ID or a full Google Docs URL.
- **Rich metadata** – extracts title, creation/modification dates, author, and source URL via `gog docs info --json`.
- **Plain‑text content** – fetches document body via `gog docs cat`.
- **Demo mode** – generates a sample markdown document when the Google Docs API is not enabled or for offline testing.
- **Verification script** – includes `verify.py` to validate the tool works as expected.
- **Obsidian‑ready** – outputs YAML frontmatter compatible with Obsidian’s dataview plugin and standard markdown.

## Installation

No installation required – the tool is a single Python script.

**Prerequisites:**
- Python 3.8+
- [`gog` CLI](https://github.com/victorres11/gog) installed and authenticated (run `gog login` if needed).
- Google Docs API enabled for your Google Cloud project (optional; demo mode works without it).

## Usage

### Basic conversion

```bash
python3 google_docs_to_markdown.py <doc-id-or-url>
```

Example with a Doc ID:
```bash
python3 google_docs_to_markdown.py 1a2b3c4d5e6f
```

Example with a Google Docs URL:
```bash
python3 google_docs_to_markdown.py "https://docs.google.com/document/d/1a2b3c4d5e6f/edit"
```

### Save to a file

```bash
python3 google_docs_to_markdown.py <doc-id> -o output.md
```

### Demo mode (no API needed)

```bash
python3 google_docs_to_markdown.py --demo
```

### Help

```bash
python3 google_docs_to_markdown.py --help
```

## Integration with Broadcaster Notes Intelligence System

This tool is designed as the first step in converting broadcaster notes (hundreds of Google Docs) into a searchable Obsidian vault.

**Suggested pipeline:**
1. **Fetch & convert** – Use this tool to download each Google Doc as markdown.
2. **Entity extraction** – Run the existing `broadcaster_notes_entity_extractor.py` (2026‑02‑26) on the markdown files to detect coach names, school names, dates, and roles.
3. **Backlinking** – Use the extracted entities to create Obsidian backlinks (`[[coach-name]]`, `[[school-name]]`).
4. **Search & visualization** – Browse the resulting vault with Obsidian’s graph view, or use the Coach‑School Relationship Visualizer (2026‑03‑23) for interactive exploration.

**Example workflow script (sketch):**
```bash
#!/bin/bash
# convert_all.sh
for doc_id in $(cat doc_ids.txt); do
    python3 google_docs_to_markdown.py "$doc_id" -o "vault/${doc_id}.md"
done
```

## Verification

Run the included verification script to confirm the tool works:

```bash
python3 verify.py
```

Expected output:
```
Running google_docs_to_markdown.py in demo mode...
Output received, verifying...
✅ Verification passed: All checks passed
```

## Error Handling

- **Missing `gog` CLI** – tool prints an error and exits.
- **Google Docs API not enabled** – metadata fetch fails gracefully; the tool falls back to placeholder metadata (title “Document”, author “Unknown”) and continues with the content fetch.
- **Invalid Doc ID / URL** – `gog` CLI returns an error; the tool prints the error and exits.
- **Timeout** – commands are limited to 30 seconds; timeout results in an error message.

## Limitations

- **Plain text only** – formatting (bold, italic, bullet lists, tables) is not preserved because `gog docs cat` returns plain text. Future versions could use `gog docs export --format html` and an HTML‑to‑Markdown converter.
- **No authentication refresh** – relies on `gog` CLI’s existing token; if the token expires, the user must re‑authenticate with `gog login`.
- **API enablement required** – for real metadata, the Google Docs API must be enabled in the Google Cloud project associated with the `gog` CLI credentials. Demo mode works without it.

## Future Improvements

- Add `--format html` option and integrate `html2text` for richer markdown conversion.
- Batch processing mode for converting multiple documents at once.
- Direct Obsidian vault integration (auto‑place files in vault, update index).
- Integration with the existing Coach CRM to link coaches mentioned in notes to contact records.

## Changelog

- **2026‑04‑14** – Initial nightly build: basic CLI with demo mode, verification script, and README.

---

*Part of the Nightly Builds “Surprise Me” series. See [NIGHTLY‑BUILDS.md](https://github.com/seneca‑torres/nightly‑builds/blob/main/NIGHTLY‑BUILDS.md) for more.*