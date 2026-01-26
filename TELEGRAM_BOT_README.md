# SAS EuroBonus Interactive Telegram Bot

Interactive Telegram bot that allows on-demand searching for SAS EuroBonus award seat availability.

## Features

- **/search** command - Query award availability for any supported route
- Real-time SAS API integration
- Formatted results showing Economy, Premium, and Business class availability
- Support for all Europe-Asia routes monitored by the main monitor

## Installation

### 1. Install Dependencies

The bot requires the `python-telegram-bot` library (version 20+):

```bash
pip install python-telegram-bot
```

Or install all requirements:

```bash
pip install requests python-telegram-bot
```

### 2. Configuration

The bot uses the same `config.json` as the monitor. Ensure your config has:

```json
{
    "telegram_bot_token": "8438473195:AAH5Sd50mTcGprKRIUVUDC1aEClz8tMvDUQ",
    "base_url": "https://www.sas.no/bff/award-finder/destinations/v1",
    "market": "no-no"
}
```

## Usage

### Start the Bot

```bash
python telegram_bot.py
```

Or with a custom config file:

```bash
python telegram_bot.py --config my_config.json
```

### Bot Commands

Once the bot is running, open Telegram and interact with your bot:

#### /start
Welcome message with quick overview

#### /help
Shows detailed help including all supported airports and cabin classes

#### /search ORIGIN DESTINATION
Search for award availability

**Examples:**
- `/search OSL BKK` - Oslo to Bangkok
- `/search CPH NRT` - Copenhagen to Tokyo Narita
- `/search AMS SIN` - Amsterdam to Singapore

**Supported formats:**
- `/search OSL BKK`
- `/search OSL - BKK`
- `/search OSL-BKK`
- `/search osl bkk` (case insensitive)

## Supported Routes

### Origins
- **OSL** - Oslo, Norway
- **CDG** - Paris, France
- **CPH** - Copenhagen, Denmark
- **AMS** - Amsterdam, Netherlands

### Destinations
- **BKK** - Bangkok, Thailand
- **NRT** - Tokyo Narita, Japan
- **HND** - Tokyo Haneda, Japan
- **KIX** - Osaka, Japan
- **PVG** - Shanghai, China
- **PEK** - Beijing, China
- **SGN** - Ho Chi Minh City, Vietnam
- **HAN** - Hanoi, Vietnam
- **SIN** - Singapore

### Cabin Classes
- **Economy (AG)** - 💺
- **Premium (AP)** - ⭐
- **Business (AB)** - 💼

## Example Output

When you search for a route, the bot returns formatted results:

```
🔍 Search: OSL → Bangkok (BKK)

📤 OUTBOUND (OSL → BKK):
  📅 Feb 15, 2026
     💺 Economy: 4
     ⭐ Premium: 2
     💼 Business: 1
  📅 Feb 16, 2026
     💺 Economy: 2

📥 RETURN (BKK → OSL):
  📅 Feb 22, 2026
     💺 Economy: 3
     ⭐ Premium: 1

🔗 Book on SAS
```

## Architecture

The bot is designed to run as a **separate process** from the main monitor:

- **sas_monitor.py** - Continuous monitoring with notifications for NEW releases
- **telegram_bot.py** - Interactive bot for on-demand searches

Both can run simultaneously without conflicts.

### Key Design Decisions

1. **Polling vs Webhooks**: Uses polling (simpler for local/personal deployment)
2. **Stateless**: No conversation state - each search is independent
3. **Reuses API Client**: Imports `SASAwardAPI` from `sas_monitor.py`
4. **Error Handling**: Graceful fallbacks for API failures
5. **Rate Limiting**: Inherits SAS API rate limits from the main client

## Running Both Services

You can run the monitor and bot simultaneously:

```bash
# Terminal 1 - Monitor (continuous background monitoring)
python sas_monitor.py

# Terminal 2 - Interactive bot
python telegram_bot.py
```

Or use a process manager like `systemd`, `supervisor`, or `screen`.

## Troubleshooting

### Bot not responding
- Check that the bot token is correct in config.json
- Verify the bot is running (check terminal logs)
- Ensure you started a conversation with the bot on Telegram

### "No availability data found"
- This is expected if the route has no award seats
- Try a different route or check SAS website directly

### API errors
- The SAS API may temporarily be unavailable
- Check your internet connection
- Verify the API endpoint is still valid

### Import errors
- Ensure `sas_monitor.py` is in the same directory
- Check that all dependencies are installed

## Development

### Adding New Features

The bot is structured for easy extension:

- **Command handlers**: Add new commands in the handlers section
- **Formatters**: Customize message formatting in `format_search_results()`
- **Route parsing**: Modify `parse_route()` for different input formats

### Testing

Test the bot locally before deployment:

```bash
# Test API connectivity
python sas_monitor.py --test

# Run bot in development mode
python telegram_bot.py
```

## Security Notes

- **Never commit** your bot token to version control
- Use environment variables for production deployments
- The bot token in the example config should be regenerated if exposed
- Consider implementing user authentication for public bots

## Production Deployment

For production deployment, consider:

1. **Process Management**: Use systemd or supervisor to keep bot running
2. **Webhooks**: Switch from polling to webhooks for better performance
3. **Logging**: Configure persistent logging to files
4. **Monitoring**: Add health checks and uptime monitoring
5. **Rate Limiting**: Implement per-user rate limits if bot is public

### Example systemd service

```ini
[Unit]
Description=SAS EuroBonus Telegram Bot
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/eurobonus
ExecStart=/usr/bin/python3 telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## License

Same as the main SAS monitor project.

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify configuration is correct
3. Test API connectivity with `python sas_monitor.py --test`
