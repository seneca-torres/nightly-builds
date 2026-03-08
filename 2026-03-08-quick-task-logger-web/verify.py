#!/usr/bin/env python3
"""
Quick verification script for the Quick Task Logger.
Starts the server, tests GET / and POST /log, then stops.
"""
import json
import subprocess
import time
import urllib.request
import urllib.error
import sys
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8080
BASE_URL = f"http://{HOST}:{PORT}"


def wait_for_server(timeout=5):
    """Wait until server responds to GET /"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{BASE_URL}/", timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False


def test_get_entries():
    """Test GET /entries endpoint"""
    try:
        req = urllib.request.Request(f"{BASE_URL}/entries")
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status != 200:
                return False
            data = json.load(resp)
            assert "entries" in data
            return True
    except Exception as e:
        print(f"GET /entries failed: {e}")
        return False


def test_post_log():
    """Test POST /log with a sample entry"""
    payload = json.dumps({"text": "Test entry from verification", "category": "todo"}).encode()
    req = urllib.request.Request(f"{BASE_URL}/log", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status != 201:
                return False
            data = json.load(resp)
            assert data.get("ok") is True
            assert "entry" in data
            return True
    except Exception as e:
        print(f"POST /log failed: {e}")
        return False


def main():
    print("Starting server...")
    # Start server as subprocess
    server = subprocess.Popen([sys.executable, "server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        # Wait for server to be ready
        if not wait_for_server():
            print("ERROR: Server did not start within timeout")
            server.terminate()
            server.wait()
            return 1
        print("Server started.")

        # Run tests
        print("Testing GET /entries...")
        if not test_get_entries():
            print("FAIL: GET /entries test")
            return 1
        print("OK")

        print("Testing POST /log...")
        if not test_post_log():
            print("FAIL: POST /log test")
            return 1
        print("OK")

        print("All verification tests passed.")
        return 0
    finally:
        server.terminate()
        server.wait()


if __name__ == "__main__":
    sys.exit(main())