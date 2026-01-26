# SAS EuroBonus System Architecture

## Overview

The system consists of two independent services that both interact with the SAS API:

```
┌─────────────────────────────────────────────────────────────┐
│                     SAS Award Finder API                     │
│            https://www.sas.no/bff/award-finder/...          │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               │                               │
               ▼                               ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│    SAS Monitor Service       │  │   Interactive Bot Service    │
│    (sas_monitor.py)          │  │   (telegram_bot.py)          │
│                              │  │                              │
│  - Continuous monitoring     │  │  - On-demand searches        │
│  - 15-minute poll interval   │  │  - User-initiated via /search│
│  - Detects NEW releases      │  │  - Real-time queries         │
│  - Sends notifications       │  │  - Interactive responses     │
│  - Stores baseline in DB     │  │  - Stateless (no DB)         │
└──────────────┬───────────────┘  └──────────────┬───────────────┘
               │                                 │
               │                                 │
               ▼                                 ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│     SQLite Database          │  │      Telegram API            │
│   (sas_monitor.db)           │  │   (Bot Polling/Webhooks)     │
│                              │  │                              │
│  - availability              │  │  - Receive commands          │
│  - known_tickets (baseline)  │  │  - Send formatted responses  │
│  - notifications             │  │  - Handle /start, /help      │
└──────────────────────────────┘  └──────────────┬───────────────┘
                                                  │
                                                  │
                                                  ▼
                                   ┌──────────────────────────────┐
                                   │     Telegram User            │
                                   │                              │
                                   │  Sends: /search OSL BKK      │
                                   │  Receives: Formatted results │
                                   └──────────────────────────────┘
```

## Components

### 1. SAS Monitor (Background Service)

**File:** `sas_monitor.py`

**Purpose:** Continuous monitoring to detect NEW award releases

**Features:**
- Polls SAS API every 15 minutes (configurable)
- Checks 36 Europe→Asia routes (4 origins × 9 destinations)
- Stores availability in SQLite database
- Compares with baseline to detect NEW releases
- Sends Telegram notifications only for NEW or increased availability
- Runs independently - doesn't require user interaction

**Database Tables:**
- `availability` - Historical snapshots of seat availability
- `known_tickets` - Baseline tickets (initialized with --init-baseline)
- `notifications` - Log of sent notifications

**Workflow:**
```
1. Query SAS API for all 36 routes
2. For each route/date/cabin class combination:
   a. Check if seats are available
   b. Compare with previous availability
   c. Check if existed in baseline
   d. If NEW or increased → send notification
   e. Store current state in database
3. Sleep 15 minutes
4. Repeat
```

### 2. Interactive Bot (User-Facing Service)

**File:** `telegram_bot.py`

**Purpose:** On-demand searches via Telegram commands

**Features:**
- Responds to user commands (/start, /help, /search)
- Queries SAS API in real-time when user requests
- Formats and returns results immediately
- No database - stateless operation
- Runs independently from monitor

**Supported Commands:**
- `/start` - Welcome message and overview
- `/help` - Detailed help with airports and examples
- `/search ORIGIN DEST` - Query specific route

**Workflow:**
```
1. User sends: /search OSL BKK
2. Bot parses route (OSL → BKK)
3. Bot queries SAS API for that route
4. Bot formats results (outbound + return flights)
5. Bot sends formatted message with:
   - Available dates
   - Seat counts per cabin class
   - Direct booking link
```

### 3. Shared Components

**SASAwardAPI Class**

Both services use the same API client from `sas_monitor.py`:

```python
class SASAwardAPI:
    def get_availability(origin, destination, ...) -> list:
        """Query SAS Award Finder API"""
```

**Configuration**

Both services use `config.json`:

```json
{
    "telegram_bot_token": "...",
    "telegram_chat_id": "...",
    "base_url": "https://www.sas.no/bff/award-finder/destinations/v1",
    "market": "no-no",
    "poll_interval": 900
}
```

## Data Flow

### Monitor Service Data Flow

```
SAS API → SASAwardAPI → Monitor Logic → Database
                                      ↓
                            TelegramNotifier → Telegram API → User
```

### Interactive Bot Data Flow

```
User → Telegram → Bot Handlers → Parse Route → SASAwardAPI → SAS API
                                                              ↓
User ← Telegram ← Format Results ← API Response ←────────────┘
```

## Deployment Scenarios

### Scenario 1: Local Development

```bash
# Terminal 1
python3 sas_monitor.py --once    # Single check

# Terminal 2
python3 telegram_bot.py          # Interactive bot
```

### Scenario 2: Production (Both Services)

```bash
./run_both.sh    # Starts both in background
```

Or use systemd (Linux):
```bash
sudo systemctl start sas-monitor
sudo systemctl start telegram-bot
```

### Scenario 3: Bot Only (No Monitoring)

If you only want on-demand searches:

```bash
python3 telegram_bot.py
```

### Scenario 4: Monitor Only (No Interactive Bot)

If you only want automatic notifications:

```bash
python3 sas_monitor.py
```

## Key Design Decisions

### Why Two Separate Services?

1. **Different use cases**
   - Monitor: "Alert me when NEW tickets appear"
   - Bot: "Show me what's available NOW"

2. **Independent scaling**
   - Monitor runs on a schedule (every 15 min)
   - Bot responds to user demand (unlimited searches)

3. **Failure isolation**
   - If bot crashes, monitor keeps running
   - If monitor crashes, bot keeps responding

4. **Simplified logic**
   - Monitor focuses on change detection
   - Bot focuses on query formatting

### Why Polling Instead of Webhooks?

**For the bot:** Polling is simpler for local/personal deployment
- No need for public HTTPS endpoint
- No need for domain/SSL certificate
- Works behind firewalls/NAT
- Easy to run on laptop/personal server

**For production:** Can easily switch to webhooks by modifying bot initialization

### Why No Database for Bot?

- Bot queries are real-time (don't need historical data)
- Reduces complexity and dependencies
- Makes bot stateless and easier to scale
- Monitor already handles historical tracking

### Why Shared API Client?

- DRY principle (Don't Repeat Yourself)
- Consistent API request handling
- Easier to update if SAS changes API
- Both services benefit from improvements

## Rate Limiting

Both services respect SAS API rate limits:

- **Monitor:** Built-in delay (2 seconds between routes)
- **Bot:** Natural rate limiting (users don't spam searches)
- **Combined:** Services don't interfere with each other

If you run both:
- Monitor: 36 routes × 2 sec = 72 sec per cycle (every 15 min)
- Bot: Ad-hoc user requests (maybe 1-2 per minute max)
- Total: Well within API capacity

## Error Handling

Both services implement robust error handling:

1. **API Timeouts:** Retry with exponential backoff
2. **Network Errors:** Log and continue (don't crash)
3. **Invalid Data:** Graceful fallback to empty results
4. **Telegram Errors:** Log but don't fail the operation

## Security Considerations

1. **Bot Token:** Never commit to git, use environment variables
2. **Database:** SQLite file permissions (600)
3. **API Keys:** Stored in config.json (exclude from git)
4. **User Input:** Validated and sanitized before processing
5. **Webhook Validation:** Use secret token if using webhooks

## Monitoring and Logging

Both services log to stdout/files:

- **Monitor:** `monitor.log` (when using run_both.sh)
- **Bot:** `bot.log` (when using run_both.sh)

Log format:
```
2026-01-26 10:00:00 | INFO     | Message here
```

## Future Enhancements

Possible improvements:

1. **Bot Features:**
   - Subscribe to route notifications
   - Set price alerts
   - Compare multiple routes
   - Date range filtering

2. **Monitor Features:**
   - Email notifications
   - Slack/Discord integration
   - Price tracking
   - Multi-region support

3. **Infrastructure:**
   - Docker containers
   - Kubernetes deployment
   - Prometheus metrics
   - Grafana dashboards

4. **Performance:**
   - Redis caching
   - Connection pooling
   - Async request batching
   - CDN for static responses
