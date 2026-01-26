# Quick Start Guide - Interactive Telegram Bot

## What's New

You now have an **interactive Telegram bot** that lets you search for SAS award availability on-demand using the `/search` command.

## Installation (One-time Setup)

### Option 1: Automatic Installation

```bash
cd /Users/tomhoel/Documents/eurobonus
./install_bot.sh
```

### Option 2: Manual Installation

```bash
pip install python-telegram-bot
```

## Running the Bot

### Start the Interactive Bot

```bash
python3 telegram_bot.py
```

You should see:
```
2026-01-26 10:00:00 | INFO     | Bot initialized successfully
2026-01-26 10:00:00 | INFO     | Starting SAS EuroBonus Award Search Bot
2026-01-26 10:00:00 | INFO     | Bot is running. Press Ctrl+C to stop.
```

### Using the Bot on Telegram

1. Open Telegram
2. Find your bot (the one with token 8438473195:AAH5Sd50mTcGprKRIUVUDC1aEClz8tMvDUQ)
3. Send commands:

```
/start          - Welcome message
/help           - Show help and available routes
/search OSL BKK - Search Oslo to Bangkok
/search CPH NRT - Search Copenhagen to Tokyo
```

## Example Usage

**You type:**
```
/search OSL BKK
```

**Bot responds:**
```
🔍 Search: OSL → Bangkok (BKK)

📤 OUTBOUND (OSL → BKK):
  📅 Feb 15, 2026
     💺 Economy: 4
     ⭐ Premium: 2
     💼 Business: 1
  📅 Feb 20, 2026
     💺 Economy: 6
     💼 Business: 2

📥 RETURN (BKK → OSL):
  📅 Feb 22, 2026
     💺 Economy: 3
     ⭐ Premium: 1

🔗 Book on SAS
```

## Running Both Services Together

You can run both the **monitor** (continuous background monitoring) and the **interactive bot** at the same time:

### Option 1: Use the launcher script

```bash
./run_both.sh
```

### Option 2: Manual (separate terminals)

```bash
# Terminal 1 - Monitor
python3 sas_monitor.py

# Terminal 2 - Bot
python3 telegram_bot.py
```

## Testing

Before running the bot, test that everything is set up correctly:

```bash
python3 test_bot.py
```

This will check:
- Required libraries are installed
- Route parsing works correctly
- Configuration is loaded properly
- Available airports are displayed

## Troubleshooting

### Bot not responding

**Check if bot is running:**
```bash
ps aux | grep telegram_bot
```

**Check logs:**
```bash
tail -f bot.log
```

### Missing library error

```bash
pip install python-telegram-bot
```

### Import errors

Make sure you're in the correct directory:
```bash
cd /Users/tomhoel/Documents/eurobonus
python3 telegram_bot.py
```

### API errors

Test API connectivity:
```bash
python3 sas_monitor.py --test
```

## File Overview

New files created:

- **telegram_bot.py** - Main interactive bot implementation
- **TELEGRAM_BOT_README.md** - Detailed documentation
- **install_bot.sh** - Automatic installation script
- **test_bot.py** - Test script to verify setup
- **run_both.sh** - Launcher for both services
- **QUICK_START.md** - This file

Existing files (unchanged):

- **sas_monitor.py** - Background monitor (still works the same)
- **config.json** - Configuration (used by both)

## Key Features

1. **On-demand searches** - Query any route whenever you want
2. **Real-time data** - Fetches current availability from SAS API
3. **Formatted results** - Clear display of Economy/Premium/Business seats
4. **Both directions** - Shows outbound AND return flights
5. **Direct booking links** - Quick link to SAS website

## Supported Routes

**Origins:** OSL, CDG, CPH, AMS
**Destinations:** BKK, NRT, HND, KIX, PVG, PEK, SGN, HAN, SIN

**That's 36 route combinations you can search!**

## Next Steps

1. Install dependencies: `./install_bot.sh`
2. Test setup: `python3 test_bot.py`
3. Start bot: `python3 telegram_bot.py`
4. Open Telegram and send `/search OSL BKK`

Enjoy your interactive SAS award search bot!
