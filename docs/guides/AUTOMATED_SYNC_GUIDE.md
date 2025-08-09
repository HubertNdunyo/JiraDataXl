# Automated Sync Guide

## Overview

The JIRA Sync system now includes a built-in scheduler for automated synchronization. This eliminates the need for external cron jobs or manual sync triggers.

## Features

### 1. Built-in Scheduler
- **APScheduler Integration**: Uses Python's APScheduler library for reliable scheduling
- **Configurable Intervals**: Set sync frequency from 2 minutes to 2 hours
- **Enable/Disable Control**: Turn automated syncs on/off without affecting manual syncs
- **Real-time Status**: View next scheduled sync time and current status
- **Non-overlapping**: Prevents multiple syncs from running simultaneously

### 2. Web Interface
- **Location**: Admin Panel → Scheduler (`/admin/scheduler`)
- **Live Updates**: Status refreshes every 5 seconds
- **Manual Trigger**: Use the main dashboard "Start Sync" button (removed from scheduler page)
- **Visual Controls**: Slider and switch for easy configuration

### 3. API Endpoints
```bash
# Get scheduler status
GET /api/scheduler/status

# Update scheduler configuration
PUT /api/scheduler/config
Body: {
  "enabled": true,
  "interval_minutes": 30
}

# Enable scheduler
POST /api/scheduler/enable

# Disable scheduler
POST /api/scheduler/disable

# Note: No run-now endpoint - use /api/sync/start from main dashboard
```

## Configuration

### Default Settings
- **Status**: Enabled
- **Interval**: 2 minutes (currently configured)
- **Location**: `/backend/config/sync_config.json`
- **Thread Pool**: Uses separate thread to prevent blocking

### Recommended Settings
- **Small datasets (< 10k issues)**: 15-30 minutes
- **Medium datasets (10k-50k issues)**: 30-60 minutes
- **Large datasets (> 50k issues)**: 60-120 minutes

## How It Works

1. **Startup**: Scheduler initializes when the backend starts
2. **Configuration Loading**: Reads settings from `sync_config.json`
3. **Job Scheduling**: Creates an interval-based job if enabled
4. **Execution**: Runs sync at specified intervals
5. **Safety Checks**: 
   - Skips if sync already running
   - Skips if last sync was < 1 minute ago
   - Records sync type as "scheduled" in history

## Monitoring

### Dashboard
- Main dashboard shows sync status
- "Next sync time" displays when scheduler is active

### Sync History
- Scheduled syncs are marked with `sync_type: "scheduled"`
- Manual syncs show `sync_type: "manual"`
- Initiated by field shows "scheduler" for automated syncs

## Troubleshooting

### Scheduler Not Running
1. Check if enabled in config: `cat backend/config/sync_config.json`
2. Check backend logs for scheduler initialization
3. Verify APScheduler is installed: `pip list | grep apscheduler`

### Syncs Not Triggering
1. Check scheduler status via API or web interface
2. Verify no sync is currently running
3. Check for errors in backend logs
4. Ensure interval is reasonable (not too frequent)

### Performance Issues
1. Increase interval if syncs overlap
2. Adjust performance settings (workers, batch size)
3. Monitor system resources during syncs

## Migration from External Schedulers

If you were using cron or other external schedulers:

1. **Disable External Scheduler**: Remove cron jobs or systemd timers
2. **Configure Built-in Scheduler**: Set desired interval via web interface
3. **Enable Scheduler**: Toggle the enable switch
4. **Monitor**: Watch first few automated syncs to ensure proper operation

### Example: Removing Cron Job
```bash
# List current cron jobs
crontab -l

# Edit cron jobs
crontab -e
# Remove any JIRA sync entries

# Or remove all cron jobs for current user
crontab -r
```

## Security Considerations

- Scheduler runs with same permissions as backend process
- No additional authentication required for scheduled syncs
- All syncs are logged with timestamp and initiator
- Rate limiting prevents excessive API calls

## Best Practices

1. **Start Conservative**: Begin with longer intervals and decrease if needed
2. **Monitor Performance**: Check sync duration and adjust interval accordingly
3. **Use Off-Peak Hours**: Configure to run during low-activity periods if possible
4. **Regular Monitoring**: Check sync history weekly for failures
5. **Backup Before Changes**: Create configuration backup before major schedule changes

## Recent Bug Fixes (July 2025)

1. **Statistics Accumulation**: Fixed issue where project counts and issue counts were accumulating across multiple syncs. Each sync now starts with fresh statistics.
2. **Socket Hang Up Errors**: Resolved by implementing thread pool execution for syncs, preventing the event loop from being blocked.
3. **Sync History Accuracy**: Project counts now correctly show actual totals (e.g., 47/101) instead of accumulated values.

## Future Enhancements

Planned features for the scheduler:
- Cron expression support for complex schedules
- Multiple schedule support (e.g., hourly during business hours, daily after hours)
- Email notifications for sync failures
- Webhook notifications
- Schedule pause during maintenance windows
- Project-specific sync schedules