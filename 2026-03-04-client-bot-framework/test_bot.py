#!/usr/bin/env python3
"""
Quick test for the client bot framework.
Runs the bot in a subprocess, sends a POST request, verifies response, then stops the bot.
"""
import subprocess
import time
import sys
import json
import http.client

def test_bot():
    # Start bot
    print("Starting bot...")
    bot_proc = subprocess.Popen([sys.executable, 'sample_bot.py'], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)
    # Give it time to bind
    time.sleep(2)
    
    conn = http.client.HTTPConnection('127.0.0.1', 8000, timeout=5)
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': 'test-api-key'
    }
    body = json.dumps({'command': '/start'})
    
    try:
        conn.request('POST', '/', body, headers)
        resp = conn.getresponse()
        data = resp.read().decode('utf-8')
        print(f"Response status: {resp.status}")
        print(f"Response body: {data}")
        
        if resp.status != 200:
            print("FAIL: Expected status 200")
            return False
        
        parsed = json.loads(data)
        if parsed.get('result') != 'Welcome! Type /help to see available commands.':
            print(f"FAIL: Unexpected result: {parsed.get('result')}")
            return False
        
        print("SUCCESS: /start command works")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        print("Stopping bot...")
        bot_proc.terminate()
        bot_proc.wait()
        conn.close()

if __name__ == '__main__':
    success = test_bot()
    sys.exit(0 if success else 1)