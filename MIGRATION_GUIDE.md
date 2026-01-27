# Direction Column Migration Guide

## Quick Start

### For Existing Databases

1. **Stop the monitor** (if running):
   ```bash
   # Press Ctrl+C if monitor is running
   ```

2. **Run the migration**:
   ```bash
   cd /Users/tomhoel/Documents/eurobonus/eurobonus
   python3 migrate_add_direction.py
   ```

3. **Verify migration**:
   ```bash
   python3 test_direction_fix.py
   ```

4. **Restart the monitor**:
   ```bash
   python3 sas_monitor.py
   ```

### For Fresh Installations

No migration needed! The new schema will be created automatically when you first run the monitor.

## What the Migration Does

1. **Checks** if migration is needed (skips if already done)
2. **Creates backup** of existing ticket_summary table
3. **Creates new table** with direction column
4. **Migrates data** (all existing records → 'outbound')
5. **Recreates indexes**
6. **Drops backup** after successful migration

## Expected Output

```
Starting migration for: sas_monitor.db
Timestamp: 2026-01-27 23:44:31

1. Creating backup table...
   Backed up 150 records

2. Creating new ticket_summary table with direction column...

3. Migrating data from backup...
   Note: All existing records will be assigned direction='outbound'
   After migration completes, run the monitor to populate inbound data
   Migrated 150 records

4. Recreating indexes...

5. Dropping backup table...

✓ Migration completed successfully!

Summary:
  - Migrated 150 records
  - All existing records set to direction='outbound'
  - Primary key now includes direction

Next steps:
  1. Run the monitor to populate inbound flight data
  2. Check /catalogue in Telegram to see direction-separated data
```

## Verification Steps

### 1. Check Schema
```bash
sqlite3 sas_monitor.db "PRAGMA table_info(ticket_summary)" | grep direction
```
Should output:
```
4|direction|TEXT|1||0
```

### 2. Check Data
```bash
sqlite3 sas_monitor.db "SELECT DISTINCT direction FROM ticket_summary"
```
Initially should show only:
```
outbound
```

After monitor runs, should show:
```
inbound
outbound
```

### 3. Test Specific Route
```bash
sqlite3 sas_monitor.db "SELECT date, direction, cabin_class, currently_available FROM ticket_summary WHERE origin='CPH' AND destination='BKK' ORDER BY date, direction, cabin_class"
```
Should show separate records for each direction.

## Troubleshooting

### Migration Already Applied
```
✓ Migration already applied - 'direction' column exists
```
**Solution**: No action needed. Migration has already been completed.

### Table Doesn't Exist
```
✓ Table 'ticket_summary' does not exist yet - no migration needed
  The table will be created with the direction column when the monitor runs
```
**Solution**: No action needed. Run the monitor to create the new schema.

### Migration Failed
If migration fails, the script automatically:
1. Rolls back changes
2. Restores from backup
3. Exits with error message

**Solution**: Check the error message and fix the issue, then re-run migration.

### Manual Backup (Optional)
To create an extra backup before migration:
```bash
cp sas_monitor.db sas_monitor.db.backup.$(date +%Y%m%d_%H%M%S)
```

### Manual Rollback (Emergency)
If you need to manually rollback:
```bash
# Stop the monitor
sqlite3 sas_monitor.db
sqlite> DROP TABLE IF EXISTS ticket_summary;
sqlite> CREATE TABLE ticket_summary AS SELECT * FROM ticket_summary_backup;
sqlite> .quit
```

## After Migration

1. **Run the monitor** to populate inbound data:
   ```bash
   python3 sas_monitor.py --once
   ```

2. **Check Telegram bot**:
   - Run `/catalogue` command
   - You should see routes with both directions:
     - `CPH → Bangkok (outbound)`
     - `CPH ← Bangkok (inbound)`

3. **Verify different seat counts**:
   - Outbound and inbound should have independent seat availability
   - Example: Outbound might have 0 Business seats while inbound has 6

## Performance Impact

- **Storage**: Minimal increase (one TEXT column per row)
- **Query speed**: No significant impact (direction is part of indexes)
- **Monitor runtime**: No change (same number of API calls)

## Data Integrity

The migration preserves all existing data:
- ✓ All seat counts preserved
- ✓ All timestamps preserved
- ✓ All booking velocity data preserved
- ✓ All other columns unchanged

Only change: All existing records get `direction='outbound'` since the old schema didn't distinguish direction.

## Support

If you encounter any issues:

1. Check the error message from the migration script
2. Review the migration log output
3. Check that database file exists and is writable
4. Ensure no other processes are accessing the database
5. Try running with `--db-path` to specify exact path:
   ```bash
   python3 migrate_add_direction.py --db-path /full/path/to/sas_monitor.db
   ```
