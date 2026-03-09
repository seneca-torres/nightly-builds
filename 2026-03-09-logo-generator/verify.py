#!/usr/bin/env python3
"""Verification script for logo_gen.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    target = Path("logo.svg")
    if target.exists():
        target.unlink()

    cmd = [sys.executable, "logo_gen.py"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Verification failed: logo_gen.py exited with non-zero status.")
        if result.stdout.strip():
            print("stdout:")
            print(result.stdout.strip())
        if result.stderr.strip():
            print("stderr:")
            print(result.stderr.strip())
        return 1

    if not target.exists():
        print("Verification failed: logo.svg was not created.")
        return 1

    if target.stat().st_size == 0:
        print("Verification failed: logo.svg is empty.")
        return 1

    print("Verification passed: logo.svg created successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
