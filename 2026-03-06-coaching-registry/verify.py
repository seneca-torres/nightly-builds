#!/usr/bin/env python3
"""
Verification script for coaching registry.
Runs a quick smoke test to ensure the CLI works as expected.
"""
import subprocess
import sys
import os
import tempfile
import sqlite3

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise RuntimeError(f"Command failed with exit code {result.returncode}")
    return result.stdout

def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        # init
        run_cmd(f"python3 coaching_registry.py --db {db_path} init")
        # ingest demo
        run_cmd(f"python3 coaching_registry.py --db {db_path} ingest --demo")
        # search head coach
        output = run_cmd(f"python3 coaching_registry.py --db {db_path} search --position 'Head Coach'")
        assert "Kalen DeBoer" in output
        assert "Washington" in output
        # search school Alabama
        output = run_cmd(f"python3 coaching_registry.py --db {db_path} search --school Alabama")
        assert "Alabama" in output
        assert "DeBoer" in output
        # search year 2023
        output = run_cmd(f"python3 coaching_registry.py --db {db_path} search --year 2023")
        assert "2023" in output
        # csv output
        output = run_cmd(f"python3 coaching_registry.py --db {db_path} search --position 'Head Coach' --output csv")
        assert "full_name,title,school,year" in output
        # json output (should be valid json)
        import json
        output = run_cmd(f"python3 coaching_registry.py --db {db_path} search --position 'Head Coach' --output json")
        data = json.loads(output)
        assert isinstance(data, list)
        assert len(data) >= 1
        # verify database schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM coaches")
        count = cursor.fetchone()[0]
        assert count == 3, f"Expected 3 coaches, got {count}"
        cursor.execute("SELECT COUNT(*) FROM coach_seasons")
        seasons = cursor.fetchone()[0]
        assert seasons == 6, f"Expected 6 seasons, got {seasons}"
        conn.close()
        print("✅ All verification tests passed!")

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)