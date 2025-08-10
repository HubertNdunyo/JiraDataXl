# Performance Tuning Guide

This guide covers how to optimize JIRA Sync Dashboard performance for your specific needs.

## Quick Start

Access the Performance Configuration UI at: **http://localhost:5648/admin/performance**

## Current Performance Metrics

With optimized settings, the system achieves:
- **500 issues/second** throughput
- **~90 seconds** for full sync of 45,000+ issues
- **97 projects** synced in parallel
- **56,000+ issues** stored in database

## Performance Parameters

### 1. Rate Limit Pause (`rate_limit_pause`)
**Current: 0.5 seconds | Default: 1.0 seconds**

Controls the delay between JIRA API requests.
- **Lower values** (0.1-0.3): Faster sync but risk of rate limiting
- **Safe range**: 0.3-0.5 seconds
- **Conservative**: 0.5-1.0 seconds
- **Impact**: Most significant factor for sync speed

### 2. Batch Size (`batch_size`)
**Current: 400 | Default: 200**

Number of issues fetched per JIRA API request.
- **Range**: 50-1000 issues
- **Optimal**: 200-500 for most JIRA instances
- **Trade-off**: Larger batches = fewer API calls but more memory usage
- **Impact**: Reduces total API calls needed

### 3. Max Workers (`max_workers`)
**Current: 10 | Default: 8**

Number of parallel worker threads for processing projects.
- **Range**: 1-20 workers
- **Optimal**: 8-12 for standard servers
- **Trade-off**: More workers = faster but higher CPU/memory usage
- **Impact**: Enables parallel project processing

### 4. Lookback Days (`lookback_days`)
**Current: 49 days | Default: 60 days**

How far back in history to sync issues.
- **Initial sync**: Use 60-365 days for complete history
- **Regular syncs**: 7-30 days is sufficient
- **Trade-off**: More days = more data but longer sync time
- **Impact**: Directly affects data volume

### 5. Connection Pool Size (`connection_pool_size`)
**Current: 20 | Default: 20**

Size of HTTP connection pool for JIRA API.
- **Range**: 10-50 connections
- **Optimal**: 20-30 for most cases
- **Trade-off**: More connections = better parallelism but more resources
- **Impact**: Affects parallel request handling

### 6. Project Timeout (`project_timeout`)
**Current: 300 seconds | Default: 300 seconds**

Maximum time to wait for a single project sync.
- **Range**: 60-1800 seconds
- **Use case**: Increase for very large projects
- **Impact**: Prevents hanging on slow projects

## Optimization Strategies

### For Maximum Speed (Aggressive)
⚠️ **Warning**: May trigger JIRA rate limits

```json
{
  "rate_limit_pause": 0.1,
  "batch_size": 500,
  "max_workers": 15,
  "lookback_days": 7,
  "connection_pool_size": 40
}
```
Expected: ~1 minute for full sync

### Balanced Performance (Recommended)
✅ **Safe and efficient**

```json
{
  "rate_limit_pause": 0.3,
  "batch_size": 400,
  "max_workers": 12,
  "lookback_days": 30,
  "connection_pool_size": 25
}
```
Expected: ~75 seconds for full sync

### Conservative (Safe)
✅ **No risk of rate limiting**

```json
{
  "rate_limit_pause": 0.5,
  "batch_size": 200,
  "max_workers": 8,
  "lookback_days": 60,
  "connection_pool_size": 20
}
```
Expected: ~2 minutes for full sync

## Using the Performance UI

1. **Navigate** to http://localhost:5648/admin/performance
2. **Login** with admin credentials
3. **Adjust sliders** to modify parameters
4. **Test Configuration** to see estimated impact
5. **Monitor warnings** for potentially risky settings
6. **Save Configuration** to apply changes
7. **Run sync** to test new settings

## Monitoring Performance

### Check Sync Statistics
```bash
curl http://localhost:8987/api/sync/stats/summary | python3 -m json.tool
```

### View Real-time Logs
```bash
docker-compose -f docker-compose.dev.yml logs -f backend | grep "issues/s"
```

### Database Metrics
```sql
-- Total issues
SELECT COUNT(*) FROM jira_issues_v2;

-- Issues by project
SELECT project_name, COUNT(*) FROM jira_issues_v2 GROUP BY project_name;

-- Recent sync performance
SELECT * FROM sync_history ORDER BY started_at DESC LIMIT 10;
```

## Troubleshooting Slow Syncs

### 1. Check Current Configuration
```bash
docker-compose logs backend | grep "Loaded performance config"
```

### 2. Monitor Rate Limiting
If you see 429 errors or "Rate limit exceeded":
- Increase `rate_limit_pause` to 0.5-1.0
- Reduce `max_workers` to 5-8
- Contact JIRA admin to check rate limits

### 3. Database Performance
Check if indexes exist:
```sql
SELECT indexname FROM pg_indexes WHERE tablename = 'jira_issues_v2';
```

### 4. Network Latency
- Check connection to JIRA instances
- Consider reducing `batch_size` if timeout errors occur
- Increase `project_timeout` for slow connections

### 5. Memory Issues
If container restarts or OOM errors:
- Reduce `max_workers`
- Reduce `batch_size`
- Increase Docker memory limits

## Best Practices

1. **Start Conservative**: Begin with safe settings and gradually optimize
2. **Monitor Logs**: Watch for rate limit warnings during optimization
3. **Test Off-Peak**: Test aggressive settings during JIRA's off-peak hours
4. **Regular Syncs**: Use shorter `lookback_days` for scheduled syncs
5. **Full Sync Weekly**: Run complete sync with longer lookback weekly
6. **Document Changes**: Keep track of what settings work for your instance

## Performance Benchmarks

| Setting Profile | Issues/Second | Full Sync Time | Risk Level |
|----------------|---------------|----------------|------------|
| Aggressive     | 800-1000      | ~60 seconds    | High       |
| Optimized      | 400-600       | ~90 seconds    | Low        |
| Balanced       | 200-400       | ~2 minutes     | Very Low   |
| Conservative   | 100-200       | ~3 minutes     | None       |

## Advanced Tuning

### Database Optimization
Ensure indexes are created:
```sql
CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_summary ON jira_issues_v2(summary);
CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_status ON jira_issues_v2(status);
CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_project_name ON jira_issues_v2(project_name);
CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_last_updated ON jira_issues_v2(last_updated);
```

### Redis Optimization
Adjust cache TTL in environment:
```bash
REDIS_TTL=120  # seconds
```

### PostgreSQL Connection Pool
In `.env`:
```bash
CONNECTION_POOL_SIZE=30
DB_MAX_CONNECTIONS=100
```

## FAQ

**Q: What's the safest way to improve performance?**
A: Increase `batch_size` first (up to 500), then reduce `lookback_days` for regular syncs.

**Q: How do I know if I'm being rate limited?**
A: Check logs for "429" errors or "Rate limit exceeded" messages.

**Q: Can I sync specific projects faster?**
A: Yes, use project-specific sync endpoints with optimized settings.

**Q: Should I increase workers on a small server?**
A: No, keep workers at 4-6 for servers with <4GB RAM.

**Q: How often should I run full syncs?**
A: Daily incremental (7-14 days lookback), weekly full sync (60+ days).