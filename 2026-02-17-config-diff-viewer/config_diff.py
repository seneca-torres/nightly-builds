#!/usr/bin/env python3
"""
config_diff.py — Config Diff Viewer for clawdbot / openclaw configs

Snapshots the current config and diffs against previous snapshots.
Tracks changes over time so you can see what changed and when.

Usage:
  python3 config_diff.py snapshot             # Save current config snapshot
  python3 config_diff.py list                 # List all snapshots
  python3 config_diff.py diff                 # Diff last two snapshots
  python3 config_diff.py diff <id1> <id2>     # Diff two specific snapshots
  python3 config_diff.py show <id>            # Show a snapshot's content
  python3 config_diff.py history <key>        # Track a key's value over time
  python3 config_diff.py watch               # Auto-snapshot + diff on change
"""

import argparse
import json
import os
import sys
import difflib
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

# ── Config sources to track ──────────────────────────────────────────────────
CONFIG_SOURCES = [
    {
        "name": "openclaw",
        "path": "~/.openclaw/openclaw.json",
        "description": "Main OpenClaw gateway config",
    },
    {
        "name": "clawdbot",
        "path": "~/clawd/config/clawdbot.json",
        "description": "Clawdbot agent config",
    },
    {
        "name": "calendar",
        "path": "~/clawd/config/calendar_token.json",
        "description": "Calendar OAuth token (track staleness only)",
    },
]

SNAPSHOT_DIR = Path("~/.clawdbot/config-snapshots").expanduser()
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────


def ts_now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


def load_json_safe(path: Path):
    """Load JSON, return dict or empty dict on error."""
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Not valid JSON — store raw text
        try:
            return {"_raw": path.read_text()[:4000]}
        except Exception:
            return {}
    except FileNotFoundError:
        return None


def flatten(obj, prefix="", sep="."):
    """Flatten nested dict to dot-separated keys."""
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            full = f"{prefix}{sep}{k}" if prefix else k
            if isinstance(v, (dict, list)):
                items.update(flatten(v, full, sep))
            else:
                items[full] = v
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            full = f"{prefix}[{i}]"
            if isinstance(v, (dict, list)):
                items.update(flatten(v, full, sep))
            else:
                items[full] = v
    else:
        items[prefix] = obj
    return items


def snapshot_path(snap_id: str, source_name: str) -> Path:
    return SNAPSHOT_DIR / snap_id / f"{source_name}.json"


def list_snapshots() -> list[str]:
    """Return sorted list of snapshot IDs (oldest first)."""
    if not SNAPSHOT_DIR.exists():
        return []
    dirs = sorted(
        [d.name for d in SNAPSHOT_DIR.iterdir() if d.is_dir()],
    )
    return dirs


def cmd_snapshot(args):
    snap_id = ts_now()
    snap_dir = SNAPSHOT_DIR / snap_id
    snap_dir.mkdir(parents=True, exist_ok=True)

    print(f"📸 Creating snapshot: {snap_id}")
    meta = {"id": snap_id, "created_at": datetime.now().isoformat(), "sources": {}}

    for src in CONFIG_SOURCES:
        path = Path(src["path"]).expanduser()
        data = load_json_safe(path)
        if data is None:
            print(f"  ⚠️  {src['name']}: not found at {src['path']}")
            meta["sources"][src["name"]] = {"status": "missing"}
            continue

        out_path = snap_dir / f"{src['name']}.json"
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        content_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True, default=str).encode()
        ).hexdigest()[:12]
        meta["sources"][src["name"]] = {"status": "ok", "hash": content_hash}
        print(f"  ✅  {src['name']}: saved ({content_hash})")

    # Write metadata
    with open(snap_dir / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    # Check if anything changed vs last snapshot
    snaps = list_snapshots()
    if len(snaps) >= 2:
        prev_id = snaps[-2]  # second-to-last (we just created the last)
        changed = _check_changes(prev_id, snap_id)
        if changed:
            print(f"\n🔄 Changes detected since {prev_id}:")
            for c in changed:
                print(f"  • {c}")
        else:
            print("\n✨ No changes since last snapshot.")

    print(f"\n✅ Snapshot saved: {snap_id}")
    return snap_id


def _check_changes(id1: str, id2: str) -> list[str]:
    """Return list of human-readable change summaries."""
    changes = []
    for src in CONFIG_SOURCES:
        name = src["name"]
        p1 = SNAPSHOT_DIR / id1 / f"{name}.json"
        p2 = SNAPSHOT_DIR / id2 / f"{name}.json"

        d1 = json.loads(p1.read_text()) if p1.exists() else {}
        d2 = json.loads(p2.read_text()) if p2.exists() else {}

        f1 = flatten(d1)
        f2 = flatten(d2)

        all_keys = set(f1) | set(f2)
        for k in sorted(all_keys):
            v1 = f1.get(k, "‹missing›")
            v2 = f2.get(k, "‹missing›")
            if v1 != v2:
                # Redact secrets
                if any(s in k.lower() for s in ("token", "secret", "key", "pass", "auth")):
                    v1_disp = "***" if v1 != "‹missing›" else v1
                    v2_disp = "***" if v2 != "‹missing›" else v2
                else:
                    v1_disp = str(v1)[:60]
                    v2_disp = str(v2)[:60]
                changes.append(f"[{name}] {k}: {v1_disp!r} → {v2_disp!r}")
    return changes


def cmd_list(args):
    snaps = list_snapshots()
    if not snaps:
        print("No snapshots yet. Run: python3 config_diff.py snapshot")
        return

    print(f"📋 Config Snapshots ({len(snaps)} total)\n")
    for i, snap_id in enumerate(snaps):
        meta_path = SNAPSHOT_DIR / snap_id / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            sources = meta.get("sources", {})
            ok = sum(1 for s in sources.values() if s.get("status") == "ok")
            total = len(sources)
            label = "(latest)" if i == len(snaps) - 1 else ""
            print(f"  {i+1:3}. {snap_id}  [{ok}/{total} sources] {label}")
        else:
            print(f"  {i+1:3}. {snap_id}")

    print(f"\nUsage: python3 config_diff.py diff  (last two)")
    print(f"       python3 config_diff.py diff <id1> <id2>")


def cmd_diff(args):
    snaps = list_snapshots()
    if not snaps:
        print("No snapshots. Run: python3 config_diff.py snapshot")
        return

    if hasattr(args, "id1") and args.id1:
        id1, id2 = args.id1, args.id2
    elif len(snaps) >= 2:
        id1, id2 = snaps[-2], snaps[-1]
    else:
        print("Need at least 2 snapshots to diff.")
        return

    print(f"🔍 Diff: {id1}  →  {id2}\n")

    any_diff = False
    for src in CONFIG_SOURCES:
        name = src["name"]
        p1 = SNAPSHOT_DIR / id1 / f"{name}.json"
        p2 = SNAPSHOT_DIR / id2 / f"{name}.json"

        if not p1.exists() and not p2.exists():
            continue

        t1 = p1.read_text() if p1.exists() else "{}"
        t2 = p2.read_text() if p2.exists() else "{}"

        if t1 == t2:
            print(f"  [{name}] ✅ No changes")
            continue

        # Pretty unified diff
        lines1 = t1.splitlines(keepends=True)
        lines2 = t2.splitlines(keepends=True)

        diff = list(
            difflib.unified_diff(
                lines1,
                lines2,
                fromfile=f"{name} ({id1})",
                tofile=f"{name} ({id2})",
                n=2,
            )
        )

        # Redact secrets in diff output
        redacted = []
        for line in diff:
            lower = line.lower()
            if any(s in lower for s in ("token", "secret", "key", "pass", "auth")):
                # Show the key name but redact the value
                if ":" in line and (line.startswith("+") or line.startswith("-")):
                    parts = line.split(":", 1)
                    line = parts[0] + ': "***REDACTED***"\n'
            redacted.append(line)

        any_diff = True
        print(f"\n── [{name}] Changes ──")
        # Colorize if terminal supports it
        use_color = sys.stdout.isatty()
        for line in redacted:
            if use_color:
                if line.startswith("+") and not line.startswith("+++"):
                    print(f"\033[32m{line}\033[0m", end="")
                elif line.startswith("-") and not line.startswith("---"):
                    print(f"\033[31m{line}\033[0m", end="")
                elif line.startswith("@@"):
                    print(f"\033[36m{line}\033[0m", end="")
                else:
                    print(line, end="")
            else:
                print(line, end="")

    if not any_diff:
        print("\n✨ Configs are identical between these two snapshots.")


def cmd_show(args):
    snaps = list_snapshots()
    snap_id = args.id if hasattr(args, "id") and args.id else (snaps[-1] if snaps else None)
    if not snap_id:
        print("No snapshots available.")
        return

    print(f"📄 Snapshot: {snap_id}\n")
    for src in CONFIG_SOURCES:
        name = src["name"]
        p = SNAPSHOT_DIR / snap_id / f"{name}.json"
        if not p.exists():
            print(f"  [{name}] ⚠️  Not captured")
            continue
        data = json.loads(p.read_text())
        flat = flatten(data)
        print(f"\n── [{name}] {src['description']} ──")
        for k, v in sorted(flat.items()):
            if any(s in k.lower() for s in ("token", "secret", "key", "pass", "auth")):
                v = "***REDACTED***"
            val_str = str(v)
            if len(val_str) > 80:
                val_str = val_str[:77] + "..."
            print(f"  {k}: {val_str}")


def cmd_history(args):
    key = args.key
    snaps = list_snapshots()
    if not snaps:
        print("No snapshots yet.")
        return

    print(f"📈 History for key: {key!r}\n")
    last_val = None
    for snap_id in snaps:
        for src in CONFIG_SOURCES:
            name = src["name"]
            p = SNAPSHOT_DIR / snap_id / f"{name}.json"
            if not p.exists():
                continue
            data = json.loads(p.read_text())
            flat = flatten(data)
            # Support partial key match
            matches = {k: v for k, v in flat.items() if key.lower() in k.lower()}
            for k, v in matches.items():
                if any(s in k.lower() for s in ("token", "secret", "key", "pass", "auth")):
                    v = "***REDACTED***"
                tag = " ← CHANGED" if v != last_val and last_val is not None else ""
                print(f"  {snap_id}  [{name}] {k}: {v}{tag}")
                last_val = v


def cmd_watch(args):
    """Take a snapshot, then loop every 60s and diff on change."""
    import time

    print("👁  Watching configs for changes. Ctrl-C to stop.\n")
    interval = getattr(args, "interval", 60)

    prev_snap = cmd_snapshot(argparse.Namespace())
    print(f"\nWatching every {interval}s …\n")

    try:
        while True:
            time.sleep(interval)
            new_snap = ts_now()
            snap_dir = SNAPSHOT_DIR / new_snap
            snap_dir.mkdir(parents=True, exist_ok=True)

            changed_sources = []
            for src in CONFIG_SOURCES:
                name = src["name"]
                path = Path(src["path"]).expanduser()
                data = load_json_safe(path)
                if data is None:
                    continue
                out_path = snap_dir / f"{name}.json"
                with open(out_path, "w") as f:
                    json.dump(data, f, indent=2, default=str)

                p_prev = SNAPSHOT_DIR / prev_snap / f"{name}.json"
                if p_prev.exists():
                    if p_prev.read_text() != out_path.read_text():
                        changed_sources.append(name)

            # Write minimal meta
            with open(snap_dir / "meta.json", "w") as f:
                json.dump({"id": new_snap, "created_at": datetime.now().isoformat()}, f)

            if changed_sources:
                print(f"\n🔔 [{new_snap}] Changes in: {', '.join(changed_sources)}")
                # Print a compact diff
                for src in CONFIG_SOURCES:
                    if src["name"] in changed_sources:
                        changes = _check_changes(prev_snap, new_snap)
                        for c in changes:
                            print(f"  • {c}")
                prev_snap = new_snap
            else:
                print(f"  [{new_snap}] No changes", end="\r")

    except KeyboardInterrupt:
        print("\nStopped.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Config Diff Viewer — track clawdbot/openclaw config changes over time",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("snapshot", help="Save a snapshot of current configs")
    sub.add_parser("list", help="List all snapshots")

    p_diff = sub.add_parser("diff", help="Diff between two snapshots (default: last two)")
    p_diff.add_argument("id1", nargs="?", help="First snapshot ID")
    p_diff.add_argument("id2", nargs="?", help="Second snapshot ID")

    p_show = sub.add_parser("show", help="Show a snapshot's contents")
    p_show.add_argument("id", nargs="?", help="Snapshot ID (default: latest)")

    p_hist = sub.add_parser("history", help="Track a config key over all snapshots")
    p_hist.add_argument("key", help="Key name (partial match supported)")

    p_watch = sub.add_parser("watch", help="Auto-snapshot and alert on changes")
    p_watch.add_argument("--interval", type=int, default=60, help="Check interval in seconds")

    args = parser.parse_args()

    dispatch = {
        "snapshot": cmd_snapshot,
        "list": cmd_list,
        "diff": cmd_diff,
        "show": cmd_show,
        "history": cmd_history,
        "watch": cmd_watch,
    }

    fn = dispatch.get(args.cmd)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
