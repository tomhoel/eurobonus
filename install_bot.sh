#!/bin/bash
# Installation script for SAS EuroBonus Telegram Bot

echo "================================"
echo "SAS EuroBonus Telegram Bot Setup"
echo "================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "Error: Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo ""
echo "Installing dependencies..."
pip3 install python-telegram-bot requests

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation successful!"
    echo ""
    echo "Next steps:"
    echo "1. Ensure config.json has your telegram_bot_token"
    echo "2. Run: python3 telegram_bot.py"
    echo "3. Open Telegram and send /start to your bot"
    echo ""
    echo "For detailed instructions, see TELEGRAM_BOT_README.md"
else
    echo ""
    echo "❌ Installation failed. Please install manually:"
    echo "   pip3 install python-telegram-bot requests"
    exit 1
fi
