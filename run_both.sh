#!/bin/bash
# Run both the monitor and interactive bot together
# This script starts both services in the background

echo "Starting SAS EuroBonus services..."
echo ""

# Check if processes are already running
if pgrep -f "python.*sas_monitor.py" > /dev/null; then
    echo "⚠️  Monitor already running (PID: $(pgrep -f 'python.*sas_monitor.py'))"
else
    echo "Starting monitor..."
    nohup python3 sas_monitor.py > monitor.log 2>&1 &
    MONITOR_PID=$!
    echo "✅ Monitor started (PID: $MONITOR_PID)"
    echo "   Logs: monitor.log"
fi

if pgrep -f "python.*telegram_bot.py" > /dev/null; then
    echo "⚠️  Bot already running (PID: $(pgrep -f 'python.*telegram_bot.py'))"
else
    echo "Starting interactive bot..."
    nohup python3 telegram_bot.py > bot.log 2>&1 &
    BOT_PID=$!
    echo "✅ Bot started (PID: $BOT_PID)"
    echo "   Logs: bot.log"
fi

echo ""
echo "Both services are running!"
echo ""
echo "To check status:"
echo "  tail -f monitor.log  # Monitor logs"
echo "  tail -f bot.log      # Bot logs"
echo ""
echo "To stop services:"
echo "  pkill -f sas_monitor.py"
echo "  pkill -f telegram_bot.py"
