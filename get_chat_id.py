#!/usr/bin/env python3
"""Quick script to get your Telegram chat ID"""
import requests
import sys

if len(sys.argv) < 2:
    print("Usage: python get_chat_id.py YOUR_BOT_TOKEN")
    sys.exit(1)

token = sys.argv[1]
url = f"https://api.telegram.org/bot{token}/getUpdates"

print("Send a message to your bot in Telegram, then press Enter...")
input()

response = requests.get(url)
data = response.json()

if data.get("result"):
    for update in data["result"]:
        chat_id = update.get("message", {}).get("chat", {}).get("id")
        if chat_id:
            print(f"\nYour Chat ID: {chat_id}")
            break
else:
    print("No messages found. Make sure you sent a message to your bot first.")