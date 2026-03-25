#!/usr/bin/env python3
"""
Memory Cleanup CLI - Tool for maintaining and organizing the memory system.

Scans memory/daily/ directory for markdown files and:
- Identifies and deduplicates repetitive entries (like cron job logs)
- Archives files older than 30 days (optional, with confirmation)
- Provides statistics on memory usage
- Fixes common formatting issues

Usage:
    python3 memory_cleanup.py [--dry-run] [--verbose] [--archive] [--stats]
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set

# Constants
MEMORY_ROOT = Path.home() / "clawd" / "memory"
DAILY_DIR = MEMORY_ROOT / "daily"
ARCHIVE_DIR = MEMORY_ROOT / "archive" / "daily"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Common repetitive patterns to deduplicate
REPETITIVE_PATTERNS = [
    r"^-\s*\[\d{2}:\d{2}\] ✅ (?:outcome for this cron run|action for this cron execution|the cron task properly)",
    r"^-\s*\[\d{2}:\d{2}\] 📋 Decision: (?:queue is empty|file contains `\[\]` \(empty array\))",
    r"^-\s*\[\d{2}:\d{2}\] 🔀 PR #\d+ in ",
    r"^-\s*\[\d{2}:\d{2}\] ✅ for ",
    r"^-\s*\[\d{2}:\d{2}\] 📋 Decision: ",
    r"^-\s*\[\d{2}:\d{2}\] 💡 ",
    r"^-\s*\[\d{2}:\d{2}\] 🚨 ",
    r"^-\s*\[\d{2}:\d{2}\] 🎯 ",
    r"^-\s*\[\d{2}:\d{2}\] ✅ this week: ",
]

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Cleanup and organize memory system files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Archive files older than 30 days"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show memory usage statistics"
    )
    parser.add_argument(
        "--dedupe",
        action="store_true",
        default=True,
        help="Deduplicate repetitive entries (default: True)"
    )
    parser.add_argument(
        "--fix-formatting",
        action="store_true",
        default=True,
        help="Fix common formatting issues (default: True)"
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=30,
        help="Maximum age in days for archiving (default: 30)"
    )
    return parser.parse_args()

def get_memory_files() -> List[Path]:
    """Get all markdown files in the daily directory."""
    if not DAILY_DIR.exists():
        print(f"Error: Daily directory not found at {DAILY_DIR}")
        sys.exit(1)
    
    files = list(DAILY_DIR.glob("*.md"))
    files.sort()
    return files

def parse_date_from_filename(filename: str) -> datetime:
    """Parse date from filename in format YYYY-MM-DD.md or YYYY-MM-DD-*.md."""
    match = re.match(r"(\d{4}-\d{2}-\d{2})", filename.stem)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d")
        except ValueError:
            pass
    return None

def load_file_content(filepath: Path) -> List[str]:
    """Load file content as list of lines."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []

def save_file_content(filepath: Path, lines: List[str]):
    """Save lines to file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    except Exception as e:
        print(f"Error writing {filepath}: {e}")

def deduplicate_entries(lines: List[str], verbose: bool = False) -> Tuple[List[str], int]:
    """Remove duplicate repetitive entries from file content."""
    if not lines:
        return lines, 0
    
    # Keep track of seen entries (by normalized content)
    seen = set()
    deduped = []
    removed = 0
    
    for line in lines:
        line_stripped = line.rstrip('\n')
        
        # Check if line matches any repetitive pattern
        is_repetitive = False
        matched_pattern = None
        for pattern in REPETITIVE_PATTERNS:
            if re.match(pattern, line_stripped):
                is_repetitive = True
                matched_pattern = pattern
                break
        
        if is_repetitive:
            # For better deduplication, normalize the line
            # Remove bullet point and timestamp
            normalized = re.sub(r'^-\s*\[\d{2}:\d{2}\] ', '', line_stripped)
            
            # Further normalize based on pattern type
            if 'PR #' in normalized:
                # Normalize PR references to just "PR # in repo"
                normalized = re.sub(r'PR #\d+', 'PR #', normalized)
            elif '✅ for' in normalized:
                # Normalize repo references
                normalized = re.sub(r'`[^`]+`', '`repo`', normalized)
                normalized = re.sub(r'\(\d+ open issues reviewed\)', '(N open issues reviewed)', normalized)
            
            if normalized in seen:
                removed += 1
                if verbose:
                    print(f"  Removing duplicate: {line_stripped[:80]}...")
                continue
            seen.add(normalized)
        
        deduped.append(line)
    
    return deduped, removed

def fix_formatting_issues(lines: List[str], verbose: bool = False) -> Tuple[List[str], int]:
    """Fix common formatting issues in memory files."""
    if not lines:
        return lines, 0
    
    fixed = []
    changes = 0
    i = 0
    
    while i < len(lines):
        line = lines[i]
        line_stripped = line.rstrip('\n')
        
        # Fix empty Summary sections
        if line_stripped.startswith("## Summary"):
            # Look ahead to find the next section or end of file
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            
            # If next line is another header or EOF, and there's no content
            if j >= len(lines) or lines[j].startswith("#"):
                if verbose:
                    print(f"  Fixing empty Summary section at line {i+1}")
                # Replace with placeholder
                fixed.append("## Summary\n")
                fixed.append("*(no entries yet)*\n")
                fixed.append("\n")
                changes += 1
                i = j
                continue
        
        # Fix malformed timestamps (e.g., missing brackets)
        # Handle lines like "- 12:00 Meeting" or "12:00 Meeting"
        if line_stripped.startswith('- '):
            # Check if it's "- 12:00 Meeting" format
            after_dash = line_stripped[2:].strip()
            timestamp_match = re.match(r'^(\d{2}:\d{2})\s+(.+)$', after_dash)
            if timestamp_match:
                if verbose:
                    print(f"  Fixing malformed timestamp: {line_stripped[:80]}...")
                fixed.append(f"- [{timestamp_match.group(1)}] {timestamp_match.group(2)}\n")
                changes += 1
                i += 1
                continue
        elif not line_stripped.startswith('[') and not line_stripped.startswith('#'):
            # Check if it's "12:00 Meeting" format (no dash)
            timestamp_match = re.match(r'^(\d{2}:\d{2})\s+(.+)$', line_stripped)
            if timestamp_match:
                if verbose:
                    print(f"  Fixing malformed timestamp: {line_stripped[:80]}...")
                fixed.append(f"[{timestamp_match.group(1)}] {timestamp_match.group(2)}\n")
                changes += 1
                i += 1
                continue
        
        fixed.append(line)
        
        i += 1
    
    return fixed, changes

def analyze_file_stats(filepath: Path, content: List[str]) -> Dict:
    """Analyze statistics for a single file."""
    stats = {
        'filename': filepath.name,
        'lines': len(content),
        'entries': 0,
        'word_count': 0,
        'timestamp_count': 0,
        'has_summary': False,
        'empty_summary': False,
        'duplicates': 0,
    }
    
    for line in content:
        line_stripped = line.strip()
        
        # Count timestamp entries
        if re.match(r'^\[\d{2}:\d{2}\]', line_stripped):
            stats['entries'] += 1
            stats['timestamp_count'] += 1
        
        # Check for Summary section
        if line_stripped.startswith("## Summary"):
            stats['has_summary'] = True
            # Check if empty
            j = content.index(line) + 1
            while j < len(content) and content[j].strip() == "":
                j += 1
            if j >= len(content) or content[j].startswith("#"):
                stats['empty_summary'] = True
        
        # Word count (rough)
        if line_stripped and not line_stripped.startswith("#"):
            stats['word_count'] += len(line_stripped.split())
    
    return stats

def collect_statistics(files: List[Path], verbose: bool = False) -> Dict:
    """Collect overall statistics about memory files."""
    stats = {
        'total_files': len(files),
        'total_lines': 0,
        'total_entries': 0,
        'total_words': 0,
        'files_with_empty_summary': 0,
        'files_without_summary': 0,
        'oldest_file': None,
        'newest_file': None,
        'entries_by_hour': defaultdict(int),
        'files_by_year_month': defaultdict(int),
    }
    
    for filepath in files:
        content = load_file_content(filepath)
        file_stats = analyze_file_stats(filepath, content)
        
        stats['total_lines'] += file_stats['lines']
        stats['total_entries'] += file_stats['entries']
        stats['total_words'] += file_stats['word_count']
        
        if file_stats['empty_summary']:
            stats['files_with_empty_summary'] += 1
        elif not file_stats['has_summary']:
            stats['files_without_summary'] += 1
        
        # Parse date for time-based stats
        date = parse_date_from_filename(filepath)
        if date:
            year_month = date.strftime("%Y-%m")
            stats['files_by_year_month'][year_month] += 1
            
            if not stats['oldest_file'] or date < stats['oldest_file']:
                stats['oldest_file'] = date
            if not stats['newest_file'] or date > stats['newest_file']:
                stats['newest_file'] = date
        
        # Analyze entry times
        for line in content:
            if line.strip().startswith('['):
                match = re.match(r'\[(\d{2}):\d{2}\]', line)
                if match:
                    hour = int(match.group(1))
                    stats['entries_by_hour'][hour] += 1
    
    return stats

def print_statistics(stats: Dict):
    """Print formatted statistics."""
    print("\n" + "="*60)
    print("MEMORY STATISTICS")
    print("="*60)
    
    print(f"\n📊 Overview:")
    print(f"  Total files: {stats['total_files']:,}")
    print(f"  Total lines: {stats['total_lines']:,}")
    print(f"  Total entries: {stats['total_entries']:,}")
    print(f"  Total words: ~{stats['total_words']:,}")
    
    if stats['oldest_file'] and stats['newest_file']:
        days_span = (stats['newest_file'] - stats['oldest_file']).days + 1
        print(f"  Date range: {stats['oldest_file'].strftime('%Y-%m-%d')} to {stats['newest_file'].strftime('%Y-%m-%d')} ({days_span} days)")
        print(f"  Avg entries/day: {stats['total_entries'] / max(days_span, 1):.1f}")
        print(f"  Avg lines/day: {stats['total_lines'] / max(days_span, 1):.1f}")
    
    print(f"\n📝 Summary Sections:")
    print(f"  Files with empty Summary: {stats['files_with_empty_summary']}")
    print(f"  Files without Summary: {stats['files_without_summary']}")
    
    if stats['files_by_year_month']:
        print(f"\n📅 Files by Month:")
        for ym, count in sorted(stats['files_by_year_month'].items()):
            print(f"  {ym}: {count} file{'s' if count != 1 else ''}")
    
    if stats['entries_by_hour']:
        print(f"\n⏰ Activity by Hour (24h):")
        for hour in range(24):
            count = stats['entries_by_hour'].get(hour, 0)
            bar = "█" * (count // max(1, max(stats['entries_by_hour'].values()) // 20))
            print(f"  {hour:02d}:00 {bar} {count}")
    
    print("="*60)

def archive_old_files(files: List[Path], max_age: int, dry_run: bool, verbose: bool) -> int:
    """Archive files older than max_age days."""
    cutoff_date = datetime.now() - timedelta(days=max_age)
    archived = 0
    
    for filepath in files:
        date = parse_date_from_filename(filepath)
        if date and date < cutoff_date:
            if verbose:
                print(f"  Archiving {filepath.name} ({date.strftime('%Y-%m-%d')})")
            
            if not dry_run:
                try:
                    dest = ARCHIVE_DIR / filepath.name
                    shutil.move(str(filepath), str(dest))
                    archived += 1
                except Exception as e:
                    print(f"  Error archiving {filepath.name}: {e}")
            else:
                archived += 1
    
    return archived

def main():
    args = parse_args()
    
    print("🧠 Memory Cleanup CLI")
    print(f"Scanning {DAILY_DIR}...")
    
    # Get all memory files
    files = get_memory_files()
    print(f"Found {len(files)} memory file(s)")
    
    if args.stats:
        stats = collect_statistics(files, args.verbose)
        print_statistics(stats)
    
    if args.archive:
        print(f"\n🗄️  Archiving files older than {args.max_age} days...")
        archived = archive_old_files(files, args.max_age, args.dry_run, args.verbose)
        if args.dry_run:
            print(f"  Would archive {archived} file(s)")
        else:
            print(f"  Archived {archived} file(s)")
    
    # Process files for deduplication and formatting
    if args.dedupe or args.fix_formatting:
        print("\n🔧 Processing files...")
        total_deduped = 0
        total_fixed = 0
        
        for filepath in files:
            if args.verbose:
                print(f"\nProcessing {filepath.name}:")
            
            content = load_file_content(filepath)
            original_len = len(content)
            
            # Deduplicate
            if args.dedupe:
                content, deduped = deduplicate_entries(content, args.verbose)
                total_deduped += deduped
                if args.verbose and deduped:
                    print(f"  Removed {deduped} duplicate entries")
            
            # Fix formatting
            if args.fix_formatting:
                content, fixed = fix_formatting_issues(content, args.verbose)
                total_fixed += fixed
                if args.verbose and fixed:
                    print(f"  Fixed {fixed} formatting issues")
            
            # Save if changes were made
            if (args.dedupe and deduped > 0) or (args.fix_formatting and fixed > 0):
                if not args.dry_run:
                    save_file_content(filepath, content)
                    if args.verbose:
                        print(f"  Saved changes to {filepath.name}")
                else:
                    if args.verbose:
                        print(f"  Would save changes to {filepath.name}")
        
        print(f"\n📝 Summary:")
        if args.dedupe:
            print(f"  Duplicates removed: {total_deduped}")
        if args.fix_formatting:
            print(f"  Formatting issues fixed: {total_fixed}")
        
        if args.dry_run and (total_deduped > 0 or total_fixed > 0):
            print("\n⚠️  DRY RUN: No changes were saved. Use without --dry-run to apply.")
    
    if not any([args.stats, args.archive, args.dedupe, args.fix_formatting]):
        print("\nℹ️  No actions specified. Use --stats, --archive, --dedupe, or --fix-formatting.")
        print("   Try: python3 memory_cleanup.py --stats --dedupe --fix-formatting --dry-run")
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()