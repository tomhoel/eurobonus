# SAS EuroBonus Project Structure

Complete file organization for the SAS EuroBonus award monitor and interactive bot.

## File Tree

```
/Users/tomhoel/Documents/eurobonus/
│
├── Core Application Files
│   ├── sas_monitor.py              # Background monitor service (original)
│   ├── telegram_bot.py             # Interactive bot service (NEW)
│   └── config.json                 # Configuration (shared by both)
│
├── Documentation
│   ├── QUICK_START.md              # Quick setup guide (NEW)
│   ├── TELEGRAM_BOT_README.md      # Comprehensive bot docs (NEW)
│   ├── ARCHITECTURE.md             # System architecture (NEW)
│   ├── EXAMPLES.md                 # Usage examples (NEW)
│   ├── IMPLEMENTATION_SUMMARY.md   # Implementation details (NEW)
│   └── PROJECT_STRUCTURE.md        # This file (NEW)
│
├── Installation & Setup
│   ├── install_bot.sh              # Automatic installation (NEW)
│   └── run_both.sh                 # Launcher for both services (NEW)
│
├── Testing & Utilities
│   ├── test_bot.py                 # Bot functionality tests (NEW)
│   ├── get_chat_id.py              # Get Telegram chat ID (existing)
│   ├── test_api_cookies.py         # API testing (existing)
│   ├── test_cookies.py             # Cookie testing (existing)
│   └── verify_session.py           # Session verification (existing)
│
├── Systemd Services (Linux)
│   └── systemd/
│       ├── README.md               # Service installation guide (NEW)
│       ├── telegram-bot.service    # Bot systemd unit (NEW)
│       └── sas-monitor.service     # Monitor systemd unit (NEW)
│
└── Runtime Files (generated)
    ├── sas_monitor.db              # SQLite database (created on first run)
    ├── monitor.log                 # Monitor logs (if using run_both.sh)
    └── bot.log                     # Bot logs (if using run_both.sh)
```

## File Descriptions

### Core Application

**sas_monitor.py** (23 KB)
- Background monitoring service
- Polls SAS API every 15 minutes
- Detects NEW award releases
- Sends Telegram notifications
- Stores data in SQLite database
- Original implementation (unchanged)

**telegram_bot.py** (14 KB) **NEW**
- Interactive Telegram bot
- Handles /start, /help, /search commands
- On-demand route queries
- Real-time SAS API integration
- Formatted result display
- Stateless operation (no database)

**config.json** (293 B)
- Shared configuration file
- Contains bot token, chat ID
- API endpoints and settings
- Used by both services

### Documentation

**QUICK_START.md** (3.7 KB) **NEW**
- Quick setup instructions
- Installation steps
- Basic usage examples
- Troubleshooting tips

**TELEGRAM_BOT_README.md** (5.6 KB) **NEW**
- Comprehensive documentation
- Detailed feature list
- All commands explained
- Production deployment guide
- Security considerations

**ARCHITECTURE.md** (9.8 KB) **NEW**
- System architecture diagrams
- Data flow explanations
- Design decisions
- Component relationships
- Deployment scenarios

**EXAMPLES.md** (5.3 KB) **NEW**
- Real-world usage examples
- All command variations
- Expected bot responses
- Tips and best practices
- Comparison scenarios

**IMPLEMENTATION_SUMMARY.md** (11 KB) **NEW**
- Complete implementation details
- Technical specifications
- Feature checklist
- Performance characteristics
- Future enhancements

**PROJECT_STRUCTURE.md** (This file) **NEW**
- File organization
- Directory structure
- File descriptions
- Size and purpose

### Installation & Setup

**install_bot.sh** (951 B) **NEW**
- Automatic dependency installation
- Python version check
- Library installation (python-telegram-bot)
- Success/failure reporting
- Executable script

**run_both.sh** (1.1 KB) **NEW**
- Starts both services in background
- Process conflict detection
- Log file creation
- PID tracking
- Status reporting
- Executable script

### Testing & Utilities

**test_bot.py** (2.8 KB) **NEW**
- Route parsing tests
- Import validation
- Configuration checks
- Message formatting tests
- Airport database validation
- Executable script

**get_chat_id.py** (701 B)
- Utility to get Telegram chat ID
- Original utility (existing)

**test_api_cookies.py** (1.5 KB)
- SAS API testing with cookies
- Original testing utility (existing)

**test_cookies.py** (1.4 KB)
- Cookie validation
- Original testing utility (existing)

**verify_session.py** (1.3 KB)
- Session verification
- Original testing utility (existing)

### Systemd Services

**systemd/README.md** (1.6 KB) **NEW**
- Systemd installation guide
- Service management commands
- Linux-specific instructions
- Alternative deployment methods

**systemd/telegram-bot.service** (554 B) **NEW**
- Systemd unit file for bot
- Auto-restart configuration
- Logging setup
- Security settings

**systemd/sas-monitor.service** (550 B) **NEW**
- Systemd unit file for monitor
- Auto-restart configuration
- Logging setup
- Security settings

### Runtime Files

**sas_monitor.db**
- SQLite database (created automatically)
- Contains availability history
- Baseline ticket records
- Notification logs
- Created by sas_monitor.py

**monitor.log**
- Monitor service logs (when using run_both.sh)
- Timestamped entries
- API request logs
- Error messages

**bot.log**
- Bot service logs (when using run_both.sh)
- User interaction logs
- Search queries
- Error messages

## File Categories by Purpose

### Must-Have Files (Required)
```
sas_monitor.py          # Original monitor
telegram_bot.py         # Interactive bot (NEW)
config.json            # Configuration
```

### Documentation (Recommended)
```
QUICK_START.md         # Start here!
TELEGRAM_BOT_README.md # Full documentation
EXAMPLES.md           # Usage examples
```

### Setup Scripts (Helpful)
```
install_bot.sh        # Easy installation
run_both.sh          # Easy launching
test_bot.py          # Validation
```

### Advanced (Optional)
```
ARCHITECTURE.md              # For developers
IMPLEMENTATION_SUMMARY.md    # Technical details
systemd/*.service           # Production deployment
```

## File Sizes

```
Total project files:     18 files
Total documentation:     ~50 KB
Total code:             ~40 KB
Total size:             ~90 KB

New files added:         12 files
New code:               ~15 KB
New documentation:      ~35 KB
```

## File Dependencies

### telegram_bot.py depends on:
- sas_monitor.py (imports SASAwardAPI, Config)
- config.json (configuration)
- python-telegram-bot library

### sas_monitor.py depends on:
- config.json (configuration)
- requests library
- SQLite (built-in)

### Both services can run:
- Independently (either one alone)
- Simultaneously (both together)
- No shared state or locks

## Quick Reference

### To Start
```bash
# Install dependencies
./install_bot.sh

# Test setup
python3 test_bot.py

# Start bot only
python3 telegram_bot.py

# Start both services
./run_both.sh
```

### To Read
```bash
# Quick start
cat QUICK_START.md

# Full documentation
cat TELEGRAM_BOT_README.md

# Examples
cat EXAMPLES.md
```

### To Deploy (Linux)
```bash
# Copy service files
sudo cp systemd/*.service /etc/systemd/system/

# Enable and start
sudo systemctl enable telegram-bot sas-monitor
sudo systemctl start telegram-bot sas-monitor
```

## File Permissions

All scripts are executable:
```
-rwxr-xr-x  install_bot.sh
-rwxr-xr-x  run_both.sh
-rwxr-xr-x  test_bot.py
```

All Python files are readable:
```
-rw-r--r--  sas_monitor.py
-rw-r--r--  telegram_bot.py
```

All documentation is readable:
```
-rw-r--r--  *.md
```

## Git Status

Files to commit (if using git):
```
# New files
telegram_bot.py
QUICK_START.md
TELEGRAM_BOT_README.md
ARCHITECTURE.md
EXAMPLES.md
IMPLEMENTATION_SUMMARY.md
PROJECT_STRUCTURE.md
install_bot.sh
run_both.sh
test_bot.py
systemd/

# Modified files
(none - existing files unchanged)
```

Files to ignore (.gitignore):
```
*.log
*.db
*.pyc
__pycache__/
.env
config.json  # Contains secrets!
```

## Summary

This project now contains:
- **1 original service** (monitor) - unchanged and working
- **1 new service** (bot) - fully implemented and tested
- **6 documentation files** - comprehensive guides
- **3 utility scripts** - installation, testing, launching
- **3 deployment files** - systemd services for Linux

Everything is production-ready and well-documented!
