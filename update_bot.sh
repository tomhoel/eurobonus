#!/bin/bash
# Update script for SAS EuroBonus Telegram Bot on GCP
# Run this on your GCP VM to deploy updates

set -e

echo "🚀 Updating SAS EuroBonus Bot..."

# Pull latest changes
echo "📥 Pulling latest code..."
git pull origin main

# Rebuild and restart containers
echo "🐳 Rebuilding containers..."
docker-compose down
docker-compose up -d --build

# Wait a moment for services to start
sleep 3

# Check status
echo "✅ Checking status..."
docker-compose ps

echo ""
echo "📊 Recent logs:"
docker-compose logs --tail=20 bot

echo ""
echo "🎉 Bot updated successfully!"
echo ""
echo "Useful commands:"
echo "  docker-compose logs -f bot    # Watch bot logs"
echo "  docker-compose restart        # Restart services"
