#!/usr/bin/env python3
"""Generate simple customizable SVG logos from the command line."""

from __future__ import annotations

import argparse
import re
import sys
import webbrowser
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    import svgwrite
except ImportError:
    print("Error: svgwrite is not installed. Install it with: pip install svgwrite")
    sys.exit(1)


ICON_PATHS: Dict[str, Optional[str]] = {
    # Minimal owl-like silhouette (head + ears + body)
    "owl": (
        "M0,-40 L-16,-26 L-28,-6 L-24,22 L-10,40 L0,48 L10,40 L24,22 "
        "L28,-6 L16,-26 Z"
    ),
    # Classic American football with pointed ends and subtle belly
    "football": "M-44,0 Q-24,-20 0,-20 Q24,-20 44,0 Q24,20 0,20 Q-24,20 -44,0 Z",
    # Simple rocket silhouette with fins and nose
    "rocket": (
        "M0,-46 Q18,-20 18,8 L30,30 L14,26 L8,40 L-8,40 L-14,26 "
        "L-30,30 L-18,8 L-18,-20 Q0,-46 0,-46 Z"
    ),
    "none": None,
}


HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{6})$")


def parse_size(value: str) -> Tuple[int, int]:
    """Parse size as INT or WIDTHxHEIGHT."""
    value = value.strip().lower()
    if "x" in value:
        parts = value.split("x", maxsplit=1)
        if len(parts) != 2:
            raise argparse.ArgumentTypeError("Size must be INT or WIDTHxHEIGHT (e.g., 512 or 512x512).")
        try:
            width = int(parts[0])
            height = int(parts[1])
        except ValueError as exc:
            raise argparse.ArgumentTypeError("Width and height must be integers.") from exc
    else:
        try:
            width = int(value)
            height = width
        except ValueError as exc:
            raise argparse.ArgumentTypeError("Size must be an integer or WIDTHxHEIGHT.") from exc

    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("Width and height must be positive integers.")
    return width, height


def validate_hex_color(value: str) -> str:
    """Validate 6-digit hex color like #1A2B3C."""
    if not HEX_COLOR_RE.match(value):
        raise argparse.ArgumentTypeError("Color must be in hex format #RRGGBB.")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate customizable SVG logos.")
    parser.add_argument("--text", default="VR", help="Logo text. Default: VR")
    parser.add_argument(
        "--icon",
        default="owl",
        choices=sorted(ICON_PATHS.keys()),
        help="Icon to place in the center.",
    )
    parser.add_argument(
        "--primary-color",
        default="#1E4DB7",
        type=validate_hex_color,
        help="Primary hex color for circular background.",
    )
    parser.add_argument(
        "--secondary-color",
        default="#1F2937",
        type=validate_hex_color,
        help="Secondary hex color for text.",
    )
    parser.add_argument(
        "--size",
        default="512",
        type=parse_size,
        help="Logo size as INT or WIDTHxHEIGHT. Default: 512",
    )
    parser.add_argument(
        "--output",
        default="logo.svg",
        help="Output SVG file path. Default: logo.svg",
    )
    parser.add_argument(
        "--list-icons",
        action="store_true",
        help="List available built-in icons and exit.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Open generated SVG in the default browser.",
    )
    return parser


def generate_logo(
    text: str,
    icon: str,
    primary_color: str,
    secondary_color: str,
    size: Tuple[int, int],
    output: Path,
) -> None:
    width, height = size
    dwg = svgwrite.Drawing(str(output), size=(width, height), profile="tiny")

    # Main circular badge occupies the upper area to leave room for text below.
    cx, cy = width / 2, height * 0.38
    radius = min(width, height) * 0.30
    dwg.add(dwg.circle(center=(cx, cy), r=radius, fill=primary_color))

    icon_path = ICON_PATHS.get(icon)
    if icon_path:
        # Scale and center the icon path around (0,0), then translate to badge center.
        icon_scale = min(width, height) / 220.0
        icon_group = dwg.g(
            fill="#FFFFFF",
            transform=f"translate({cx},{cy}) scale({icon_scale})",
        )
        icon_group.add(dwg.path(d=icon_path))
        dwg.add(icon_group)

    safe_text = text.strip() or "VR"
    font_size = max(16, int(min(width, height) * 0.12))
    text_y = min(height - font_size * 0.3, cy + radius + font_size * 0.9)
    dwg.add(
        dwg.text(
            safe_text,
            insert=(cx, text_y),
            text_anchor="middle",
            fill=secondary_color,
            font_size=font_size,
            font_family="Arial, sans-serif",
            font_weight="700",
        )
    )

    dwg.save()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_icons:
        print("Available icons:")
        for name in sorted(ICON_PATHS.keys()):
            print(f"- {name}")
        return 0

    try:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generate_logo(
            text=args.text,
            icon=args.icon,
            primary_color=args.primary_color,
            secondary_color=args.secondary_color,
            size=args.size,
            output=output_path,
        )
    except Exception as exc:  # pragma: no cover - safety for CLI runtime issues
        print(f"Error: failed to generate logo: {exc}", file=sys.stderr)
        return 1

    print(f"Logo generated: {output_path}")

    if args.preview:
        try:
            webbrowser.open(output_path.as_uri())
            print("Opened preview in default browser.")
        except Exception as exc:  # pragma: no cover - browser open depends on host
            print(f"Warning: could not open browser preview: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
