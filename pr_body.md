nightly: tweet summarizer CLI using FxEmbed API

## What
A Python CLI tool that fetches a tweet via the FxEmbed API (api.fxtwitter.com) and outputs a clean markdown summary.

## Features
- Accepts tweet URL or tweet ID
- Optional `--summarize` flag to pass text through the `summarize` command (falls back to truncation)
- Includes metadata: author, date, likes, retweets, replies, URL
- Thread context: follows parent tweets up to a configurable limit
- Error handling for invalid URLs, network issues, API errors
- Self-contained, only requires `requests` (already installed)

## Usage
\`\`\`bash
python3 tweet_summary.py https://twitter.com/jack/status/20
python3 tweet_summary.py 20 --summarize
python3 tweet_summary.py <url> --thread-limit 5
\`\`\`

## Test
Run the included example:
\`\`\`bash
python3 tweet_summary.py https://twitter.com/jack/status/20
\`\`\`

## Notes
- FxEmbed API does not provide replies listing; thread context is built from parent chain.
- The `summarize` command must be installed for summarization to work; otherwise truncation is used.

## Files
- `tweet_summary.py` – main CLI script
- `README.md` – usage and examples

Built as part of the nightly "Surprise Me" build series.
