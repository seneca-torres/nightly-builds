#!/usr/bin/env python3
import re

sample = """1. **Systems Dashboard** ✅ (2026-01-28) — HTML dashboard with dark theme showing cron jobs, services, nightly builds, projects, and health (disk/mem/swap/temp). Auto-refresh every 60s. Location: `~/clawd/nightly-builds/2026-01-28/`"""
pattern = r'^\d+\. \*\*(.*?)\*\* ✅ \((.*?)\) — (.*?) Location: `(.*?)`(?:\. PR: (.*?))?$'
match = re.match(pattern, sample)
if match:
    print("Title:", match.group(1))
    print("Date:", match.group(2))
    print("Description:", match.group(3))
    print("Location:", match.group(4))
    print("PR:", match.group(5))
else:
    print("No match")
    # try alternative pattern without trailing slash
    pattern2 = r'^\d+\. \*\*(.*?)\*\* ✅ \((.*?)\) — (.*?) Location: `(.*?)`'
    match2 = re.match(pattern2, sample)
    if match2:
        print("Match2")
        print(match2.groups())