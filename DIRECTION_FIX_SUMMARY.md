# Direction Bug Fix Summary

## Problem
The `ticket_summary` table did not track direction (outbound vs inbound), causing data from inbound flights to overwrite outbound flight data.

### Example Bug Scenario
For CPH → BKK on Feb 3:
- Monitor checks **outbound** (CPH → BKK): Business = 0 seats
- Monitor checks **inbound** (BKK → CPH): Business = 6 seats
- The inbound data would overwrite the outbound data
- Result: Catalogue showed 6 business seats when outbound actually had 0

## Solution
Added `direction` column to the `ticket_summary` table and included it in the PRIMARY KEY to ensure outbound and inbound flights are tracked separately.

## Files Modified

### 1. `/Users/tomhoel/Documents/eurobonus/eurobonus/sas_monitor.py`

#### Schema Changes (Line 249-262)
- **Added** `direction TEXT NOT NULL` column to `ticket_summary` table
- **Updated** PRIMARY KEY to include `direction`: `PRIMARY KEY (origin, destination, date, cabin_class, direction)`

#### Function Updates

**get_ticket_summary()** (Line 437-470)
- Added `direction` parameter (optional, with legacy fallback)
- Updated SQL queries to include direction in WHERE clause

**upsert_ticket_summary()** (Line 472-520)
- Added `direction` parameter with default value `"outbound"`
- Updated INSERT to include direction column
- Updated UPDATE WHERE clause to include direction

**get_route_summary_with_changes()** (Line 667-705)
- Updated SELECT to include direction column
- Updated result dict to include direction field
- Updated ORDER BY to include direction

**get_all_tracked_tickets()** (Line 580-607)
- Updated SELECT to include direction column
- Updated ORDER BY to include direction

**get_hot_tickets()** (Line 610-624)
- Updated SELECT to include direction column

**check_route()** (Lines 1089-1209)
- Updated all calls to `get_ticket_summary()` to pass direction
- Updated all calls to `upsert_ticket_summary()` to pass direction
- Updated logging to include direction information

**Notification Functions** (Lines 1307-1400)
- Updated calls to `get_ticket_summary()` to include direction from ticket dict

### 2. `/Users/tomhoel/Documents/eurobonus/eurobonus/telegram_bot.py`

#### catalogue_command() (Line 1161-1286)
- **Updated** grouping to include direction: `route_key = (origin, destination, direction)`
- **Added** direction emoji display: `→` for outbound, `←` for inbound
- **Updated** route header to show direction

#### velocity_command() (Line 1070-1115)
- **Updated** tuple unpacking to include direction field
- **Added** direction_emoji variable
- **Updated** message formatting to show direction

#### stats_command() (Line 1146-1147)
- **Fixed** index for velocity field (now at index 7 instead of 6)

#### tickets_command() (Line 1568-1609)
- **Updated** tuple unpacking to include direction field
- **Updated** grouping to include direction: `route_key = (orig, destination, direction)`
- **Added** direction emoji and label to route display

#### build_catalogue_page() (Line 1291-1390)
- **Updated** filter indices for currently_available (now index 6)
- **Updated** sort indices for all fields
- **Updated** grouping to include direction
- **Updated** route display to show direction emoji and label
- **Updated** ticket field indices (max_issued=5, curr_avail=6, total_booked=7)

### 3. Migration Script (New File)

**`/Users/tomhoel/Documents/eurobonus/eurobonus/migrate_add_direction.py`**
- Creates backup of existing ticket_summary table
- Creates new table with direction column
- Migrates existing data (defaults all to 'outbound')
- Restores from backup on failure
- Handles case where table doesn't exist yet

### 4. Test Script (New File)

**`/Users/tomhoel/Documents/eurobonus/eurobonus/test_direction_fix.py`**
- Verifies direction column in PRIMARY KEY
- Tests that outbound/inbound records are separate
- Confirms no data overwriting occurs
- Validates PRIMARY KEY constraint

## Database Schema Change

### Before
```sql
PRIMARY KEY (origin, destination, date, cabin_class)
```

### After
```sql
PRIMARY KEY (origin, destination, date, cabin_class, direction)
```

## Data Impact

For existing databases:
1. Run `python3 migrate_add_direction.py` to update schema
2. Existing records will be set to `direction='outbound'`
3. Run the monitor to populate new inbound data
4. Both directions will now be tracked separately

For fresh databases:
- New schema will be created automatically with direction column
- No migration needed

## Testing

Run the test script to verify the fix:
```bash
python3 test_direction_fix.py
```

Expected output: All tests should pass, confirming:
- Outbound and inbound are stored separately
- Direction is part of PRIMARY KEY
- No data overwriting occurs

## User-Visible Changes

### Telegram Bot Commands

1. **/catalogue** - Now shows direction for each route:
   - `CPH → Bangkok (outbound)`
   - `CPH ← Bangkok (inbound)`

2. **/tickets** - Groups tickets by direction:
   - Separate sections for outbound and inbound

3. **/velocity** - Shows direction for hot tickets:
   - `CPH → BKK` or `CPH ← BKK`

## Verification

To verify the fix is working:

1. Check database schema:
```bash
sqlite3 sas_monitor.db "PRAGMA table_info(ticket_summary)"
```
Should show `direction` column at position 4.

2. Check for duplicate records:
```bash
sqlite3 sas_monitor.db "SELECT origin, destination, date, cabin_class, direction, currently_available FROM ticket_summary WHERE origin='CPH' AND destination='BKK' ORDER BY direction"
```
Should show separate records for outbound and inbound.

3. Test in Telegram:
- Run `/catalogue`
- Look for routes with both directions listed
- Verify seat counts are different for outbound vs inbound

## Rollback Plan

If issues occur, restore from backup:
1. Stop the monitor
2. Replace database with backup
3. Restart with previous code version

The migration script creates a backup before making changes.
