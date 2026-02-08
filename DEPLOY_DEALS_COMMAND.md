# Deploy /deals Command to GCP

## Summary
Added new `/deals` command that shows hot award availability - routes with the most seats available right now!

## What Changed
1. **sas_monitor.py** - Added `get_best_deals()` database method
2. **telegram_bot.py** - Added `/deals` command handler + updated help text
3. **update_bot.sh** - Convenient update script

## SSH Deployment Commands

### Option 1: Quick Copy-Paste (Recommended)

SSH into your VM and run:

```bash
cd ~/eurobonus && \
git pull && \
docker-compose down && \
docker-compose up -d --build && \
docker-compose ps
```

### Option 2: Using the Update Script

```bash
# SSH into your VM
gcloud compute ssh eurobonus-bot --zone=us-west1-b

# Run the update script
cd ~/eurobonus
chmod +x update_bot.sh
./update_bot.sh
```

### Option 3: Manual Step-by-Step

```bash
# 1. SSH into VM
gcloud compute ssh eurobonus-bot --zone=us-west1-b

# 2. Navigate to project
cd ~/eurobonus

# 3. Pull latest changes
git pull

# 4. Stop current containers
docker-compose down

# 5. Rebuild and start
docker-compose up -d --build

# 6. Check logs
docker-compose logs -f bot
```

## Test the New Command

Once deployed, open Telegram and send:

```
/deals
```

Or filter by cabin:
```
/deals business
/deals economy
/deals premium
```

## Example Output

```
🔥 Hot Deals — All Cabins
_Top routes with most availability right now_

1. *OSL → BKK* (💼 Business)
   📅 12 dates, 💺 45 total seats
   🗓 02-15, 02-18, 02-22 +9 more

2. *CPH → NRT* (⭐ Premium)
   📅 8 dates, 💺 24 total seats
   🗓 03-05, 03-08, 03-12 +5 more

...

💡 Tips:
• /deals business — Business class only
• /search OSL-BKK — Search specific route
• /subscribe OSL BKK — Get alerts
```

## Troubleshooting

If the bot doesn't respond:
```bash
# Check logs
docker-compose logs bot

# Restart just the bot
docker-compose restart bot

# Check if database is accessible
docker-compose exec bot ls -la data/
```

## Rollback (if needed)

```bash
cd ~/eurobonus
git reset --hard HEAD~1
docker-compose up -d --build
```
