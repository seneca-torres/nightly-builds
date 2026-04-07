# Config Diff Viewer 🔍

**Nightly Build — 2026-02-17**

Track changes to your clawdbot/openclaw config files over time. Take snapshots, diff them, and see exactly what changed and when.

## What It Does

- **Snapshots** `~/.openclaw/openclaw.json` and `~/clawd/config/*.json` with timestamps
- **Diffs** any two snapshots with colored unified-diff output
- **Redacts secrets** automatically (tokens, keys, passwords) — never leaks credentials in output
- **Tracks history** of any specific config key across all snapshots
- **Watch mode** monitors for changes live, alerting when something shifts

## Why It's Useful

Config files drift. After a gateway restart, a credential refresh, or a manual tweak, it's hard to remember what changed. This tool gives you a git-like audit trail for your configs without actually checking secrets into git.

## Quick Start

```bash
cd ~/clawd/nightly-builds/2026-02-17-config-diff-viewer

# Save your first snapshot
python3 config_diff.py snapshot

# (make a change to a config, or wait for a refresh...)

# Save another snapshot
python3 config_diff.py snapshot

# See what changed
python3 config_diff.py diff
```

## All Commands

```bash
# Take a snapshot of all tracked configs
python3 config_diff.py snapshot

# List all snapshots
python3 config_diff.py list

# Diff last two snapshots (most common)
python3 config_diff.py diff

# Diff two specific snapshots by ID
python3 config_diff.py diff 2026-02-17T02-00-00 2026-02-17T03-00-00

# Show a snapshot's full contents (secrets redacted)
python3 config_diff.py show
python3 config_diff.py show 2026-02-17T02-00-00

# Track how a specific key changed over time
python3 config_diff.py history model
python3 config_diff.py history session

# Watch for changes (snapshots every 60s, alerts on change)
python3 config_diff.py watch
python3 config_diff.py watch --interval 30
```

## Config Sources Tracked

| Name | Path | Description |
|------|------|-------------|
| `openclaw` | `~/.openclaw/openclaw.json` | Main gateway config |
| `clawdbot` | `~/clawd/config/clawdbot.json` | Agent config |
| `calendar` | `~/clawd/config/calendar_token.json` | OAuth token (staleness tracking) |

Add more sources by editing the `CONFIG_SOURCES` list at the top of `config_diff.py`.

## Snapshot Storage

Snapshots live in `~/.clawdbot/config-snapshots/<timestamp>/`. Each snapshot is a directory with one JSON file per source plus a `meta.json`.

## Testing

```bash
# Take a baseline snapshot
python3 config_diff.py snapshot

# Manually tweak something in a config, then:
python3 config_diff.py snapshot
python3 config_diff.py diff

# Should show colored diff of what changed (secrets redacted)

# List all captured snapshots
python3 config_diff.py list

# Track model setting history
python3 config_diff.py history model
```

## Notes

- No external dependencies — pure Python stdlib
- Secrets are automatically redacted in all output (keys, tokens, passwords)
- Snapshots are append-only; nothing is ever deleted automatically
- Works even if a config file is missing (marks as "not found")
