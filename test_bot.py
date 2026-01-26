#!/usr/bin/env python3
"""
Quick test script for the Telegram bot functionality.
Tests route parsing and message formatting without requiring API calls.
"""

import sys
from pathlib import Path

# Test imports
try:
    from sas_monitor import SASAwardAPI, Config
    print("✅ Successfully imported from sas_monitor.py")
except ImportError as e:
    print(f"❌ Failed to import from sas_monitor.py: {e}")
    sys.exit(1)

try:
    # Check if telegram library is available
    import telegram
    print(f"✅ python-telegram-bot installed (version {telegram.__version__})")
except ImportError:
    print("❌ python-telegram-bot not installed")
    print("   Run: pip install python-telegram-bot")
    sys.exit(1)

try:
    from telegram_bot import parse_route, format_error_message, AIRPORT_NAMES
    print("✅ Successfully imported from telegram_bot.py")
except ImportError as e:
    print(f"❌ Failed to import from telegram_bot.py: {e}")
    sys.exit(1)

# Test route parsing
print("\n" + "="*50)
print("Testing route parsing...")
print("="*50)

test_cases = [
    ("OSL BKK", ("OSL", "BKK")),
    ("OSL - BKK", ("OSL", "BKK")),
    ("OSL-BKK", ("OSL", "BKK")),
    ("osl bkk", ("OSL", "BKK")),
    ("/search CPH NRT", ("CPH", "NRT")),
    ("invalid", None),
    ("OSL", None),
    ("OSL XXX", None),  # Invalid destination
]

all_passed = True
for test_input, expected in test_cases:
    result = parse_route(test_input)
    status = "✅" if result == expected else "❌"
    if result != expected:
        all_passed = False
    print(f"{status} '{test_input}' -> {result} (expected: {expected})")

if all_passed:
    print("\n✅ All route parsing tests passed!")
else:
    print("\n❌ Some route parsing tests failed")

# Test error message formatting
print("\n" + "="*50)
print("Testing error message formatting...")
print("="*50)

error_msg = format_error_message("invalid_format")
print(f"✅ Generated error message ({len(error_msg)} chars)")

# Test airport names
print("\n" + "="*50)
print("Available airports:")
print("="*50)
for code, name in sorted(AIRPORT_NAMES.items()):
    print(f"  {code} - {name}")

# Check config
print("\n" + "="*50)
print("Checking configuration...")
print("="*50)

config_path = Path("config.json")
if config_path.exists():
    try:
        config = Config.from_file(str(config_path))
        print(f"✅ Config loaded successfully")
        print(f"   Bot token: {'SET' if config.telegram_bot_token else 'NOT SET'}")
        print(f"   Chat ID: {config.telegram_chat_id if config.telegram_chat_id else 'NOT SET'}")
        print(f"   API URL: {config.base_url}")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
else:
    print(f"❌ Config file not found: {config_path}")

print("\n" + "="*50)
print("Test complete!")
print("="*50)
print("\nTo start the bot, run:")
print("  python3 telegram_bot.py")
