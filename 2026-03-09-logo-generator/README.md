# SVG Logo Generator CLI

`logo_gen.py` is a small Python CLI that generates customizable SVG logos using `svgwrite`.

## Features

- Configurable text (`--text`, default: `VR`)
- Built-in icon options (`--icon`): `owl`, `football`, `rocket`, `none`
- Custom colors:
  - `--primary-color` for circular background
  - `--secondary-color` for text
- Custom size via `--size`:
  - Single value: `512` (square)
  - Width/height: `640x360`
- Output path via `--output` (default: `logo.svg`)
- `--list-icons` to show available icons
- `--preview` to open generated SVG in your browser

## Installation

```bash
python3 -m pip install svgwrite
```

If your system Python is externally managed (common with Homebrew), use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install svgwrite
```

## Usage

Generate with defaults:

```bash
python3 logo_gen.py
```

List icon choices:

```bash
python3 logo_gen.py --list-icons
```

Custom logo:

```bash
python3 logo_gen.py \
  --text "VR Labs" \
  --icon rocket \
  --primary-color "#0B3D91" \
  --secondary-color "#111827" \
  --size 640x640 \
  --output rocket_logo.svg
```

Generate and preview:

```bash
python3 logo_gen.py --icon football --preview
```

## Example Outputs

- `logo.svg` (default settings)
- `rocket_logo.svg` (custom settings from example above)

## Verification

Run the verification script:

```bash
python3 verify.py
```

It runs `logo_gen.py` with default arguments and checks that `logo.svg` is created and non-empty.
