#!/usr/bin/env python3
"""
Canvas Updater - Updates ~/clawd/canvas/index.html based on ~/clawd/NIGHTLY-BUILDS.md

Parses completed builds and ideas from the markdown file and updates the HTML dashboard.
"""

import re
import argparse
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path


# Default paths
DEFAULT_MD_PATH = Path.home() / "clawd" / "NIGHTLY-BUILDS.md"
DEFAULT_HTML_PATH = Path.home() / "clawd" / "canvas" / "index.html"


def parse_completed_builds(md_content: str) -> list[dict]:
    """Parse the ### Completed section from NIGHTLY-BUILDS.md."""
    # Regex to match: 1. **Title** ✅ (YYYY-MM-DD) — Description. [PR: url.] Location: `path`
    # The description is everything after "— " up to (and excluding) " Location:"
    # PR can come before Location: "Description. PR: url. Location: `path`"
    # Or Location can be directly after Description: "Description. Location: `path`"
    # Or no PR at all: "Description. Location: `path`"
    
    pattern = r'^(\d+)\.\s+\*\*(.+?)\*\*\s+✅\s+\((\d{4}-\d{2}-\d{2})\)\s+—\s+(.+?)\s+Location:\s+`([^`]+)`(?:\.\s+PR:\s+(.+?))?$'
    
    builds = []
    for match in re.finditer(pattern, md_content, re.MULTILINE):
        # The description may contain "PR: url." - we need to extract just the description part
        # Find PR: in description and remove it
        full_desc = match.group(4).strip()
        pr_match = re.search(r'\.?\s*PR:\s+https?://\S+\.?$', full_desc)
        if pr_match:
            # Remove PR part from description
            description = full_desc[:pr_match.start()].strip()
            # Remove trailing period if present
            if description.endswith('.'):
                description = description[:-1]
        else:
            description = full_desc
        
        build = {
            'number': int(match.group(1)),
            'title': match.group(2).strip(),
            'date': match.group(3),
            'description': description,
            'location': match.group(5).strip(),
            'pr_link': match.group(6).strip() if match.group(6) else None
        }
        builds.append(build)
    
    # Sort by date descending
    builds.sort(key=lambda x: x['date'], reverse=True)
    return builds


def count_half_baked_ideas(md_content: str) -> int:
    """Count items in 'Victor's Half-Baked Ideas' section."""
    # Find the section
    pattern = r'### Victor\'s Half-Baked Ideas.*?(?=###|\Z)'
    match = re.search(pattern, md_content, re.DOTALL)
    
    if not match:
        return 0
    
    section_content = match.group(0)
    # Count lines starting with "- **"
    ideas = re.findall(r'^- \*\*', section_content, re.MULTILINE)
    return len(ideas)


def extract_pr_number(pr_link: str) -> str:
    """Extract PR number from URL like https://github.com/.../pull/123"""
    if not pr_link:
        return None
    match = re.search(r'/pull/(\d+)', pr_link)
    return match.group(1) if match else None


def generate_last_build_html(build: dict) -> str:
    """Generate HTML for the latest build section."""
    return f"""    <div class="last-build" id="last-build">
    <h3>✨ Latest Build</h3>
    <div class="name">{build['title']}</div>
    <div class="info">Completed {build['date']} — {build['description']}</div>
  </div>"""


def generate_build_cards_html(builds: list[dict]) -> str:
    """Generate HTML for build cards sorted by date descending."""
    cards = []
    for build in builds:
        pr_html = ""
        if build['pr_link']:
            pr_num = extract_pr_number(build['pr_link'])
            if pr_num:
                pr_html = f""" · <a href="{build['pr_link']}" style="color: #58a6ff; text-decoration: none;">PR #{pr_num}</a>"""
        
        card = f"""      <div class="build-card">
        <div class="title">{build['title']} <span class="status done">done</span></div>
        <div class="desc">{build['description']}</div>
        <div class="meta">Completed {build['date']}{pr_html} · {build['location']}</div>
      </div>"""
        cards.append(card)
    
    return "\n".join(cards)


def update_html(
    html_content: str,
    builds: list[dict],
    ideas_count: int,
    completed_count: int,
    queued_count: int = 0,
    failed_count: int = 0
) -> str:
    """Update the HTML content with new build data."""
    
    # Generate new sections
    last_build_html = generate_last_build_html(builds[0]) if builds else ""
    cards_html = generate_build_cards_html(builds)
    
    # Replace last-build div content (entire div with id="last-build")
    last_build_pattern = r'<div class="last-build" id="last-build">.*?</div>\s*</div>'
    html_content = re.sub(
        last_build_pattern,
        last_build_html + "\n  </div>",
        html_content,
        flags=re.DOTALL
    )
    
    # Replace completed-list inner HTML
    completed_list_pattern = r'<div id="completed-list">.*?</div>\s*</div>\s*</section>'
    replacement = f'<div id="completed-list">\n{cards_html}\n    </div>\n  </section>'
    html_content = re.sub(
        completed_list_pattern,
        replacement,
        html_content,
        flags=re.DOTALL
    )
    
    # Update stat counts
    html_content = re.sub(
        r'<div class="num green" id="completed-count">\d+</div>',
        f'<div class="num green" id="completed-count">{completed_count}</div>',
        html_content
    )
    html_content = re.sub(
        r'<div class="num blue" id="queued-count">\d+</div>',
        f'<div class="num blue" id="queued-count">{queued_count}</div>',
        html_content
    )
    html_content = re.sub(
        r'<div class="num yellow" id="ideas-count">\d+</div>',
        f'<div class="num yellow" id="ideas-count">{ideas_count}</div>',
        html_content
    )
    html_content = re.sub(
        r'<div class="num red" id="failed-count">\d+</div>',
        f'<div class="num red" id="failed-count">{failed_count}</div>',
        html_content
    )
    
    # Update badges
    html_content = re.sub(
        r'<span class="badge" id="completed-badge">\d+</span>',
        f'<span class="badge" id="completed-badge">{completed_count}</span>',
        html_content
    )
    
    # Update timestamp
    now = datetime.now()
    timestamp = now.strftime("%b %d, %Y")
    html_content = re.sub(
        r'Last updated:.*?·',
        f'Last updated: {timestamp} ·',
        html_content
    )
    
    return html_content


def main():
    parser = argparse.ArgumentParser(
        description="Update canvas/index.html based on NIGHTLY-BUILDS.md"
    )
    parser.add_argument(
        "--md",
        type=Path,
        default=DEFAULT_MD_PATH,
        help=f"Path to NIGHTLY-BUILDS.md (default: {DEFAULT_MD_PATH})"
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=DEFAULT_HTML_PATH,
        help=f"Path to index.html (default: {DEFAULT_HTML_PATH})"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write output to a different file instead of overwriting HTML"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print changes without writing to file"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup of original HTML"
    )
    
    args = parser.parse_args()
    
    # Read source files
    if not args.md.exists():
        print(f"Error: Markdown file not found: {args.md}")
        return 1
    
    md_content = args.md.read_text()
    
    if not args.html.exists():
        print(f"Error: HTML file not found: {args.html}")
        return 1
    
    html_content = args.html.read_text()
    
    # Parse data
    builds = parse_completed_builds(md_content)
    ideas_count = count_half_baked_ideas(md_content)
    completed_count = len(builds)
    queued_count = 0
    failed_count = 0
    
    print(f"Found {completed_count} completed builds")
    print(f"Found {ideas_count} half-baked ideas")
    
    if builds:
        print(f"Latest build: {builds[0]['title']} ({builds[0]['date']})")
    
    # Generate updated HTML
    updated_html = update_html(
        html_content,
        builds,
        ideas_count,
        completed_count,
        queued_count,
        failed_count
    )
    
    if args.dry_run:
        print("\n--- DRY RUN: Changes would be ---")
        print(f"Completed count: {completed_count}")
        print(f"Queued count: {queued_count}")
        print(f"Ideas count: {ideas_count}")
        print(f"Failed count: {failed_count}")
        print(f"\nLatest build:\n{generate_last_build_html(builds[0]) if builds else 'None'}")
        print(f"\nFirst 3 build cards:")
        for build in builds[:3]:
            print(f"  - {build['title']} ({build['date']})")
        print("\n--- End dry run ---")
        return 0
    
    # Determine output path
    output_path = args.output if args.output else args.html
    
    # Create backup unless disabled
    if not args.no_backup and output_path == args.html:
        backup_path = args.html.with_suffix('.html.bak')
        shutil.copy2(args.html, backup_path)
        print(f"Created backup: {backup_path}")
    
    # Write updated HTML
    output_path.write_text(updated_html)
    print(f"Updated HTML written to: {output_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
