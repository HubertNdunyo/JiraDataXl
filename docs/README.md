# JIRA Sync Documentation

This documentation is optimized for AI models to understand and work with the JIRA sync system.

## Documentation Structure

### 1. [SYSTEM_REFERENCE.md](SYSTEM_REFERENCE.md)
Complete technical reference including:
- Environment configuration
- Database schema
- Field mappings between JIRA instances
- API endpoints
- Project structure
- Performance metrics
- Quick commands

### 2. [OPERATIONAL_GUIDE.md](OPERATIONAL_GUIDE.md)
Operational information including:
- Critical security fixes required
- Known issues and their solutions
- Feature implementation status
- Monitoring and maintenance procedures
- Troubleshooting guide
- Emergency procedures

### 3. [AI_AGENT_GUIDE.md](AI_AGENT_GUIDE.md)
Guide for AI agents working with the system:
- System overview and current state
- Recent major changes
- Feature implementation details
- Common questions and answers

### 4. [FEATURE_TEST_RESULTS.md](FEATURE_TEST_RESULTS.md)
Comprehensive test results (July 2025):
- Performance configuration testing
- Sync history verification
- Connection pool management
- Field discovery and caching
- Automated sync system testing
- Bug fixes verified (statistics accumulation, socket hang up)
- All API endpoints tested

### 5. [AUTOMATED_SYNC_GUIDE.md](AUTOMATED_SYNC_GUIDE.md)
Guide for the automated sync system:
- APScheduler integration details
- Configuration options (2-minute minimum)
- Thread pool implementation
- Troubleshooting automated syncs
- Recent bug fixes

## Quick Start
1. Configure environment variables (see SYSTEM_REFERENCE.md)
2. Start backend: `cd backend && ./run.sh`
3. Start frontend: `cd frontend && npm run dev`
4. Access dashboard at http://localhost:5648

## Key Information
- **Backend Port**: 8987 (localhost only)
- **Frontend Port**: 5648
- **Database**: PostgreSQL on 10.110.121.130
- **JIRA Instances**: 2 (betteredits and betteredits2)
- **Total Projects**: 101
- **Sync Performance**: 265-315 issues/second (tested)
- **Average Sync Time**: 30-35 seconds for full sync
- **Success Rate**: 100% (268 syncs in last 7 days)
- **Automated Sync**: Enabled (2-minute intervals)
- **Issues per Sync**: ~8,000-41,000 (varies by project activity)