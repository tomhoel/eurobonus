# Systemd Service Files

These service files allow you to run the monitor and bot as system services on Linux.

## Installation (Linux only)

### 1. Copy service files

```bash
sudo cp systemd/*.service /etc/systemd/system/
```

### 2. Reload systemd

```bash
sudo systemctl daemon-reload
```

### 3. Enable services to start on boot

```bash
sudo systemctl enable telegram-bot.service
sudo systemctl enable sas-monitor.service
```

### 4. Start services

```bash
sudo systemctl start telegram-bot
sudo systemctl start sas-monitor
```

## Managing Services

### Check status

```bash
sudo systemctl status telegram-bot
sudo systemctl status sas-monitor
```

### View logs

```bash
sudo journalctl -u telegram-bot -f
sudo journalctl -u sas-monitor -f
```

Or check the log files directly:
```bash
tail -f /Users/tomhoel/Documents/eurobonus/bot.log
tail -f /Users/tomhoel/Documents/eurobonus/monitor.log
```

### Stop services

```bash
sudo systemctl stop telegram-bot
sudo systemctl stop sas-monitor
```

### Restart services

```bash
sudo systemctl restart telegram-bot
sudo systemctl restart sas-monitor
```

### Disable services (prevent auto-start on boot)

```bash
sudo systemctl disable telegram-bot
sudo systemctl disable sas-monitor
```

## Notes

- These files are for **Linux** systems with systemd (Ubuntu, Debian, CentOS, etc.)
- **macOS** uses launchd instead - these files won't work on macOS
- For macOS, use the `run_both.sh` script or run manually in terminals
- Update the `User` field in the service files if your username is different
- Update paths if you installed the project in a different directory
