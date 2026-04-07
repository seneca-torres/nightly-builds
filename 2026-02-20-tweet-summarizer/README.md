# Tweet Summary CLI

A small Python CLI that fetches a tweet from the FxEmbed API (`api.fxtwitter.com`) and outputs a clean markdown summary.

## Requirements

- Python 3.9+
- `requests` installed
- Optional: `summarize` command (expected at `/opt/homebrew/bin/summarize`)

## Usage

```bash
python3 tweet_summary.py <tweet-url-or-id>
```

With summarization:

```bash
python3 tweet_summary.py <tweet-url-or-id> --summarize
```

Include more thread context (parent tweets):

```bash
python3 tweet_summary.py <tweet-url-or-id> --thread-limit 5
```

## Examples

Using a known public tweet from FxEmbed documentation:

```bash
python3 tweet_summary.py https://twitter.com/jack/status/20
```

Using a tweet ID only:

```bash
python3 tweet_summary.py 20
```

Using summarization:

```bash
python3 tweet_summary.py https://x.com/jack/status/20 --summarize
```

## Notes

- The FxEmbed API expects URLs of the form `https://api.fxtwitter.com/{user}/status/{id}`. When you provide only a tweet ID, the CLI uses a placeholder user because the API ignores the user segment for lookups.
- FxEmbed does not provide a replies listing in the status response. When a tweet is part of a thread (it replies to another tweet), the CLI follows the parent chain up to `--thread-limit` and includes those earlier tweets as thread context.
- If the `summarize` command is unavailable or fails, the CLI falls back to truncating the tweet text.

## Output Format

The CLI outputs markdown with:

- Heading and author (@screen_name)
- Metadata: date, likes, retweets, replies, URL
- Tweet text (optionally summarized)
- Thread context (parent tweets, when available)

## Error Handling

The CLI reports clear errors for:

- Invalid URLs or missing tweet IDs
- Network failures
- API errors or malformed responses

## Quick Test

```bash
python3 tweet_summary.py https://twitter.com/jack/status/20
```

If you want a different sample, provide any public tweet URL.
