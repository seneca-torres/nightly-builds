#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import requests

API_BASE = "https://api.fxtwitter.com"
DEFAULT_THREAD_LIMIT = 5
DEFAULT_TRUNCATE_CHARS = 280
USER_AGENT = "tweet-summary-cli/1.0"


class TweetSummaryError(Exception):
    pass


def parse_input(arg: str) -> Tuple[str, str]:
    arg = arg.strip()
    if not arg:
        raise TweetSummaryError("Empty input. Provide a tweet URL or tweet ID.")

    if re.fullmatch(r"\d{5,}", arg):
        return "i", arg

    try:
        parsed = urlparse(arg)
    except Exception as exc:
        raise TweetSummaryError(f"Invalid URL: {exc}")

    if not parsed.scheme or not parsed.netloc:
        raise TweetSummaryError("Invalid URL. Provide a full tweet URL or a tweet ID.")

    match = re.search(r"/status/(\d+)", parsed.path)
    if not match:
        raise TweetSummaryError("Could not find a tweet ID in the URL.")

    tweet_id = match.group(1)
    path_parts = [p for p in parsed.path.split("/") if p]
    screen_name = "i"
    if len(path_parts) >= 1 and path_parts[0] not in {"i"}:
        screen_name = path_parts[0]

    return screen_name, tweet_id


def fetch_tweet(screen_name: str, tweet_id: str) -> Dict:
    url = f"{API_BASE}/{screen_name}/status/{tweet_id}"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
    except requests.RequestException as exc:
        raise TweetSummaryError(f"Network error: {exc}")

    try:
        data = resp.json()
    except json.JSONDecodeError:
        raise TweetSummaryError("API returned invalid JSON.")

    if resp.status_code != 200 or data.get("code") != 200:
        message = data.get("message") or resp.reason or "Unknown error"
        raise TweetSummaryError(f"API error ({resp.status_code}): {message}")

    tweet = data.get("tweet")
    if not tweet:
        raise TweetSummaryError("API response missing tweet data.")

    return tweet


def format_date(created_at: Optional[str]) -> str:
    if not created_at:
        return "Unknown"
    try:
        dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
        return dt.strftime("%Y-%m-%d %H:%M %Z")
    except ValueError:
        return created_at


def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.strip().replace("\r\n", "\n").replace("\r", "\n")


def summarize_text(text: str) -> Tuple[str, bool]:
    summarize_path = shutil.which("summarize")
    if summarize_path:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as handle:
                handle.write(text)
                temp_path = handle.name
            proc = subprocess.run(
                [summarize_path, temp_path],
                text=True,
                capture_output=True,
                check=False,
            )
            if proc.returncode == 0:
                output = proc.stdout.strip()
                if output:
                    return output, True
        except OSError:
            pass
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    if len(text) <= DEFAULT_TRUNCATE_CHARS:
        return text, False
    return text[: DEFAULT_TRUNCATE_CHARS - 1].rstrip() + "…", False


def fetch_thread_parents(tweet: Dict, limit: int) -> Tuple[list, Optional[str]]:
    parents = []
    current = tweet
    while len(parents) < limit:
        parent_id = current.get("replying_to_status")
        parent_user = current.get("replying_to")
        if not parent_id:
            break
        screen_name = parent_user or "i"
        try:
            parent = fetch_tweet(screen_name, parent_id)
        except TweetSummaryError as exc:
            return parents, str(exc)
        parents.append(parent)
        current = parent
    return parents, None


def render_markdown(tweet: Dict, summarize: bool, thread_limit: int) -> str:
    author = tweet.get("author") or {}
    author_name = author.get("name", "Unknown")
    author_screen = author.get("screen_name", "unknown")
    created_at = format_date(tweet.get("created_at"))
    likes = tweet.get("likes", 0)
    retweets = tweet.get("retweets", 0)
    replies = tweet.get("replies", 0)

    raw_text = clean_text(tweet.get("text", ""))
    if summarize:
        body, used_summarize = summarize_text(raw_text)
    else:
        body, used_summarize = raw_text, False

    lines = []
    lines.append(f"# Tweet Summary")
    lines.append("")
    lines.append(f"## {author_name} (@{author_screen})")
    lines.append("")
    lines.append("**Metadata**")
    lines.append("")
    lines.append(f"- Date: {created_at}")
    lines.append(f"- Likes: {likes}")
    lines.append(f"- Retweets: {retweets}")
    lines.append(f"- Replies: {replies}")
    if tweet.get("url"):
        lines.append(f"- URL: {tweet['url']}")

    lines.append("")
    lines.append("**Tweet**")
    lines.append("")
    lines.append(body or "(No text)")

    if summarize and not used_summarize:
        lines.append("")
        lines.append("_Note: summarize command not available; text truncated._")

    parents, parent_error = fetch_thread_parents(tweet, thread_limit)
    if parents:
        lines.append("")
        lines.append(f"## Thread Context (Earlier Tweets, up to {thread_limit})")
        lines.append("")
        for idx, parent in enumerate(parents, 1):
            parent_author = parent.get("author") or {}
            parent_name = parent_author.get("name", "Unknown")
            parent_screen = parent_author.get("screen_name", "unknown")
            parent_date = format_date(parent.get("created_at"))
            parent_text = clean_text(parent.get("text", ""))
            lines.append(f"### {idx}. {parent_name} (@{parent_screen})")
            lines.append("")
            lines.append(f"- Date: {parent_date}")
            if parent.get("url"):
                lines.append(f"- URL: {parent['url']}")
            lines.append("")
            lines.append(parent_text or "(No text)")
            lines.append("")

    if parent_error:
        lines.append("")
        lines.append(f"_Thread fetch halted: {parent_error}_")

    return "\n".join(lines).strip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a tweet via FxEmbed API and output a markdown summary."
    )
    parser.add_argument(
        "tweet",
        help="Tweet URL (https://x.com/user/status/id) or numeric tweet ID",
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Summarize the tweet text using the 'summarize' command when available",
    )
    parser.add_argument(
        "--thread-limit",
        type=int,
        default=DEFAULT_THREAD_LIMIT,
        help="Max number of parent tweets to include when the tweet is part of a thread",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        screen_name, tweet_id = parse_input(args.tweet)
        tweet = fetch_tweet(screen_name, tweet_id)
        output = render_markdown(tweet, args.summarize, max(args.thread_limit, 0))
        sys.stdout.write(output)
        return 0
    except TweetSummaryError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
