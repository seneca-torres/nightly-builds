#!/usr/bin/env python3
"""
Conversation Stats Analyzer
Parses Clawdbot session JSONL files and generates fun analytics.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

# Common words to exclude from keyword analysis
STOP_WORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for',
    'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by',
    'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all',
    'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get',
    'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him',
    'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them',
    'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over',
    'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first',
    'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day',
    'most', 'us', 'is', 'was', 'are', 'been', 'has', 'had', 'were', 'said', 'did',
    'having', 'may', 'should', 'am', 'does', 'being'
}


def parse_session_file(filepath):
    """Parse a single JSONL session file and extract messages."""
    messages = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Look for message entries
                    if entry.get('type') == 'message' and 'message' in entry:
                        msg = entry['message']
                        role = msg.get('role')
                        if role in ['user', 'assistant']:
                            # Extract text from content array
                            text_parts = []
                            for content_item in msg.get('content', []):
                                if content_item.get('type') == 'text':
                                    text_parts.append(content_item.get('text', ''))
                            
                            if text_parts:  # Only add if there's actual text content
                                messages.append({
                                    'role': role,
                                    'timestamp': datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')),
                                    'text': ' '.join(text_parts),
                                    'tokens': msg.get('usage', {}).get('totalTokens', 0)
                                })
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Warning: Could not parse {filepath}: {e}")
    return messages


def get_session_files(sessions_dir, start_date=None, end_date=None):
    """Get all session files within the date range."""
    sessions_path = Path(sessions_dir).expanduser()
    if not sessions_path.exists():
        return []
    
    files = []
    for file in sessions_path.glob('**/*.jsonl'):
        # Skip if file has date filter and doesn't match
        if start_date or end_date:
            try:
                # Try to extract date from filename or file mtime
                file_date = datetime.fromtimestamp(file.stat().st_mtime).date()
                if start_date and file_date < start_date:
                    continue
                if end_date and file_date > end_date:
                    continue
            except:
                pass
        files.append(file)
    return files


def extract_keywords(text, top_n=20):
    """Extract top keywords from text, excluding stop words."""
    # Remove URLs, markdown, code blocks
    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`[^`]+`', '', text)
    
    # Extract words (lowercase, alphanumeric)
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    
    # Filter stop words and count
    filtered = [w for w in words if w not in STOP_WORDS]
    return Counter(filtered).most_common(top_n)


def compute_stats(messages):
    """Compute conversation statistics from messages."""
    if not messages:
        return None
    
    stats = {
        'total_messages': len(messages),
        'user_messages': sum(1 for m in messages if m['role'] == 'user'),
        'assistant_messages': sum(1 for m in messages if m['role'] == 'assistant'),
        'date_range': {
            'start': min(m['timestamp'] for m in messages).isoformat(),
            'end': max(m['timestamp'] for m in messages).isoformat()
        },
        'messages_by_day': defaultdict(lambda: {'user': 0, 'assistant': 0}),
        'messages_by_hour': defaultdict(int),
        'response_times': [],
        'message_lengths': {'user': [], 'assistant': []},
        'total_tokens': sum(m['tokens'] for m in messages),
        'tokens_by_day': defaultdict(int)
    }
    
    # Group messages by day and hour
    for msg in messages:
        day = msg['timestamp'].date().isoformat()
        hour = msg['timestamp'].hour
        
        stats['messages_by_day'][day][msg['role']] += 1
        stats['messages_by_hour'][hour] += 1
        stats['message_lengths'][msg['role']].append(len(msg['text']))
        stats['tokens_by_day'][day] += msg['tokens']
    
    # Calculate response times (time between user message and next assistant message)
    for i in range(len(messages) - 1):
        if messages[i]['role'] == 'user' and messages[i+1]['role'] == 'assistant':
            delta = (messages[i+1]['timestamp'] - messages[i]['timestamp']).total_seconds()
            if delta < 300:  # Only count responses within 5 minutes
                stats['response_times'].append(delta)
    
    # Extract keywords from all text
    all_text = ' '.join(m['text'] for m in messages)
    stats['keywords'] = extract_keywords(all_text)
    
    # Compute averages
    if stats['message_lengths']['user']:
        stats['avg_user_message_length'] = sum(stats['message_lengths']['user']) / len(stats['message_lengths']['user'])
    if stats['message_lengths']['assistant']:
        stats['avg_assistant_message_length'] = sum(stats['message_lengths']['assistant']) / len(stats['message_lengths']['assistant'])
    if stats['response_times']:
        stats['avg_response_time'] = sum(stats['response_times']) / len(stats['response_times'])
        stats['median_response_time'] = sorted(stats['response_times'])[len(stats['response_times']) // 2]
    
    return stats


def format_text_output(stats):
    """Format stats as pretty text output with emoji."""
    if not stats:
        return "📊 No conversation data found."
    
    output = []
    output.append("📊 Conversation Stats\n")
    output.append("=" * 50)
    
    # Date range
    start = datetime.fromisoformat(stats['date_range']['start']).strftime('%Y-%m-%d')
    end = datetime.fromisoformat(stats['date_range']['end']).strftime('%Y-%m-%d')
    output.append(f"\n📅 Date Range: {start} to {end}")
    
    # Message counts
    output.append(f"\n💬 Total Messages: {stats['total_messages']}")
    output.append(f"   👤 User: {stats['user_messages']}")
    output.append(f"   🤖 Assistant: {stats['assistant_messages']}")
    
    # Response times
    if 'avg_response_time' in stats:
        output.append(f"\n⚡ Response Times:")
        output.append(f"   Average: {stats['avg_response_time']:.1f}s")
        output.append(f"   Median: {stats['median_response_time']:.1f}s")
    
    # Message lengths
    if 'avg_user_message_length' in stats:
        output.append(f"\n📏 Average Message Length:")
        output.append(f"   User: {stats['avg_user_message_length']:.0f} chars")
    if 'avg_assistant_message_length' in stats:
        output.append(f"   Assistant: {stats['avg_assistant_message_length']:.0f} chars")
    
    # Token usage
    if stats['total_tokens'] > 0:
        output.append(f"\n🎫 Total Tokens: {stats['total_tokens']:,}")
    
    # Most active hours
    if stats['messages_by_hour']:
        top_hours = sorted(stats['messages_by_hour'].items(), key=lambda x: x[1], reverse=True)[:3]
        output.append(f"\n🕐 Most Active Hours:")
        for hour, count in top_hours:
            output.append(f"   {hour:02d}:00 - {count} messages")
    
    # Top keywords
    if stats['keywords']:
        output.append(f"\n🔑 Top Keywords:")
        for word, count in stats['keywords'][:10]:
            output.append(f"   {word}: {count}")
    
    # Daily breakdown (if multiple days)
    if len(stats['messages_by_day']) > 1:
        output.append(f"\n📆 Daily Breakdown:")
        for day in sorted(stats['messages_by_day'].keys())[-7:]:  # Last 7 days
            day_stats = stats['messages_by_day'][day]
            total = day_stats['user'] + day_stats['assistant']
            tokens = stats['tokens_by_day'][day]
            output.append(f"   {day}: {total} messages ({day_stats['user']} user, {day_stats['assistant']} assistant) | {tokens:,} tokens")
    
    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description='Analyze Clawdbot conversation statistics')
    parser.add_argument('--date', help='Analyze specific date (YYYY-MM-DD)')
    parser.add_argument('--week', action='store_true', help='Analyze last 7 days')
    parser.add_argument('--all', action='store_true', help='Analyze all time')
    parser.add_argument('--output', choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--sessions-dir', default='~/.openclaw/agents/main/sessions', help='Sessions directory path')
    
    args = parser.parse_args()
    
    # Determine date range
    end_date = datetime.now().date()
    start_date = None
    
    if args.date:
        start_date = end_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    elif args.week:
        start_date = end_date - timedelta(days=7)
    elif not args.all:
        # Default to today
        start_date = end_date
    
    # Get session files
    files = get_session_files(args.sessions_dir, start_date, end_date)
    
    if not files:
        print("No session files found.")
        return
    
    # Parse all messages
    all_messages = []
    for file in files:
        all_messages.extend(parse_session_file(file))
    
    if not all_messages:
        print("No messages found in session files.")
        return
    
    # Compute stats
    stats = compute_stats(all_messages)
    
    # Output
    if args.output == 'json':
        # Convert defaultdicts to regular dicts for JSON serialization
        json_stats = {
            **stats,
            'messages_by_day': dict(stats['messages_by_day']),
            'messages_by_hour': dict(stats['messages_by_hour']),
            'tokens_by_day': dict(stats['tokens_by_day'])
        }
        # Remove non-serializable fields
        json_stats.pop('message_lengths', None)
        json_stats.pop('response_times', None)
        print(json.dumps(json_stats, indent=2))
    else:
        print(format_text_output(stats))


if __name__ == '__main__':
    main()
