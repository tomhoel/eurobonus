# SAS EuroBonus Award Monitor & Telegram Bot

A comprehensive monitoring system and interactive Telegram bot for tracking SAS Star Alliance award ticket availability.

## Features

### Monitoring Script (`sas_monitor.py`)
- Monitors 36 Europe→Asia routes (OSL, CDG, CPH, AMS → BKK, NRT, HND, KIX, PVG, PEK, SGN, HAN, SIN)
- Tracks Economy, Premium, and Business class availability
- Sends Telegram notifications for new ticket releases
- Detects vanishing seats (when tickets are booked)
- SQLite database for historical tracking

### Telegram Bot (`telegram_bot.py`)
- **Interactive Buttons**: Quick destination buttons and action buttons
- **Commands**:
  - `/start` - Welcome with quick search buttons
  - `/search OSL BKK` - Search for availability
  - `/search OSL BKK July` - Search with month filter
  - `/calendar OSL BKK` - Emoji grid calendar view
  - `/history OSL BKK` - Release history
  - `/best` - Best Business Class availability
  - `/status` - System health dashboard
- **Smart Features**:
  - Connection Checker (suggests alternatives)
  - Month filtering
  - Inline keyboard navigation

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure `config.json`:
   ```json
   {
     "telegram_bot_token": "YOUR_BOT_TOKEN",
     "telegram_chat_id": "YOUR_CHAT_ID",
     "db_path": "sas_monitor.db"
   }
   ```

3. Initialize baseline (first run only):
   ```bash
   python sas_monitor.py --init-baseline
   ```

4. Run services:
   ```bash
   bash run_both.sh
   ```

## Files

- `sas_monitor.py` - Monitoring script with SAS API client
- `telegram_bot.py` - Interactive Telegram bot
- `run_both.sh` - Script to start both services
- `config.json` - Configuration file
- `requirements.txt` - Python dependencies

## License

MIT
