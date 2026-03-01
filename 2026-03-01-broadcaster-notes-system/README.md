# Broadcaster Notes CLI

Small Python CLI for converting plain text that represents Google Docs broadcaster notes into Obsidian-compatible markdown.

## Scope

- Reads plain text from a file or stdin.
- Detects a small set of entities with lightweight heuristics:
  - coach names
  - school names
  - dates
  - staff roles
- Generates:
  - YAML frontmatter with entity lists
  - Obsidian `[[backlinks]]` in the body
  - one markdown file per input note

This is intentionally narrow and suitable for a 1-2 hour implementation. It does not call the Google Docs API.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

Input file example:

```text
Friday Prep
Head Coach Marcus Freeman met with Assistant Coach James Laurinaitis on March 1, 2026.
Notre Dame University hosts USC on 09/03/2026.
Marcus Freeman, head coach, said the defensive depth improved.
```

Convert a file and write markdown to `output/`:

```bash
broadcaster-notes sample.txt
```

Print the generated markdown instead of writing a file:

```bash
broadcaster-notes sample.txt --stdout
```

Pipe text directly:

```bash
cat sample.txt | broadcaster-notes --title "Notre Dame Prep" --stdout
```

Write to a custom output directory:

```bash
broadcaster-notes sample.txt --output-dir notes
```

## Output shape

Generated markdown includes:

```markdown
---
title: "Friday Prep"
source: "plain-text"
tags:
  - broadcaster-notes
coaches:
  - "Marcus Freeman"
schools:
  - "Notre Dame University"
dates:
  - "2026-03-01"
roles:
  - "Head Coach"
---
```

The body preserves the original text while converting recognized entities into Obsidian links like `[[Marcus Freeman]]` or aliased date links like `[[2026-03-01|March 1, 2026]]`.

## Testing

Run the unit tests with:

```bash
python3 -m unittest discover -s tests -v
```

Quick manual smoke test:

```bash
python3 -m broadcaster_notes.cli sample.txt --stdout
```

## Notes on heuristics

- Coach names are detected from patterns like `Coach Name`, `Head Coach Name`, or `Name, head coach`.
- Schools are detected from a small suffix-based matcher plus a few common aliases like `USC` and `LSU`.
- Dates support `Month DD, YYYY`, `Month YYYY`, and `MM/DD/YYYY`.
- Roles are matched from a short predefined list.

If you need broader or more accurate entity extraction later, the next step is to replace the regex heuristics with a proper NER layer or a configurable alias dictionary.